# Catalog maintenance

## Daily unattended refresh

GitHub Actions runs `scripts/refresh_catalogs.py` at 18:47 UTC daily, independently of the desktop app. It refreshes Open Matte archive discovery, observed movie editions, approved series metadata and a popular-series review queue. The live service reads the public metadata every minute. Stremio can still cache a response between visits.

Each updater keeps its previous successful files if it fails, while the other updaters continue. Health and the healthy catalogs are published before the workflow reports a failed source. Check `/status.json` on the live service, `data/refresh-health.json`, or the Actions run. The live service keeps the most recent good pool in memory during upstream outages, using its bundled metadata only on a cold start without a working source. Precise `refreshedAt` versions prevent older same-day CDN responses from replacing newer bundled or fetched pools. A newer explicitly empty valid pool is respected so a policy revocation does not serve old titles forever.

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


## Broader archive discovery and film scans (2026-10-25)

`discover_open_matte.py` inspects only HTML directory listings at storage.open-matte.ru. It never requests video files. It inventories the alphabetical folders and checks up to 200 new, changed or stale film folders per daily run, retaining an inspection journal in `data/open-matte-discoveries.json`. Unchanged folders are periodically reconsidered after 30 days. The initial audit inspected all 1,498 title/year folders and found 311 explicit Open Matte-labelled candidates; inspection counts, pending work and errors are recorded separately so an incomplete scan cannot be presented as complete coverage. The community archive is an independent discovery task: if it fails, its last good metadata is retained and movie/series updates still run.

Only an explicit Open Matte label in a directory or listed filename becomes an unverified discovery lead. Plain 35mm, 16mm, 70mm, fullscreen, archive membership or an IMDb aspect-ratio field is insufficient. Matching still requires the exact Cinemeta title, release year and valid IMDb identity. Known framing blocks and future-release gates apply to archive leads as well as index results. Titles known only under alternate/non-English names can remain unmatched; do not loosen matching to hide that gap.

Reviewed, already-released native/expanded home editions no longer depend on Knaben returning a filename to appear in the metadata pool. This corrects omissions such as the Back to the Future trilogy. Firsthand home-media review evidence is recorded in the approval file. Additions include Back to the Future I–III, Aliens, Predator, Batman (1989), Batman Returns, Gremlins, The Princess Bride, Men in Black, E.T., The 7th Voyage of Sinbad and Wrath of the Titans. The new rule has 35mm filename exceptions only for the explicitly reviewed Back to the Future trilogy; this is not a global admission rule for film scans. All files remain individually unverified.

The initial expanded pool contains 352 movies: 30 reviewed title/edition entries and 322 release-labelled discovery entries. The 43-title series pool is unchanged. All four refresh tasks succeeded.

The expanded rule also recognises spaced, joined, dotted, hyphenated and underscored Open Matte labels. It was applied and saved in the accessible IMAX/Open Matte AIO profile. Public catalog refresh still cannot update that private rule automatically.

Playback coverage remains separate from metadata discovery. The current seven providers have not been established as direct storage.open-matte.ru or HDrezka scrapers. HDrezka integrations found in Nuvio-related projects use direct HTTP; the public ElfHosted AIOStreams instance explicitly excludes HTTP/P2P/live streams. The main tapframe/NuvioStreamsAddon repository is archived. Do not claim an untested fork is a reliable TorBox integration, or publish source video URLs in the metadata repository. Archive observations can guide searches through existing providers without adding direct HTTP playback.

Movie-year matching was enabled for movie requests only, with a one-year tolerance and strict/missing-year rejection disabled, after a provider returned Back to the Future Part III for the first film. The returned filenames still require inspection; cached responses and provider parsing can delay or limit this check. Do not report that particular mismatch fixed until the live result confirms it.
