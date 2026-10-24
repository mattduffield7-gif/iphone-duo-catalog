# Good for the iPhone Duo

A metadata-only Stremio row for full-film expanded IMAX, Open Matte and native tall presentations, rotating daily in Australia/Adelaide time.

## Selection policy

Only titles and editions in `data/approved-editions.json` are eligible. Sixteen reviewed films are currently listed, including native tall presentations from 1.33:1 to 1.90:1. Each entry records source evidence and the intended aspect ratio. IMAX filmed-camera credits alone are insufficient: the home edition must preserve expansion across the film. Variable-ratio editions such as Interstellar, Oppenheimer and The Marvels are excluded. Fantastic Four: First Steps is held in `pendingReview` because its home presentation has framing changes; an entire-film IMAX marketing credit is insufficient. Unknown IMAX tags are excluded until reviewed. `includeReleaseLabelledOpenMatte` defaults to false: enabling it admits exact-matched Open Matte-labelled discovery leads with an explicit unverified-framing description, while known variable-ratio titles remain blocked. This setting requires a deliberate preference change; it does not assert that uploader labels prove whole-film expansion. The word HYBRID is not treated as proof of changing aspect ratio: it can refer to combined audio, HDR or video sources.

This is a conservative starting list, not a complete directory. Primary IMAX/Disney sources support the IMAX entries; the Blade Runner 2049 Open Matte entry uses community restoration documentation, recorded separately in its evidence. Individual stream files have not been played or independently verified. Select the matching edition in the stream results; an ordinary widescreen release of an eligible movie does not qualify.

The daily update searches Knaben's public movie index, paginates results and includes zero-seed records because debrid services may retain cached copies. It intersects results with the reviewed list by default, and requires exact normalized title, year and IMDb matches from Cinemeta. Most editions require IMAX/Open Matte labels. Five explicitly reviewed films preserve expansion in their regular 2D home releases: Avatar, Avatar: The Way of Water, Avatar: Fire and Ash, Aquaman and the Lost Kingdom, and The Suicide Squad. Those entries permit Blu-ray/WEB sources without edition labels. Native tall entries also permit normal 2D home sources: Zack Snyder's Justice League (4:3), The Avengers (1.78/1.85 depending on release), Pacific Rim (1.85) and the original Jurassic Park trilogy (1.85). These are selected for their framing, rather than classified as IMAX productions. Explicit cropped, custom-frame, VAR/UAR and 3D labels are excluded. `includeOlderTitles` controls whether older reviewed titles are eligible; otherwise the current and previous three years are used. Up to 12 posters are shown, with daily order rotation even when fewer titles qualify. Daily refresh finds newly indexed releases of approved titles; it cannot safely approve every new movie automatically. New title/edition pairs require evidence review and an allowlist update.

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

`stream-expression.txt` is generated from the same reviewed list and discovery preference for the AIOStreams Required Stream Expression field. Apply it when the approved list changes; the catalog schedule does not update the private AIOStreams profile automatically.
