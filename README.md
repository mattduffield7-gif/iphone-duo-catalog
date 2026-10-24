# Good for the iPhone Duo

A metadata-only Stremio row combining reviewed tall/expanded presentations with Open Matte-labelled discovery leads, rotating daily in Australia/Adelaide time.

## Selection policy

The row combines reviewed titles in `data/approved-editions.json` with publicly indexed Open Matte-labelled discovery leads. Sixteen reviewed films are currently listed, including native tall presentations from 1.33:1 to 1.90:1. Each reviewed entry records source evidence and the intended aspect ratio. Unreviewed release-labelled entries explicitly say their framing is unverified. IMAX filmed-camera credits alone are insufficient: the home edition must preserve expansion across the film. Variable-ratio editions such as Interstellar, Oppenheimer and The Marvels are excluded. Fantastic Four: First Steps is held in `pendingReview` because its home presentation has framing changes; an entire-film IMAX marketing credit is insufficient. Unknown IMAX tags are excluded until reviewed. `includeReleaseLabelledOpenMatte` is enabled with the user’s approval: exact-matched Open Matte-labelled discovery leads are admitted with an explicit unverified-framing description, while known variable-ratio titles remain blocked. Uploader labels do not prove whole-film expansion. The word HYBRID is not treated as proof of changing aspect ratio: it can refer to combined audio, HDR or video sources.

This is a conservative starting list, not a complete directory. Primary IMAX/Disney sources support the IMAX entries; the Blade Runner 2049 Open Matte entry uses community restoration documentation, recorded separately in its evidence. Individual stream files have not been played or independently verified. Select the matching edition in the stream results. Ordinary widescreen releases do not qualify unless the title is explicitly approved for its normal tall home presentation.

The daily update searches Knaben's public movie index, paginates results and includes zero-seed records because debrid services may retain cached copies. It combines reviewed tall-format editions with release-labelled Open Matte leads, and requires exact normalized title, year and IMDb matches from Cinemeta. Most editions require IMAX/Open Matte labels. Five explicitly reviewed films preserve expansion in their regular 2D home releases: Avatar, Avatar: The Way of Water, Avatar: Fire and Ash, Aquaman and the Lost Kingdom, and The Suicide Squad. Those entries permit Blu-ray/WEB sources without edition labels. Native tall entries also permit normal 2D home sources: Zack Snyder's Justice League (4:3), The Avengers (1.78/1.85 depending on release), Pacific Rim (1.85) and the original Jurassic Park trilogy (1.85). These are selected for their framing, rather than classified as IMAX productions. Explicit cropped, custom-frame, VAR/UAR and 3D labels are excluded. `includeOlderTitles` controls whether older reviewed titles are eligible; otherwise the current and previous three years are used. The full eligible movie pool is returned, so Discover and Show more can reach every title. The live service shuffles the complete pool on each fetch; Stremio may cache the result between visits. Daily refresh can discover new Open Matte-labelled titles automatically; these remain explicitly unverified. Independently reviewed IMAX/native tall additions still require evidence review and an approval-list update.

No credentials, media files, torrent hashes, magnets or playback links are stored here. Existing addons provide movie details and playback. This catalog does not check debrid availability.

## Endpoints

- `manifest.json` — installation URL
- `catalog/movie/iphone-duo.json` — full movie catalog, with daily order rotation
- `catalog/series/iphone-duo-series.json` — full sourced series catalog
- `status.json` — last refresh, pool size and limitations

The static fallback uses a five-minute catalog cache; older installed versions may retain a previous response for longer. Refresh Stremio if necessary. Rotation changes posters/order and never starts playback. GitHub Actions runs at 05:17 Adelaide during daylight saving and 04:17 during standard time; scheduled jobs can be delayed. A failed source request keeps the previous published selection and fails the workflow. A successful strict scan can publish an empty row rather than admit disallowed movies.

## Development

Python 3.12+, no external dependencies.

```sh
python -m unittest discover -s tests -v
python scripts/update_catalog.py
```

GitHub Pages publishes only manifest, status and catalog endpoints.

`stream-expression.txt` is generated from the same reviewed list and discovery preference for the AIOStreams Required Stream Expression field. Apply it when the approved list changes; the catalog schedule does not update the private AIOStreams profile automatically.

## Live service

The replacement metadata-only endpoint is https://iphone-duo-catalog.ivory-carp-4098.chatgpt.site/manifest.json. It serves both full catalogs and freshly shuffles their order on each HTTP fetch. It publishes no playback links, credentials, watched-title identifiers or account history. A broad genre mix guides series ordering; it is not a live history-sync or automatic watched-title exclusion service.

Series in `data/series-editions.json` have sourced reported home framing between 1.33:1 and 2.00:1, with episode/season exceptions possible. Daily metadata refreshes do not automatically approve arbitrary new series.
