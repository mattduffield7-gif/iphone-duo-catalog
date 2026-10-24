import datetime as dt
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("catalog", Path(__file__).parents[1] / "scripts/update_catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def test_edition_and_recent_year_required(self):
        today = dt.date(2026, 10, 25)
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2025.1080p.WEB-DL"}, today))
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2025.NON.IMAX.1080p"}, today))
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2025.IMAX.HDCAM"}, today))
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2022.Open.Matte"}, today))
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2027.IMAX"}, today))
        movie = catalog.parse_release({"title": "Some.Movie.2025.Open.Matte.1080p.WEB-DL"}, today)
        self.assertEqual((movie["title"], movie["year"], movie["edition"]), ("Some Movie", 2025, "Open Matte"))

    def test_title_number_is_not_release_year(self):
        movie = catalog.parse_release({"title": "Blade Runner 2049 (2017) Open Matte"}, dt.date(2018, 1, 1))
        self.assertEqual(movie["year"], 2017)
        self.assertEqual(movie["title"], "Blade Runner 2049")

    def test_rotation_stable_and_complete(self):
        movies = [{"id": f"tt{i:07}"} for i in range(23)]
        start = dt.date(2026, 10, 25)
        first = catalog.rotate(movies, start)
        self.assertEqual(first, catalog.rotate(list(reversed(movies)), start))
        self.assertNotEqual(first, catalog.rotate(movies, start + dt.timedelta(days=1)))
        seen = {m["id"] for day in range(23) for m in catalog.rotate(movies, start + dt.timedelta(days=day))}
        self.assertEqual(len(seen), 23)
        self.assertEqual(len({m["id"] for m in first}), 12)

    def test_metadata_must_match_title_year_and_release_date(self):
        candidate = {"title": "Some Movie", "year": 2026, "edition": "IMAX", "observed": "2026-10-24"}
        movie = {"id": "tt1234567", "type": "movie", "name": "Some Movie", "releaseInfo": "2026", "released": "2026-10-24"}
        today = dt.date(2026, 10, 25)
        with patch.object(catalog, "fetch_json", return_value={"metas": [movie]}):
            self.assertEqual(catalog.resolve_movie(candidate, today)["id"], "tt1234567")
        for changes in [{"name": "Some Other Movie"}, {"releaseInfo": "2025"}, {"released": "2026-11-01"}, {"type": "series"}]:
            with patch.object(catalog, "fetch_json", return_value={"metas": [dict(movie, **changes)]}):
                self.assertIsNone(catalog.resolve_movie(candidate, today))
        with patch.object(catalog, "fetch_json", return_value={"metas": [movie, dict(movie, id="tt7654321")]}):
            self.assertIsNone(catalog.resolve_movie(candidate, today))


if __name__ == "__main__":
    unittest.main()
