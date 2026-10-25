# Catalog maintenance

## Daily unattended refresh

GitHub Actions runs `scripts/refresh_catalogs.py` at 18:47 UTC daily, independently of the desktop app. It refreshes Open Matte archive discovery, observed movie editions, approved series metadata and a popular-series review queue. The live service reads the public metadata every minute. Stremio can still cache a response between visits.

Each updater keeps its previous successful files if it fails, while the other updaters continue. Health and the healthy catalogs are published before the workflow reports a failed source. Check `/status.json` on the live service, `data/refresh-health.json`, or the Actions run. The live service keeps the most recent good pool in memory during upstream outages, using its bundled metadata only on a cold start without a working source. Precise `refreshedAt` versions prevent older same-day CDN responses from replacing newer bundled or fetched pools. A newer explicitly empty valid pool is respected so a policy revocation does not serve old titles forever.

Movie releases labelled Open Matte are automatically discovered and exact-matched by title, year and IMDb ID, then clearly labelled unverified. New arbitrary IMAX labels are not sufficient evidence for approval. A reviewed future home edition may have `notBefore: YYYY-MM-DD`: this gates all discovered and retained editions of that title. It becomes eligible automatically on that date, but still needs an indexed matching home release. Dates use Australia/Adelaide in the movie updater. Release dates and specifications can change; evidence review may amend or revoke the entry.

## Weekly framing review

The recurring review in the existing Codex chat supplements the daily hosted refresh. It requires the local app/computer to be available. Review new releases, the upcoming movie entries, and `data/series-candidates.json`; also seek overlooked older matches across comedy, crime, drama, mystery, animation and documentary as well as sci-fi, fantasy, action, adventure and mythology. The latter genres are preferences, not eligibility restrictions. Candidate genres and popularity do not prove aspect ratio. Use studio/distributor specifications, cinematographer interviews or firsthand home-media reviews, and record exact evidence links.

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

## Original-framing classic series (2026-10-25)

The user explicitly requested original 4:3 series that received higher-resolution home releases, and clarified that their interests extend beyond sci-fi/fantasy. Added 32 sourced classics plus ten wider-framed choices within the existing ratio range, bringing the reviewed list to 85. The latter group includes crime, drama, medical, western, historical and war stories: The Sopranos, Mad Men, Deadwood, Lost, Dexter, House, Justified, Game of Thrones, Band of Brothers and Chernobyl. These ten are not classified as 4:3 restorations. The daily popularity review queue now accepts all genres; it still does not infer framing or automatically admit candidates.

`preferredEdition` identifies the relevant Blu-ray/UHD transfer and is included in the catalog description alongside edition/season exceptions. Blu-ray packaging does not establish native HD detail: Doctor Who, Fawlty Towers, Avatar: The Last Airbender, parts of Monty Python, Batman Beyond and Samurai Jack have restoration/upscale limitations recorded. Buffy and Xena's existing original-framing approvals remain DVD-based and are not reclassified as HD remasters.

Check exact editions: Seinfeld preserves 4:3 on UHD, while its standard Blu-ray uses 16:9; Thunderbirds has both original-framing and cropped editions. Frasier changes to native 16:9 in seasons 10–11 and has a season-seven mastering exception. Columbo's 1970s seasons are 4:3, while later Return Blu-rays are reframed. Twin Peaks' 4:3 approval covers the original two seasons. Classic Doctor Who Blu-ray coverage is incomplete, with missing/reconstructed episodes. Metadata can describe these distinctions but cannot force a playback addon to select the correct transfer.

## Home rotation and alphabetical browsing

Live service (manifest 2.1.0) keeps unfiltered home requests shuffled and adds an optional `sort=A–Z` extra to both catalogs. In Stremio, use See all/Discover → Filters → sort → A–Z. Genre filtering can be combined with the selected order. All eligible titles are still returned; no twelve-item or 100-item truncation was introduced. Alphabetical ordering uses the full displayed title, case-insensitive natural number ordering, then release information and ID for stable ties.

Home and See all initially request the same catalog resource, so the addon cannot automatically infer which order the caller wants. Do not claim automatic alphabetical See all: the user selects the A–Z filter. Do not introduce a global server-side preference, referer-based guessing or per-user tracking to distinguish the views. The installed metadata addon was refreshed to expose the filter, then the custom Movies/Series row names and positions directly below Channel 4 Series were restored. Catalog-only pool updates still do not require a reinstall.


## Framing review and refresh recovery (2026-10-26)

Added reviewed native-tall approvals for The Terminator (1984), Clash of the Titans (1981) and Toy Story 5 (2026), with exact home-disc evidence in approved-editions.json. The Terminator was already an unverified Open Matte discovery; it is now eligible in its regular 1.85 home edition. Clash uses evidence for the released Warner Blu-ray, not Arrow’s upcoming November edition. The Terminator UHD enhancement/upscale is noted rather than presented as native 4K detail.

Added Reacher (2.00:1, separate seasons 1–3 disc reviews) and The Walking Dead (1.78:1, first-season and seasons 10–11 disc reviews). The latter approval does not include spin-offs or custom fan edits. Kept future-season and individual-file caveats. Added an explicit Project Hail Mary block after firsthand UHD reviews reported variable framing; no constant tall edition was established. Universal’s Odyssey announcement was rechecked: November 17 and 1.78 remain unchanged, so it stays gated.

The October 25 scheduled movie updater retained its last good pool after one exhausted metadata lookup. Added one delayed retry around an exhausted per-title lookup, plus title/year/error diagnostics if it still fails. Exact title/year/IMDb matching and whole-catalog rollback remain in place. The new regression test covers transient recovery and persistent failure. The hosted refresh must report healthy before recovery is claimed.

Reacher follow-up: season four has already aired, but no qualifying firsthand framing evidence was found in this review. Its public note explicitly limits reviewed coverage to seasons 1–3; do not extend approval from a generic IMDb ratio or uploader MediaInfo. Recheck season four when distributor specifications, a production interview or a firsthand home-edition review becomes available.

The recovery workflow succeeded with 363 movies and 87 series (including eight additional unverified Open Matte leads). Membership checks caught an incorrect editorial IMDb ID for Toy Story 5 before it appeared in the row. Corrected it to the exact Cinemeta/IMDb match tt29355505; added a regression that makes approval-ID mismatches fail visibly and retain the previous catalog rather than silently omit a reviewed title. The final refresh below supersedes these intermediate counts.

The regenerated native-home expression was submitted with Save in the existing unlocked IMAX/Open Matte profile on 2026-10-26. The editor matches the generated file and reports no expression validation errors; providers and preloading settings were not changed.

Final verification: workflow 40241010465 succeeded. The live service returned complete 364-movie and 87-series sets in both default shuffle and A–Z modes, matching repository membership with no lost titles. All four refresh tasks were healthy. Toy Story 5 (tt29355505), Clash of the Titans (1981), the upgraded Terminator approval, Reacher and The Walking Dead were present. Odyssey, Project Hail Mary and known variable-ratio exclusions stayed absent. Reacher’s season-four limitation was present in the live description. All 23 Python tests passed. Native catalog IDs, row names, placement and manifest 2.1.0 were preserved; no Site deployment or reinstall was needed.
