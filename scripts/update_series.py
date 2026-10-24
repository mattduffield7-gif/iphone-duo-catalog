#!/usr/bin/env python3
"""Refresh metadata for a reviewed list of tall-format series, without account data."""
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
import re
import urllib.parse
from zoneinfo import ZoneInfo
from update_catalog import fetch_json, normalize, write_json

ROOT = Path(__file__).resolve().parents[1]

def resolve(entry):
    url = 'https://v3-cinemeta.strem.io/catalog/series/top/search=' + urllib.parse.quote(entry['title'],safe='') + '.json'
    metas = fetch_json(url).get('metas',[])
    matches = [m for m in metas if m.get('type') == 'series' and re.fullmatch(r'tt\d{7,10}',m.get('id',''))
               and normalize(m.get('name','')) == normalize(entry['title'])
               and str(m.get('releaseInfo',m.get('year','')))[:4] == str(entry['year'])]
    if len(matches)!=1:
        raise ValueError('Series metadata did not match uniquely: '+entry['title'])
    m=matches[0]
    return dict(id=m['id'],type='series',name=m['name'],poster=m.get('poster',f"https://images.metahub.space/poster/medium/{m['id']}/img"),posterShape='poster',releaseInfo=str(m.get('releaseInfo',entry['year'])),genres=entry['genres'],aspectRatio=entry['aspectRatio'],evidenceSources=entry['sources'],description=f"Reported standard framing: {entry['aspectRatio']}:1. {entry.get('note','Special episodes, seasons and individual stream files can differ.')} Select your usual series stream provider; this catalog does not enforce playback resolution.")

def main():
    entries=json.loads((ROOT/'data/series-editions.json').read_text())['series']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        movies=list(ex.map(resolve,entries))
    write_json(ROOT/'data/series-pool.json',{'updated':dt.datetime.now(ZoneInfo('Australia/Adelaide')).date().isoformat(),'series':movies,'limitations':'Reported home framing, not file-level verification. No viewing history, account identifiers or debrid keys are stored.'})
    write_json(ROOT/'catalog/series/iphone-duo-series.json',{'metas':movies,'cacheMaxAge':300})
    print(f'Built full series catalog with {len(movies)} titles')

if __name__=='__main__':main()
