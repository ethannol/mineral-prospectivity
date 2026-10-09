# Decision log

Append-only. One entry per scoping, data, or analytical decision, with the date,
the evidence (which script or profile), and the alternatives rejected. Entries
after the freeze are marked POST-FREEZE and are exploratory.

## 2026-10-09 Verified download URLs and recorded provenance before downloading

- Evidence: HEAD requests to both URLs returned HTTP 200 with content-length
  39,431,276 (NURE, last-modified 2014-12-01) and 25,791,223 (MRDS, last-modified
  2022-08-23). Full responses, headers and SHA-256 are in `data/raw/manifest.json`
  and `data/archive/*/*.headers`. First inspection of both archives was done with
  `python -I` scripts kept outside the archive directories.
- Rejected: the metadata URL `https://mrdata.usgs.gov/metadata/nuresed.txt` from the
  brief returned 404; the archive's own `nurehssr.met` is used and committed instead.

## 2026-10-09 Archives live in data/archive/, not data/raw/

- Evidence: `cairn freeze` hashes every file under `data/raw/**` into
  `.cairn/frozen.json`, and `cairn verify` fails with "frozen file missing" when a
  hashed file is absent. The 65 MB of archives must stay out of git, so a fresh
  checkout would fail verification if they were under `data/raw/`.
- Decision: archives go in `data/archive/` (gitignored); the committed extract,
  metadata files and manifest go in `data/raw/` and are frozen. This deviates from
  the brief's "data/raw/ location excluded from git" wording to keep `cairn verify`
  passing from a fresh checkout. This is the first thing in cairn that blocked.
- Rejected: naming archives with a leading dot (cairn skips dot-files) as too obscure.

## 2026-10-09 cairn.toml: report rendered to reports/report.md

- Evidence: the brief asks for `reports/report.md`; the template renders to
  `report.md` at the root. Changed `report = "reports/report.md"` once, at setup,
  before the freeze. No other harness configuration was changed. `report.tmpl.md`
  stays at the root as the template expects.

## 2026-10-09 Region and commodity: Nevada, gold

- Evidence: exploration of the whole-country archives (scratch scripts, outputs
  summarised here; reproduced by `scripts/10_prepare.py` for the Nevada extract).
  Nevada: 27,630 NURE sediment rows in all 18 of its 1x2 degree quadrangles, from two
  DOE labs (SRL-W 18,735; LLL 8,895), 17,518 stream-sediment samples; MRDS gold
  Producer/Past Producer sites: 2,850 with gold as a primary commodity, 4,349 with
  gold at any rank. Arizona: four labs (SRL-W, LLL, LASL, ORGDP) with inconsistent
  element suites, and 10,499 soil versus 10,297 stream samples; copper producers 3,360.
  Both candidates meet the site-count criterion; Nevada meets the single-method-family
  criterion better (three method families, but a shared ten-element suite, see below)
  and has a cleaner stream-sediment population.
- Quadrangles (stream samples by method family, LL/OR/SR): Caliente (0/930/0),
  Elko (0/0/419), Ely (0/1524/18), Goldfield (0/469/0), Kingman (497/0/0),
  Las Vegas (1537/0/0), Lovelock (910/0/0), Lund (0/1590/26), Mariposa (0/44/0),
  McDermitt (0/0/1062), Millett (1402/0/0), Reno (14/0/698), Tonopah (1600/0/0),
  Vya (0/376/989), Walker Lake (172/0/486), Wells (0/0/1139), Winnemucca (1096/0/0).
- Rejected: Arizona/copper (lab heterogeneity, soils); a sub-region of Nevada
  (would lose the batch-effect comparison).

## 2026-10-09 Analytical method family, not DOE lab, is the batch variable

