#!/usr/bin/env python3
"""Inspect public directory HTML for labelled editions; never fetch media files."""
import argparse
import concurrent.futures
import datetime as dt
from html.parser import HTMLParser
import json
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

from update_catalog import ROOT, ALTERED_FRAME, EXCLUDE, write_json

SOURCE = 'https://storage.open-matte.ru/'
OPEN_MATTE = re.compile(r'\bopen[ ._-]*matte\b', re.I)
FILM_SCAN = re.compile(r'\b(?:35|16|70)[ ._-]*mm\b', re.I)


class DirectoryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries, self.row, self.anchor = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = {'text': '', 'links': []}
        elif tag == 'a' and self.row is not None:
            self.anchor = {'href': dict(attrs).get('href', ''), 'name': ''}

    def handle_data(self, text):
        if self.row is not None:
            self.row['text'] += text
        if self.anchor is not None:
            self.anchor['name'] += text

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor is not None:
            self.row['links'].append(self.anchor)
            self.anchor = None
        elif tag == 'tr' and self.row is not None:
            modified = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', self.row['text'])
            for link in self.row['links']:
                if link['name'].strip():
                    self.entries.append(dict(link, modified=modified.group() if modified else ''))
            self.row = None


def safe_listing(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.netloc != 'storage.open-matte.ru'
            or parsed.query or parsed.fragment or not parsed.path.endswith('/')):
        raise ValueError('Only public directory HTML is permitted')
    return urllib.parse.urlunsplit(parsed._replace(path=urllib.parse.quote(parsed.path, safe='/%')))


def listing(url):
    url = safe_listing(url)
    request = urllib.request.Request(url, headers={
        'User-Agent': 'iPhoneDuoCatalog/2.1 (directory metadata only)', 'Accept': 'text/html'})
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.headers.get_content_type() != 'text/html':
            raise ValueError('Refusing a non-HTML response')
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError('Directory listing exceeded the metadata size limit')
    parser = DirectoryParser()
    parser.feed(body.decode('utf-8'))
    entries = []
    for entry in parser.entries:
        href = entry['href']
        if not href or href.startswith(('?', '#')) or href in ('../', '/'):
            continue
        target = urllib.parse.urljoin(url, href)
        if urllib.parse.urlsplit(target).netloc != 'storage.open-matte.ru':
            continue
        entries.append(dict(entry, url=target))
    return entries


def film_identity(label, today):
    # English title/year pairs are supplied by the archive itself. No loose
    # title matching or transliteration can silently select a different film.
    groups = re.findall(r'\(([^()]+)\)', label)
    for group in reversed(groups):
        years = list(re.finditer(r'(?<!\d)(?:19\d{2}|20\d{2})(?!\d)', group))
        if not years:
            continue
        year = int(years[-1].group())
        name = group[:years[-1].start()].strip(' ,.-')
        if name and year <= today.year:
            return {'title': name, 'year': year}
    return None


def child_directories(entries, parent):
    parent_path = urllib.parse.unquote(urllib.parse.urlsplit(parent).path)
    result = []
    for entry in entries:
        parsed = urllib.parse.urlsplit(entry['url'])
        path = urllib.parse.unquote(parsed.path)
        suffix = path[len(parent_path):] if path.startswith(parent_path) else ''
        if (not parsed.query and path.endswith('/') and suffix
                and '/' not in suffix.strip('/')):
            result.append(dict(entry, url=safe_listing(entry['url'])))
    return result


def inspect_film(entry, today, fetch=listing):
    identity = film_identity(entry['name'], today)
    if not identity:
        return None
    entries = fetch(entry['url'])
    names = [entry['name']] + [item['name'] for item in entries]
    labelled = any(OPEN_MATTE.search(name) and not ALTERED_FRAME.search(name)
                   and not EXCLUDE.search(name) for name in names)
    return {**identity, 'modified': entry['modified'], 'scannedAt': today.isoformat(),
            'openMatteLabelled': labelled, 'filmScanMentioned': any(FILM_SCAN.search(name) for name in names)}


def discover(today, previous, limit=200, fetch=listing):
    alphabet = child_directories(fetch(SOURCE), SOURCE)
    directories = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        for children in executor.map(fetch, [entry['url'] for entry in alphabet]):
            # Keep only folders with an explicit title/year identity.
            for entry in children:
                if entry['name'].endswith('/') and film_identity(entry['name'], today):
                    try:
                        directories.append(dict(entry, url=safe_listing(entry['url'])))
                    except ValueError:
                        continue
    current = {entry['url']: entry for entry in directories}
    cache = dict(previous.get('directories', {}))
    queue = []
    for url, entry in current.items():
        old = cache.get(url, {})
        stale = old.get('scannedAt', '0000-00-00') < (today-dt.timedelta(days=30)).isoformat()
        if not old or old.get('modified') != entry['modified'] or stale:
            queue.append(entry)
    # New/changed folders precede periodic rescans; successive daily runs
    # inspect the remainder without hammering an archive on every refresh.
    queue.sort(key=lambda entry: (entry['url'] in cache, cache.get(entry['url'], {}).get('scannedAt', ''), entry['url']))
    selected = queue[:limit]
    errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(inspect_film, entry, today, fetch): entry for entry in selected}
        for future in concurrent.futures.as_completed(futures):
            entry = futures[future]
            try:
                result = future.result()
                if result:
                    cache[entry['url']] = result
            except Exception:
                errors += 1
    leads = []
    for url, record in cache.items():
        if record.get('openMatteLabelled'):
            leads.append({'title': record['title'], 'year': record['year'], 'edition': 'Open Matte',
                          'observed': record['scannedAt'], 'sourceListing': url,
                          'source': 'Open Matte community archive; directory label, file framing unverified'})
    return {'updated': today.isoformat(), 'source': SOURCE,
            'policy': 'Only explicit Open Matte labels qualify. A 35mm/film-scan label alone is not approval. No media fetched.',
            'discoveredDirectories': len(current), 'inspectedDirectories': len(cache),
            'inspectedThisRun': len(selected)-errors, 'pendingInspections': max(0, len(queue)-len(selected))+errors,
            'inspectionErrors': errors, 'directories': cache, 'candidates': leads}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=200)
    args = parser.parse_args()
    target = ROOT/'data/open-matte-discoveries.json'
    previous = json.loads(target.read_text()) if target.exists() else {}
    result = discover(dt.datetime.now(ZoneInfo('Australia/Adelaide')).date(), previous, args.limit)
    write_json(target, result)
    print(json.dumps({key: value for key, value in result.items() if key not in ('directories', 'candidates')}, ensure_ascii=False))
