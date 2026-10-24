#!/usr/bin/env python3
"""Build a rotating row of reviewed tall films and optional Open Matte leads."""
import argparse
import concurrent.futures
import datetime as dt
import html
import json
from pathlib import Path
import random
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
EDITION = re.compile(r"\bIMAX\b|\bopen[ ._-]?matte\b", re.I)
EXCLUDE = re.compile(r"\b(?:non[ ._-]?imax|cam|hdcam|hdts|telesync|trailer|sample)\b", re.I)
HOME_SOURCE = re.compile(r"\b(?:web[ ._-]?(?:dl|rip)|blu[ ._-]?ray|bd(?:rip|remux))\b", re.I)
ALTERED_FRAME = re.compile(r"\b(?:cropped|crop|custom[ ._-]?open[ ._-]?matte|variable[ ._-]?aspect|VAR|UAR|3D)\b", re.I)


def fetch_json(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "iPhoneDuoCatalog/1.0 (metadata-only daily catalog)", "Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def normalize(title):
    value = unicodedata.normalize("NFKD", html.unescape(title)).casefold()
    value = re.sub(r"\bimax\b", "", value)
    value = re.sub(r"^star wars\s*[:\-]?\s*", "", value)
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def parse_release(release, today, allow_unlabelled=False):
    title = html.unescape(release.get("title", ""))
    if (not EDITION.search(title) and not allow_unlabelled) or EXCLUDE.search(title) or ALTERED_FRAME.search(title):
        return None
    years = [m for m in re.finditer(r"(?<!\d)(?:19\d{2}|20\d{2})(?!\d)", title) if 1900 <= int(m.group()) <= today.year]
    if not years:
        return None
    parenthesized = [m for m in years if m.start() and title[m.start() - 1] in "(["]
    match = (parenthesized or years)[0]
    year = int(match.group())
    name = title[:match.start()].strip(" ._-([{")
    if " / " in name:
        name = name.split(" / ")[-1]
    name = re.sub(r"[._]+", " ", name).strip()
    # Edition tags can precede the year (e.g. 'Collateral Open Matte 2004').
    name = EDITION.sub("", name).strip(" ._-[]()")
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s+(?:theatrical(?: (?:cut|version))?|extended(?: (?:cut|edition|version))?|director['’]?s cut|special edition|unrated|remastered)$", "", name, flags=re.I).strip()
    if not name:
        return None
    edition = "Open Matte" if re.search(r"open[ ._-]?matte", title, re.I) else "IMAX" if re.search(r"\bIMAX\b", title, re.I) else "Standard Home"
    return {"title": name, "year": year, "edition": edition, "homeSource": bool(HOME_SOURCE.search(title)), "observed": release.get("date", "")}


def resolve_movie(candidate, today):
    query = urllib.parse.quote(candidate["title"], safe="")
    data = fetch_json(f"https://v3-cinemeta.strem.io/catalog/movie/top/search={query}.json")
    matches = []
    for movie in data.get("metas", []):
        if not re.fullmatch(r"tt\d{7,10}", movie.get("id", "")) or movie.get("type") != "movie":
            continue
        year_match = re.search(r"\d{4}", str(movie.get("releaseInfo", movie.get("year", ""))))
        if not year_match or int(year_match.group()) != candidate["year"]:
            continue
        if normalize(movie.get("name", "")) != normalize(candidate["title"]):
            continue
        released = movie.get("released")
        if released and str(released)[:10] > today.isoformat():
            continue
        matches.append(movie)
    if len(matches) != 1:
        return None
    movie = matches[0]
    return {"id": movie["id"], "type": "movie", "name": movie["name"], "poster": movie.get("poster", f"https://images.metahub.space/poster/medium/{movie['id']}/img"), "releaseInfo": str(candidate["year"]), "posterShape": "poster", "description": f"A publicly indexed release is labelled {candidate['edition']}. Choose AIOStreams in the source selector for IMAX/Open Matte results.", "edition": candidate["edition"], "observed": candidate["observed"]}


def rotate(movies, day, size=12):
    pool = sorted(movies, key=lambda m: m["id"])
    random.Random("iphone-duo-catalog-v1").shuffle(pool)
    if not pool:
        return []
    count = min(size, len(pool))
    offset = (day - dt.date(2026, 1, 1)).days * max(1, count - 1) % len(pool)
    return (pool + pool)[offset:offset + count]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def retain_previous(movies, previous_pool, policy, today):
    """An index disappearing is not evidence that an observed edition never existed."""
    kept = dict(movies)
    approved_ids = {m['id'] for m in policy['movies']}
    blocked = {(normalize(m['title']), m['year']) for m in policy.get('excludedMovies', [])}
    held = {(normalize(m['title']), m['year']) for m in policy['movies']
            if m.get('notBefore', today.isoformat()) > today.isoformat()}
    for movie in previous_pool:
        match = re.match(r'\d{4}', str(movie.get('releaseInfo', '')))
        if not match or not re.fullmatch(r'tt\d{7,10}', movie.get('id', '')):
            continue
        year = int(match.group())
        if ((normalize(movie.get('name', '')), year) in blocked | held
                or (not policy['includeOlderTitles'] and year < today.year - 3)):
            continue
        reviewed = movie['id'] in approved_ids
        labelled = (policy.get('includeReleaseLabelledOpenMatte')
                    and movie.get('reviewStatus', '').startswith('Release-labelled')
                    and movie.get('edition') == 'Open Matte')
        if reviewed or labelled:
            kept.setdefault(movie['id'], movie)
    return kept


def build(today, fixture_dir=None, policy=None, previous_pool=()):
    if policy is None:
        policy = json.loads((ROOT / "data" / "approved-editions.json").read_text())
    approved = {(normalize(m["title"]), m["year"], m["edition"]): m for m in policy["movies"]
                if (policy["includeOlderTitles"] or m["year"] >= today.year - 3)
                and m.get('notBefore', today.isoformat()) <= today.isoformat()}
    blocked = {(normalize(m["title"]), m["year"]) for m in policy.get("excludedMovies", [])}
    blocked |= {(normalize(m['title']), m['year']) for m in policy['movies']
                if m.get('notBefore', today.isoformat()) > today.isoformat()}
    candidates = {}
    queries = list(dict.fromkeys(["IMAX", "Open Matte", "OpenMatte"] +
                   [f"{m['title']} {m['year']}" if m.get("allowStandardHome") else f"{m['title']} {m['edition']}" for m in approved.values()]))
    for query in queries:
        if fixture_dir and query in ("IMAX", "Open Matte"):
            name = "imax" if query == "IMAX" else "open-matte"
            payload = json.loads((fixture_dir / f"{name}-releases.json").read_text())
        else:
            # Zero-seed metadata is still useful: a debrid service can retain a
            # cached copy. Paginate broad searches rather than dropping old films.
            hits = []
            for page in range(10):
                params = urllib.parse.urlencode({"q": query, "c": "3000000", "o": "date", "d": "desc", "s": 300, "f": page * 300})
                batch = fetch_json(f"https://api.knaben.org/v2/search?{params}&dead")
                if not isinstance(batch.get("hits"), list):
                    raise ValueError("Invalid release source response; retaining the previous catalog")
                hits.extend(batch["hits"])
                if len(batch["hits"]) < 300:
                    break
            payload = {"hits": hits}
        if not isinstance(payload.get("hits"), list):
            raise ValueError("Invalid release source response; retaining the previous catalog")
        for release in payload["hits"]:
            movie = parse_release(release, today, allow_unlabelled=True)
            if movie:
                key = (normalize(movie["title"]), movie["year"], movie["edition"])
                if key[:2] in blocked:
                    continue
                if key in approved:
                    movie["approval"] = approved[key]
                    candidates[key] = movie
                else:
                    # A few reviewed films preserve expansion in their regular home
                    # releases; those files need not carry an IMAX/Open Matte tag.
                    matched = False
                    for approved_key, approval in approved.items():
                        if (approval.get("allowStandardHome") and movie["homeSource"]
                                and approved_key[:2] == key[:2]):
                            movie["edition"] = approval["edition"]
                            movie["approval"] = approval
                            candidates[approved_key] = movie
                            matched = True
                            break
                    if (not matched and policy.get("includeReleaseLabelledOpenMatte")
                            and movie["edition"] == "Open Matte"
                            and (policy["includeOlderTitles"] or movie["year"] >= today.year - 3)):
                        candidates[key] = movie
    movies = {}
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(resolve_movie, m, today): m for m in candidates.values()}
        for future in concurrent.futures.as_completed(futures):
            try:
                movie = future.result()
                approval = futures[future].get("approval")
                if movie and (not approval or movie["id"] == approval["id"]):
                    if not approval:
                        movie["reviewStatus"] = "Release-labelled; framing unverified"
                        movie["description"] = ("Publicly indexed Open Matte-labelled release. Whole-film framing has not been independently confirmed. "
                                                "Select an Open Matte result under IMAX/Open Matte; ordinary widescreen releases do not qualify.")
                        # A reviewed entry always takes precedence over a lead.
                        if movie["id"] not in movies:
                            movies[movie["id"]] = movie
                        continue
                    movie["aspectRatio"] = approval["aspectRatio"]
                    movie["evidenceSources"] = approval["sources"]
                    movie["reviewStatus"] = "Reviewed title/edition; file unverified"
                    movie["description"] = (f"Reviewed full-film tall/expanded {movie['edition']} presentation ({approval['aspectRatio']}). "
                                            + ("The regular 2D Blu-ray/WEB home presentation qualifies; an IMAX filename tag is not required. " if approval.get("allowStandardHome") else "Choose the matching edition in your stream addon. ")
                                            + "Individual files have not been played or verified.")
                    if movie["id"] in movies:
                        old = movies[movie["id"]]
                        movie["edition"] = ", ".join(sorted(set(old["edition"].split(", ") + movie["edition"].split(", "))))
                    movies[movie["id"]] = movie
            except Exception as error:
                failures.append(str(error))
    if failures:
        raise RuntimeError(f"{len(failures)} metadata lookups failed; retaining the previous catalog")
    # Unknown IMAX tags never qualify: most IMAX movies switch aspect ratios.
    pool = list(retain_previous(movies, previous_pool, policy, today).values())
    public_movies = [{k: v for k, v in m.items() if k not in ("edition", "observed", "aspectRatio", "evidenceSources")} for m in rotate(pool, today, size=len(pool))]
    return pool, {"metas": public_movies, "cacheMaxAge": 300, "staleRevalidate": 0}



def stream_expression(policy):
    def quoted(value):
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
    open_matte = "merge(editions(streams, 'Open Matte'), keyword(streams, 'filename,folderName', 'open matte', 'openmatte'))"
    expression = "[]"
    for movie in reversed(policy["movies"]):
        condition = f"(title == {quoted(movie['title'])} and year == {movie['year']})"
        if movie.get("allowStandardHome"):
            selection = "quality(streams, 'Bluray REMUX', 'Bluray', 'WEB-DL', 'WEBRip')"
        elif movie["edition"] == "Open Matte":
            selection = open_matte
        else:
            selection = "merge(visualTag(streams, 'IMAX'), editions(streams, 'IMAX', 'IMAX Enhanced'))"
        expression = f"{condition} ? {selection} : ({expression})"
    if policy.get("includeReleaseLabelledOpenMatte"):
        # The discovery tier also applies to reviewed movies: e.g. an Endgame
        # Open Matte file must not require a separate IMAX filename tag.
        expression = f"merge(({expression}), {open_matte})"
    for movie in policy.get("excludedMovies", []):
        condition = f"(title == {quoted(movie['title'])} and year == {movie['year']})"
        expression = f"{condition} ? [] : ({expression})"
    rejected = "keyword(streams, 'filename,folderName', 'cropped', 'custom open matte', 'variable aspect', 'VAR', 'UAR')"
    return ("/* Reviewed tall films and optional release-labelled Open Matte */ (queryType == 'movie' or queryType == 'anime.movie') ? "
            + f"negate({rejected}, ({expression})) : streams")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=dt.date.fromisoformat)
    parser.add_argument("--fixture-dir", type=Path)
    args = parser.parse_args()
    today = args.date or dt.datetime.now(ZoneInfo("Australia/Adelaide")).date()
    policy = json.loads((ROOT / "data" / "approved-editions.json").read_text())
    previous_path = ROOT / 'data' / 'pool.json'
    previous = json.loads(previous_path.read_text()).get('movies', []) if previous_path.exists() else []
    pool, catalog = build(today, args.fixture_dir, previous_pool=previous)
    (ROOT / "stream-expression.txt").write_text(stream_expression(policy) + "\n")
    write_json(ROOT / "data" / "pool.json", {"updated": today.isoformat(), "movies": pool})
    write_json(ROOT / "catalog" / "movie" / "iphone-duo.json", catalog)
    write_json(ROOT / "status.json", {"updated": today.isoformat(), "timezone": "Australia/Adelaide", "poolSize": len(pool), "reviewedCount": sum(m.get("reviewStatus", "").startswith("Reviewed") for m in pool), "releaseLabelledCount": sum(m.get("reviewStatus", "").startswith("Release-labelled") for m in pool), "rowSize": len(catalog["metas"]), "minimumMovieYear": None if policy["includeOlderTitles"] else today.year - 3, "source": "Reviewed native tall/expanded presentations and optional Open Matte release metadata, with exact Cinemeta title/year/IMDb matches", "rotation": "Daily order of the complete pool; the live service shuffles each fetch", "limitations": "Release-labelled Open Matte entries are discovery leads, not independently confirmed whole-film framing. Known variable-ratio titles and explicitly altered framing are excluded. Individual files are not played, downloaded or checked for TorBox availability."})
    print(f"Built full catalog with {len(catalog['metas'])} movies for {today}")


if __name__ == "__main__":
    main()
