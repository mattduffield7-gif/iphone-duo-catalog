import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]/'scripts'))
import update_catalog as movies
import discover_series
import refresh_catalogs


class UpdateTests(unittest.TestCase):
    def test_approval_id_mismatch_fails_refresh_instead_of_silently_omitting_title(self):
        entry = {'id': 'tt1000001', 'title': 'Some Movie', 'year': 2026,
                 'edition': 'Native Tall', 'aspectRatio': '1.85:1', 'allowStandardHome': True,
                 'sources': ['https://example.com/review']}
        policy = {'includeOlderTitles': True, 'movies': [entry]}
        meta = {'id': 'tt1000002', 'name': entry['title'], 'type': 'movie', 'releaseInfo': '2026'}
        with patch.object(movies, 'fetch_json', side_effect=lambda u: {'hits': []} if 'knaben' in u else {'metas': [meta]}):
            with self.assertRaisesRegex(RuntimeError, 'approved IMDb ID tt1000001 does not match metadata ID tt1000002'):
                movies.build(dt.date(2026, 10, 26), policy=policy)

    def test_exhausted_metadata_lookup_gets_one_delayed_retry_without_relaxing_matching(self):
        candidate = {'title': 'Some Movie', 'year': 2026}
        today = dt.date(2026, 10, 26)
        with patch.object(movies, 'resolve_movie', side_effect=[TimeoutError('temporary'), None]) as resolve, patch.object(movies.time, 'sleep') as sleep:
            self.assertIsNone(movies.resolve_movie_with_retry(candidate, today))
            self.assertEqual(resolve.call_count, 2)
            sleep.assert_called_once_with(5)
        with patch.object(movies, 'resolve_movie', side_effect=TimeoutError('persistent')), patch.object(movies.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, r'Some Movie \(2026\): TimeoutError: persistent'):
                movies.resolve_movie_with_retry(candidate, today)

    def test_announced_home_release_is_gated_even_for_open_matte_and_retained_entries(self):
        entry = {'id': 'tt33764258', 'title': 'The Odyssey', 'year': 2026,
                 'edition': 'Expanded Home', 'aspectRatio': '1.78:1', 'allowStandardHome': True,
                 'notBefore': '2026-11-17', 'sources': ['https://www.universalpicturesathome.com/']}
        policy = {'includeOlderTitles': True, 'includeReleaseLabelledOpenMatte': True, 'movies': [entry]}
        meta = {'id': entry['id'], 'name': entry['title'], 'type': 'movie', 'releaseInfo': '2026'}
        previous = [dict(meta, edition='Open Matte', reviewStatus='Release-labelled; framing unverified')]
        hits = {'hits': [{'title': 'The.Odyssey.2026.1080p.WEB-DL'}, {'title': 'The.Odyssey.2026.Open.Matte.WEB-DL'}]}
        with patch.object(movies, 'fetch_json', side_effect=lambda u: hits if 'knaben' in u else {'metas': [meta]}):
            early, _ = movies.build(dt.date(2026, 11, 16), policy=policy, previous_pool=previous)
            released, _ = movies.build(dt.date(2026, 11, 17), policy=policy)
        self.assertEqual(early, [])
        self.assertEqual([m['id'] for m in released], ['tt33764258'])
        self.assertTrue(released[0]['reviewStatus'].startswith('Reviewed'))

    def test_review_leads_do_not_admit_future_approved_or_excluded_series(self):
        base = {'type': 'series', 'releaseInfo': '2026', 'genres': ['Fantasy']}
        entries = [dict(base, id='tt1000001', name='New Show'),
                   dict(base, id='tt1000002', name='Known Show'),
                   dict(base, id='tt1000003', name='Wide Show'),
                   dict(base, id='tt1000004', name='Future Show', released='2026-12-01'),
                   dict(base, id='tt1000005', name='Crime Show', genres=['Crime']),
                   dict(base, id='tt1000006', name='Comedy Show', genres=['Comedy'])]
        policy = {'series': [{'title': 'Known Show', 'year': 2026}], 'excludedSeries': [{'id': 'tt1000003'}]}
        leads = discover_series.discover(entries, policy, dt.date(2026, 10, 25))
        self.assertEqual([m['id'] for m in leads], ['tt1000001', 'tt1000005', 'tt1000006'])
        self.assertTrue(all('aspectRatio' not in lead for lead in leads))

    def test_one_failed_updater_rolls_back_its_partial_writes_and_other_catalog_still_updates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'data').mkdir()
            (root/'data/approved-editions.json').write_text('{"movies": []}')
            (root/'data/pool.json').write_text('{"updated":"2026-10-24","movies":[]}')
            before = (root/'data/pool.json').read_bytes()
            (root/'status.json').write_text('{"updated":"2026-10-24","poolSize":89}')
            attempted = []
            def run(command, **kwargs):
                script = Path(command[1]).name
                attempted.append(script)
                if script == 'update_catalog.py':
                    (root/'data/pool.json').write_text('partial/broken')
                    raise subprocess.CalledProcessError(1, command)
                if script == 'update_series.py':
                    (root/'data/series-pool.json').write_text('{"updated":"2026-10-25","series":[{}]}')
                return subprocess.CompletedProcess(command, 0)
            health = refresh_catalogs.refresh(root, run)
            self.assertEqual((root/'data/pool.json').read_bytes(), before)
            self.assertEqual(len(attempted), 4)
            self.assertEqual(health['movies']['state'], 'failed')
            self.assertEqual(health['series']['state'], 'ok')
            status = json.loads((root/'status.json').read_text())
            self.assertEqual(status['poolSize'], 89)
            self.assertEqual(status['series']['poolSize'], 1)

    def test_briefly_popular_candidates_survive_until_review_but_approvals_and_rejections_remove_them(self):
        previous = [{'id': 'tt1000001', 'name': 'New Show', 'releaseInfo': '2026', 'genres': ['Fantasy'],
                     'firstSeen': '2026-10-20', 'lastSeen': '2026-10-24'}]
        policy = {'series': []}
        self.assertEqual(len(discover_series.discover([], policy, dt.date(2026, 10, 25), previous)), 1)
        policy['series'] = [{'title': 'New Show', 'year': 2026}]
        self.assertEqual(discover_series.discover([], policy, dt.date(2026, 10, 25), previous), [])
        policy = {'series': [], 'excludedSeries': [{'id': 'tt1000001'}]}
        self.assertEqual(discover_series.discover([], policy, dt.date(2026, 10, 25), previous), [])


if __name__ == '__main__':
    unittest.main()
