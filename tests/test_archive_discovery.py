import datetime as dt
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]/'scripts'))
import discover_open_matte as archive
import update_catalog as catalog

TODAY = dt.date(2026, 10, 25)


class ArchiveDiscoveryTests(unittest.TestCase):
    def test_only_directory_html_can_be_requested(self):
        for url in ['https://storage.open-matte.ru/movie.mkv', 'https://example.com/A/',
                    'http://storage.open-matte.ru/A/', 'https://storage.open-matte.ru/A/?download=1']:
            with self.assertRaises(ValueError):
                archive.safe_listing(url)
        self.assertEqual(archive.safe_listing('https://storage.open-matte.ru/A/'), 'https://storage.open-matte.ru/A/')

    def test_35mm_alone_is_not_open_matte_and_media_is_never_fetched(self):
        folder = {'name': 'Назад (Back to the Future, 1985)/', 'url': 'https://storage.open-matte.ru/A/BTTF/', 'modified': '2026-10-25 00:00'}
        requests = []
        def fetch(url):
            requests.append(url)
            return [{'name': 'Back.to.the.Future.1985.35mm.mkv', 'url': url+'movie.mkv'}]
        result = archive.inspect_film(folder, TODAY, fetch)
        self.assertFalse(result['openMatteLabelled'])
        self.assertTrue(result['filmScanMentioned'])
        self.assertEqual(requests, [folder['url']])
        result = archive.inspect_film(folder, TODAY, lambda u: [{'name': 'BTTF.35mm.Open.Matte.mkv'}])
        self.assertTrue(result['openMatteLabelled'])
        result = archive.inspect_film(folder, TODAY, lambda u: [{'name': 'BTTF.CROPPED.Open.Matte.mkv'}])
        self.assertFalse(result['openMatteLabelled'])

    def test_number_in_title_and_release_year_remain_distinct(self):
        self.assertEqual(archive.film_identity('Бегущий (Blade Runner 2049, 2017)/', TODAY),
                         {'title': 'Blade Runner 2049', 'year': 2017})
        self.assertIsNone(archive.film_identity('Будущее (Future Movie, 2027)/', TODAY))

    def test_incremental_budget_continues_without_rescanning_unchanged_folders(self):
        root = archive.SOURCE
        alphabet = root+'A/'
        folders = [{'name': f'Русский (Movie {i}, 2020)/', 'url': alphabet+str(i)+'/', 'modified': '2026-10-24 00:00'} for i in range(2)]
        requests = []
        def fetch(url):
            requests.append(url)
            if url == root:
                return [{'name': 'A/', 'url': alphabet, 'modified': ''}]
            if url == alphabet:
                return folders
            return [{'name': 'Movie.Open.Matte.mkv'}]
        first = archive.discover(TODAY, {}, limit=1, fetch=fetch)
        self.assertEqual(first['pendingInspections'], 1)
        self.assertEqual(len(first['candidates']), 1)
        requests.clear()
        second = archive.discover(TODAY, first, limit=1, fetch=fetch)
        self.assertEqual(second['pendingInspections'], 0)
        self.assertEqual(len(second['candidates']), 2)
        self.assertNotIn(folders[0]['url'], requests)

    def test_archive_leads_still_obey_framing_blocks_future_gate_and_exact_metadata(self):
        policy = {'includeOlderTitles': True, 'includeReleaseLabelledOpenMatte': True,
                  'movies': [], 'excludedMovies': [{'title': 'Interstellar', 'year': 2014}]}
        base = {'edition': 'Open Matte', 'observed': '2026-10-25', 'sourceListing': archive.SOURCE+'A/Film/'}
        leads = [dict(base, title='Some Movie', year=2020), dict(base, title='Interstellar', year=2014),
                 dict(base, title='Future Movie', year=2027), dict(base, title='Other Movie', year=2020, sourceListing='https://example.com/A/')]
        meta = {'id': 'tt1234567', 'type': 'movie', 'name': 'Some Movie', 'releaseInfo': '2020'}
        with patch.object(catalog, 'fetch_json', side_effect=lambda u: {'hits': []} if 'knaben' in u else {'metas': [meta]}):
            pool, public = catalog.build(TODAY, policy=policy, community_candidates=leads)
        self.assertEqual([movie['id'] for movie in pool], ['tt1234567'])
        self.assertTrue(pool[0]['reviewStatus'].startswith('Release-labelled'))
        self.assertIn('community archive', public['metas'][0]['description'])

    def test_reviewed_home_titles_do_not_need_a_single_index_to_return_a_file(self):
        policy = {'includeOlderTitles': True, 'movies': [{'id': 'tt0088763', 'title': 'Back to the Future', 'year': 1985,
                  'edition': 'Native Tall', 'aspectRatio': '1.85:1', 'sources': ['https://thedigitalbits.com/'],
                  'allowStandardHome': True, 'allowFilmScan': True}]}
        meta = {'id': 'tt0088763', 'name': 'Back to the Future', 'type': 'movie', 'releaseInfo': '1985'}
        with patch.object(catalog, 'fetch_json', side_effect=lambda u: {'hits': []} if 'knaben' in u else {'metas': [meta]}):
            pool, _ = catalog.build(TODAY, policy=policy)
        self.assertEqual([movie['id'] for movie in pool], ['tt0088763'])
        expression = catalog.stream_expression(policy)
        self.assertIn("'35mm'", expression)
        self.assertIn("title == 'Back to the Future'", expression)


if __name__ == '__main__':
    unittest.main()
