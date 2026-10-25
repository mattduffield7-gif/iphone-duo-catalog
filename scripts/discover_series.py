#!/usr/bin/env python3
"""Collect popular review leads across genres; never infer their aspect ratios."""
import datetime as dt
import json
import re
from zoneinfo import ZoneInfo
from update_catalog import ROOT, fetch_json, normalize, write_json

def discover(metas, policy, today, previous=()):
    approved = {(normalize(m['title']), m['year']) for m in policy['series']}
    excluded = {m['id'] for m in policy.get('excludedSeries', [])}
    leads = {}
    for m in previous:
        year = re.match(r'\d{4}', str(m.get('releaseInfo', '')))
        try:
            age = (today - dt.date.fromisoformat(m.get('lastSeen', ''))).days
        except ValueError:
            continue
        if (year and 0 <= age <= 90 and m.get('id') not in excluded
                and (normalize(m.get('name', '')), int(year[0])) not in approved):
            leads[m['id']] = m
    for m in metas:
        year = re.match(r'\d{4}', str(m.get('releaseInfo', m.get('year', ''))))
        if (m.get('type') != 'series' or not re.fullmatch(r'tt\d{7,10}', m.get('id', ''))
                or not year or int(year[0]) > today.year or m['id'] in excluded
                or (normalize(m.get('name', '')), int(year[0])) in approved
                or str(m.get('released') or '')[:10] > today.isoformat()):
            continue
        lead = {k: m[k] for k in ('id', 'name', 'releaseInfo', 'genres') if k in m}
        lead.update(firstSeen=leads.get(m['id'], {}).get('firstSeen', today.isoformat()), lastSeen=today.isoformat())
        leads[m['id']] = lead
    return list(leads.values())


def main():
    today = dt.datetime.now(ZoneInfo('Australia/Adelaide')).date()
    url = 'https://v3-cinemeta.strem.io/catalog/series/top.json'
    response = fetch_json(url)
    if not isinstance(response.get('metas'), list) or not response['metas']:
        raise ValueError('Popular-series metadata unavailable; retain previous review leads')
    policy = json.loads((ROOT/'data/series-editions.json').read_text())
    path = ROOT/'data/series-candidates.json'
    previous = json.loads(path.read_text()).get('candidates', []) if path.exists() else []
    leads = discover(response['metas'], policy, today, previous)
    write_json(path, {'updated': today.isoformat(), 'source': url,
        'policy': 'Popular-series leads across all genres. Check sourced home framing before adding to the catalog.',
        'candidates': leads})
    print(f'Collected {len(leads)} series for framing review; none automatically admitted')


if __name__ == '__main__':
    main()
