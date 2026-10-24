# Catalog maintenance

## Daily unattended refresh

GitHub Actions runs `scripts/refresh_catalogs.py` at 18:47 UTC daily, independently of the desktop app. It refreshes observed movie editions, approved series metadata and a popular-series review queue. The live service reads the public metadata every minute. Stremio can still cache a response between visits.

Each updater keeps its previous successful files if it fails, while the other updaters continue. Health and the healthy catalogs are published before the workflow reports a failed source. Check `/status.json` on the live service, `data/refresh-health.json`, or the Actions run. The live service keeps the most recent good pool in memory during upstream outages, using its bundled metadata only on a cold start without a working source. An explicitly empty valid pool is respected so a policy revocation does not serve old titles forever.

Movie releases labelled Open Matte are automatically discovered and exact-matched by title, year and IMDb ID, then clearly labelled unverified. New arbitrary IMAX labels are not sufficient evidence for approval. A reviewed future home edition may have `notBefore: YYYY-MM-DD`: this gates all discovered and retained editions of that title. It becomes eligible automatically on that date, but still needs an indexed matching home release. Dates use Australia/Adelaide in the movie updater. Release dates and specifications can change; evidence review may amend or revoke the entry.

## Weekly framing review

The recurring review in the existing Codex chat supplements the daily hosted refresh. It requires the local app/computer to be available. Review new releases, the upcoming movie entries, and `data/series-candidates.json`; also seek overlooked older matches in sci-fi, fantasy, action, adventure and mythology. Candidate genres and popularity do not prove aspect ratio. Use studio/distributor specifications, cinematographer interviews or firsthand home-media reviews, and record exact evidence links.

Movies must have a constant tall/expanded home presentation, or be an explicitly unverified uploader-labelled Open Matte discovery. Keep known variable-ratio titles excluded. For series, inspect later seasons and known special episodes, not just a season-one specification; retain explicit framing/transfer notes. Keep The Expanse as a taste reference, excluded from the row because of wider/variable later-season framing. Do not add a clearly conflicting series without user direction.

Add verified movies to `data/approved-editions.json` and verified shows to `data/series-editions.json`. Update known rejected series under `excludedSeries` with reasons and sources. Re-run tests and metadata refresh, inspect the actual diff and health, commit and push to the existing metadata repository, trigger the refresh workflow, and verify live counts/membership. Ordinary pool changes do not need a Sites deployment or Stremio reinstall. Preserve the catalog IDs, native row names, position and complete-set responses.

`stream-expression.txt` controls the separate private AIOStreams IMAX/Open Matte profile. New native tall/standard home approvals can require applying its regenerated contents there. Public metadata refresh does not automatically edit that private profile. The public ElfHosted instance currently permits syncing only whitelisted expression URLs, and this repository is not on its whitelist. Apply only when the already-authorized profile is accessible and unlocked; otherwise report that specific playback-filter step. Existing Torrentio can remain an alternative provider. Never publish account history, private addon URLs or debrid credentials. Do not start playback, preloads, downloads or new service integrations for catalog maintenance.

## Current review

On 2026-10-25, The Odyssey was registered as an upcoming reviewed 1.78:1 home edition, gated until Universal's announced 2026-11-17 release. Spider-Man (2002) was approved for its native 1.85 home framing, and Vikings was added after a complete-series 1.78 review. Spider-Man's wider sequels and American Gods' known wide framing segments were not blanket-approved from related titles or generic series tags.

Watch the GitHub Actions schedule: GitHub can delay scheduled runs. A healthy daily metadata timestamp does not mean a new movie/series has passed editorial framing review or that a playable TorBox result exists.

The regenerated Spider-Man and Odyssey stream expression was applied and saved in the existing unlocked IMAX/Open Matte profile on 2026-10-25. No reinstall was requested by the configuration UI.
