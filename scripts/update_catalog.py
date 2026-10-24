#!/usr/bin/env python3
"""Build a metadata-only Stremio row from publicly indexed edition labels."""
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


def parse_release(release, today):
    title = html.unescape(release.get("title", ""))
    if not EDITION.search(title) or EXCLUDE.search(title):
        return None
    years = [m for m in re.finditer(r"(?<!\d)(?:19\d{2}|20\d{2})(?!\d)", title) if 1900 <= int(m.group()) <= today.year]
    if not years:
        return None
    parenthesized = [m for m in years if m.start() and title[m.start() - 1] in "(["]
    match = (parenthesized or years)[0]
    year = int(match.group())
    if year < today.year - 3:
        return None
    name = title[:match.start()].strip(" ._-([{")
    if " / " in name:
        name = name.split(" / ")[-1]
    name = re.sub(r"[._]+", " ", name).strip()
    if not name:
        return None
    return {"title": name, "year": year, "edition": "Open Matte" if re.search(r"open[ ._-]?matte", title, re.I) else "IMAX", "observed": release.get("date", "")}


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
    offset = (day - dt.date(2026, 1, 1)).days * count % len(pool)
    return (pool + pool)[offset:offset + count]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def build(today, fixture_dir=None):
    candidates = {}
    for query in ["IMAX", "Open Matte", "OpenMatte"]:
        if fixture_dir and query in ("IMAX", "Open Matte"):
            name = "imax" if query == "IMAX" else "open-matte"
            payload = json.loads((fixture_dir / f"{name}-releases.json").read_text())
        else:
            params = urllib.parse.urlencode({"q": query, "c": "3000000", "o": "date", "d": "desc", "s": 300})
            payload = fetch_json(f"https://api.knaben.org/v2/search?{params}")
        if not isinstance(payload.get("hits"), list):
            raise ValueError("Invalid release source response; retaining the previous catalog")
        for release in payload["hits"]:
            movie = parse_release(release, today)
            if movie:
                candidates[(normalize(movie["title"]), movie["year"], movie["edition"])] = movie
    movies = {}
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(resolve_movie, m, today): m for m in candidates.values()}
        for future in concurrent.futures.as_completed(futures):
            try:
                movie = future.result()
                if movie:
                    if movie["id"] in movies:
                        old = movies[movie["id"]]
                        movie["edition"] = ", ".join(sorted(set(old["edition"].split(", ") + movie["edition"].split(", "))))
                    movies[movie["id"]] = movie
            except Exception as error:
                failures.append(str(error))
    if failures:
        raise RuntimeError(f"{len(failures)} metadata lookups failed; retaining the previous catalog")
    if len(movies) < 8:
        raise ValueError(f"Only {len(movies)} verified metadata matches; retaining the previous catalog")
    pool = list(movies.values())
    public_movies = [{k: v for k, v in m.items() if k not in ("edition", "observed")} for m in rotate(pool, today)]
    return pool, {"metas": public_movies, "cacheMaxAge": 3600, "staleRevalidate": 3600}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=dt.date.fromisoformat)
    parser.add_argument("--fixture-dir", type=Path)
    args = parser.parse_args()
    today = args.date or dt.datetime.now(ZoneInfo("Australia/Adelaide")).date()
    pool, catalog = build(today, args.fixture_dir)
    write_json(ROOT / "data" / "pool.json", {"updated": today.isoformat(), "movies": pool})
    write_json(ROOT / "catalog" / "movie" / "iphone-duo.json", catalog)
    write_json(ROOT / "status.json", {"updated": today.isoformat(), "timezone": "Australia/Adelaide", "poolSize": len(pool), "rowSize": len(catalog["metas"]), "minimumMovieYear": today.year - 3, "source": "Knaben public edition-labelled release metadata; exact Cinemeta title/year matches", "rotation": "Daily, 12 movies per selection", "limitations": "Release labels are community metadata, not independent aspect-ratio or playback verification."})
    print(f"Built {len(catalog['metas'])} daily picks from {len(pool)} movies for {today}")


if __name__ == "__main__":
    main()
