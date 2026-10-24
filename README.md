# Good for the iPhone Duo

A metadata-only Stremio row for full-film expanded IMAX and Open Matte editions, rotating daily in Australia/Adelaide time.

## Strict edition policy

Only titles and editions in `data/approved-editions.json` are eligible. Each entry records source evidence and the intended aspect ratio. IMAX filmed-camera credits alone are insufficient: the home edition must preserve expansion across the film. Variable-ratio editions such as Interstellar, Oppenheimer and The Marvels are excluded. Unknown IMAX/Open Matte labels are excluded until reviewed. The word HYBRID is not treated as proof of changing aspect ratio: it can refer to combined audio, HDR or video sources.

This is a conservative starting list, not a complete directory. Primary IMAX/Disney sources support the IMAX entries; the Blade Runner 2049 Open Matte entry uses community restoration documentation, recorded separately in its evidence. Individual stream files have not been played or independently verified. Select the matching edition in the stream results; an ordinary widescreen release of an eligible movie does not qualify.

The daily update searches Knaben's public movie index for edition-labelled releases, intersects them with the reviewed list, and requires exact normalized title, year and IMDb matches from Cinemeta. `includeOlderTitles` controls whether older reviewed titles are eligible; otherwise the current and previous three years are used. Up to 12 posters are shown, with daily order rotation even when fewer titles qualify. Daily refresh finds newly indexed releases of approved titles; it cannot safely approve every new movie automatically. New title/edition pairs require evidence review and an allowlist update.

No credentials, media files, torrent hashes, magnets or playback links are stored here. Existing addons provide movie details and playback. This catalog does not check debrid availability.

## Endpoints

- `manifest.json` — installation URL
- `catalog/movie/iphone-duo.json` — daily selection
- `status.json` — last refresh, pool size and limitations

The one-hour client cache may delay a new selection. Refresh Stremio if necessary. Rotation changes posters/order and never starts playback. GitHub Actions runs at 05:17 Adelaide during daylight saving and 04:17 during standard time; scheduled jobs can be delayed. A failed source request keeps the previous published selection and fails the workflow. A successful strict scan can publish an empty row rather than admit disallowed movies.

## Development

Python 3.12+, no external dependencies.

```sh
python -m unittest discover -s tests -v
python scripts/update_catalog.py
```

GitHub Pages publishes only manifest, status and catalog endpoints.