- Evidence: the `methods` field. SRL-W samples were analysed either by Savannah
  River neutron activation (SR1/SR2/SR3) or by Oak Ridge methods (OR1/OR2/OR7),
  with different element suites; 1,494 LLL-collected samples were analysed by SR
  methods. Family = first method code prefix: LL, SR, OR; NONE = no analyses.
- Decision: `method_family` (LL, SR, OR) is the laboratory-group covariate for the
  leave-one-group-out check and the lab-trap exploratory model. Records with
  NONE (520 stream records, no element data) are excluded with a logged reason.

## 2026-10-09 Element suite: Al, Fe, Mn, Na, Sc, Th, V, Ce, La, Ti

- Evidence: per-family non-null and censored fractions among Nevada stream-sediment
  records (reproduced in `artifacts/tables/element_availability.csv` by
  `scripts/10_prepare.py`). Rule, fixed before the freeze: keep an element if it is
  non-null in at least 75% of records and censored in at most 25% of its non-null
  records in every one of the three families. Ten elements pass. Ti is the most
  censored (21% in LL, detection limit 200 ppm).
- Rejected: uranium (the OR family reports it by two methods, delayed neutron for
  two thirds and fluorometry for one third); Hf (95% censored in OR); As, Sb, W,
  Hg, Zn, Ag (absent or heavily censored in at least one family). The consequence,
  stated up front: the suite is lithological (major and trace rock-forming
  elements and LREE), not a gold-pathfinder suite. Classic Nevada gold pathfinders
  (As, Sb, Hg, Tl, W) are not measured consistently across the families.

## 2026-10-09 Unit of analysis: 5 km grid cell on UTM zone 11N

- Evidence: 17,518 stream samples, 395 + 92 distinct samples share exact coordinates,
  and replicate records exist; a cell removes within-site pseudo-replication and
  gives one row per unit for the spatial blocks. UTM 11N (EPSG:32611) covers Nevada
  (scale distortion below 0.1% at the eastern edge). Both datasets are projected as
  WGS84; the NAD27 to WGS84 shift in Nevada is on the order of 100 m, two orders of
  magnitude below the cell size, so no datum transformation is applied.
- Rejected: individual samples (pseudo-replication, duplicate coordinates); 2 km
  cells (most cells would hold one sample); catchment polygons (not available
  offline).

## 2026-10-09 Multiple records per sample

- Evidence: LLL replicate pairs (replc 100 then 101/110) contain the full suite in
  both records with median |log ratio| 0.04 to 0.12 for Al, Sc, Fe; SRL-W pairs
  (rec_cnt 1 and 2) are an SR analysis and an OR analysis of the same sample
  (median |log ratio| 0.16 to 0.26), with the extended OR suite on one record only.
- Decision: one record per (doelab, prime_id): the record with the lowest rec_no
  (the primary record). Counts of collapsed records are logged. Within-cell
  averaging then removes any remaining site-level repetition.
- Rejected: averaging the two records (mixes method families); keeping both (two
  rows per sample inflate within-cell n).

## 2026-10-09 Labels: positive, ambiguous, negative cells

- Decision: a cell is positive if it contains at least one MRDS site with
  `dev_stat` in {Producer, Past Producer} and the whole word "Gold" in `commod1`
  (primary commodity list). A cell with no positive site but at least one MRDS site
  that mentions gold in commod1, commod2 or commod3 at any development status
  (prospects, occurrences, unknown, plants, and producers with gold only as a
  by-product) is ambiguous and is excluded from the confirmatory population. All
  other sampled cells are negatives, which are unlabelled, not known-barren.
- The deposit-to-cell join is a cell-level aggregation (count of positive sites per
  cell) merged 1:1 onto the cell table with `cairn.checked_merge`; duplicate MRDS
  records in one cell cannot create two positives.
- Rejected: positives at any commodity rank (by-product gold at a copper or silver
  mine is a different exploration target); a distance buffer around sites (a cell
  edge is already up to 3.5 km from a site; a buffer would blur the unit and
  multiply cells per site).
