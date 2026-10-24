#!/usr/bin/env python3
"""Refresh independently; keep each catalog's last good files after a failure."""
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo
from update_catalog import ROOT, write_json

TASKS = [
    ('movies', 'update_catalog.py', ['data/pool.json', 'catalog/movie/iphone-duo.json', 'status.json', 'stream-expression.txt']),
    ('series', 'update_series.py', ['data/series-pool.json', 'catalog/series/iphone-duo-series.json']),
    ('seriesDiscovery', 'discover_series.py', ['data/series-candidates.json']),
]


def run_task(root, name, script, outputs, previous, timestamp, run=subprocess.run):
    snapshot = {name: (root/name).read_bytes() if (root/name).exists() else None for name in outputs}
    try:
        run([sys.executable, str(root/'scripts'/script)], check=True, timeout=1200, cwd=root)
        return {'state': 'ok', 'lastAttemptAt': timestamp,
                'lastSuccessAt': dt.datetime.now(dt.timezone.utc).isoformat()}
    except (subprocess.SubprocessError, OSError) as error:
        for path, value in snapshot.items():
            target = root/path
            if value is None:
                target.unlink(missing_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(value)
        print(f'{name}: {type(error).__name__}; retained previous files', file=sys.stderr)
        return {'state': 'failed', 'lastAttemptAt': timestamp,
                'lastSuccessAt': previous.get('lastSuccessAt'),
                'message': 'Refresh failed; previous successful metadata retained. See the GitHub Actions run.'}


def refresh(root=ROOT, run=subprocess.run):
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    health_path = root/'data/refresh-health.json'
    previous = json.loads(health_path.read_text()) if health_path.exists() else {}
    results = {name: run_task(root, name, script, outputs, previous.get(name, {}), timestamp, run)
               for name, script, outputs in TASKS}
    policy = json.loads((root/'data/approved-editions.json').read_text())
    today = dt.datetime.now(ZoneInfo('Australia/Adelaide')).date().isoformat()
    health = {'checkedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'schedule': 'Daily at 18:47 UTC (05:17 Adelaide daylight time; 04:17 standard time)',
              **results, 'upcoming': [{k: m[k] for k in ('id', 'title', 'notBefore', 'aspectRatio', 'sources')}
                  for m in policy['movies'] if m.get('notBefore', '') > today]}
    write_json(health_path, health)
    status_path = root/'status.json'
    status = json.loads(status_path.read_text()) if status_path.exists() else {}
    status['refresh'] = health
    series_path = root/'data/series-pool.json'
    if series_path.exists():
        series = json.loads(series_path.read_text())
        status['series'] = {'updated': series.get('updated'), 'poolSize': len(series.get('series', []))}
    write_json(status_path, status)
    return health


if __name__ == '__main__':
    refresh()
