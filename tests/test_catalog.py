import datetime as dt
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("catalog", Path(__file__).parents[1] / "scripts/update_catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def test_edition_and_valid_year_required(self):
        today = dt.date(2026, 10, 25)
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2025.1080p.WEB-DL"}, today))
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2025.NON.IMAX.1080p"}, today))
        self.assertIsNone(catalog.parse_release({"title": "Some.Movie.2025.IMAX.HDCAM"}, today))
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

    def test_small_pool_rotates_order(self):
        movies = [{"id": f"tt{i:07}"} for i in range(6)]
        day = dt.date(2026, 10, 25)
        self.assertNotEqual(catalog.rotate(movies, day), catalog.rotate(movies, day + dt.timedelta(days=1)))
        self.assertEqual(len(catalog.rotate(movies, day)), 6)

    def test_unknown_and_variable_ratio_titles_never_enter_pool(self):
        payload = {"hits": [
            {"title": "Avengers.Infinity.War.2018.IMAX.HYBRID.1080p"},
            {"title": "The.Fantastic.Four.First.Steps.2025.IMAX.1080p"},
            {"title": "Oppenheimer.2023.IMAX.2160p"},
            {"title": "Unknown.Movie.2025.Open.Matte.1080p"},
        ]}
        movie = {"id": "tt4154756", "name": "Avengers: Infinity War", "type": "movie", "releaseInfo": "2018"}
        def fetch(url):
            return payload if "api.knaben.org" in url else {"metas": [movie]}
        with patch.object(catalog, "fetch_json", side_effect=fetch):
            pool, public = catalog.build(dt.date(2026, 10, 25))
        self.assertEqual([m["id"] for m in pool], ["tt4154756"])
        self.assertEqual(len(public["metas"]), 1)
        self.assertIn("Reviewed full-film", public["metas"][0]["description"])

    def test_open_matte_tag_before_year_is_not_part_of_movie_title(self):
        movie = catalog.parse_release({"title": "Collateral Open Matte 2004 ITA ENG 1080p"}, dt.date(2026, 10, 25))
        self.assertEqual(movie["title"], "Collateral")

    def test_broader_discovery_retains_labels_and_blocks_known_variable_titles(self):
        policy = {"includeOlderTitles": True, "includeReleaseLabelledOpenMatte": True, "movies": [],
                  "excludedMovies": [{"title": "Interstellar", "year": 2014}]}
        payload = {"hits": [{"title": "Some.Movie.2025.Open.Matte.WEB-DL"},
                            {"title": "Interstellar.2014.Open.Matte.WEB-DL"},
                            {"title": "Unknown.IMAX.Movie.2025.IMAX.WEB-DL"},
                            {"title": "Ordinary.Movie.2025.WEB-DL"}]}
        movie = {"id": "tt1234567", "name": "Some Movie", "type": "movie", "releaseInfo": "2025"}
        def fetch(url):
            return payload if "api.knaben.org" in url else {"metas": [movie]}
        with patch.object(catalog, "fetch_json", side_effect=fetch):
            pool, public = catalog.build(dt.date(2026, 10, 25), policy=policy)
        self.assertEqual([m["id"] for m in pool], ["tt1234567"])
        self.assertEqual(pool[0]["reviewStatus"], "Release-labelled; framing unverified")
        self.assertIn("not been independently confirmed", public["metas"][0]["description"])
        expression = catalog.stream_expression(policy)
        self.assertIn("title == 'Interstellar'", expression)
        self.assertIn("? [] :", expression)
        self.assertIn("editions(streams, 'Open Matte')", expression)

    def test_native_tall_snyder_cut_needs_no_edition_tag(self):
        policy = {"includeOlderTitles": True, "movies": [{"id": "tt12361974", "title": "Zack Snyder's Justice League", "year": 2021,
                  "edition": "Native Tall", "allowStandardHome": True, "aspectRatio": "1.33:1", "sources": ["https://www.motionpictures.org/"]}]}
        payload = {"hits": [{"title": "Zack.Snyders.Justice.League.2021.2160p.BluRay"}]}
        movie = {"id": "tt12361974", "name": "Zack Snyder's Justice League", "type": "movie", "releaseInfo": "2021"}
        with patch.object(catalog, "fetch_json", side_effect=lambda url: payload if "api.knaben.org" in url else {"metas": [movie]}):
            pool, public = catalog.build(dt.date(2026, 10, 25), policy=policy)
        self.assertEqual([m["id"] for m in pool], ["tt12361974"])
        self.assertIn("Native Tall", public["metas"][0]["description"])

    def test_reviewed_standard_home_edition_needs_no_imax_label(self):
        payload = {"hits": [
            {"title": "Avatar.2009.2160p.BluRay.x265"},
            {"title": "Unknown.Movie.2025.1080p.WEB-DL"},
            {"title": "Avatar.2009.CROPPED.1080p.WEB-DL"},
            {"title": "Avatar.2009.3D.BluRay"},
        ]}
        movie = {"id": "tt0499549", "name": "Avatar", "type": "movie", "releaseInfo": "2009"}
        def fetch(url):
            return payload if "api.knaben.org" in url else {"metas": [movie]}
        with patch.object(catalog, "fetch_json", side_effect=fetch):
            pool, public = catalog.build(dt.date(2026, 10, 25))
        self.assertEqual([m["id"] for m in pool], ["tt0499549"])
        self.assertIn("IMAX filename tag is not required", public["metas"][0]["description"])
        for title in ["Avatar.2009.CROPPED.WEB-DL", "Avatar.2009.3D.BluRay", "Avatar.2009.VAR.WEB-DL"]:
            self.assertIsNone(catalog.parse_release({"title": title}, dt.date(2026, 10, 25), allow_unlabelled=True))

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
