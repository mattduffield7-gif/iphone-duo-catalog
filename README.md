# Good for the iPhone Duo

A metadata-only Stremio home-screen row with 12 daily rotating movie picks.

The daily update searches Knaben's public movie index for releases labelled IMAX or Open Matte, keeps movies from the current year and previous three years, and requires an exact normalized title and release-year match from Cinemeta. It excludes obvious cam, trailer, sample, and non-IMAX labels. Movie IDs are ordinary IMDb IDs, so existing metadata and stream addons continue to handle movie details and playback.

No account credentials, media files, torrent hashes, magnets, or playback links are stored here. Community release labels are evidence of an indexed release, not independent verification of aspect ratio, quality, language, or current playability. The catalog cannot guarantee every IMAX or Open Matte movie is indexed.

The selection rotates daily according to the Australia/Adelaide date, and source data refreshes through GitHub Actions. The workflow publishes only the manifest, catalog, and status endpoints to GitHub Pages. A source outage or failed metadata lookup leaves the previous published selection in place and marks the workflow failed. GitHub's scheduled jobs can run later than their nominal time.

## Endpoints

- `manifest.json` — install this URL in Stremio
- `catalog/movie/iphone-duo.json` — today's movie picks
- `status.json` — last update date, source, pool size, and rotation information

The catalog uses a one-hour client cache. Restart or refresh Stremio if a saved row has not updated yet. It rotates the poster selection; it does not automatically start videos.

## Development

Requires Python 3.12 or newer, with no third-party dependencies.

```sh
python -m unittest discover -s tests -v
python scripts/update_catalog.py
```

The schedule refreshes at 05:17 Adelaide during daylight saving and 04:17 during standard time. Run the workflow manually to refresh sooner. Playback is provided by the user's separately configured streaming addons; this repository supplies a catalog only.
