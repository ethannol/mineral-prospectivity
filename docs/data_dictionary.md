# Data dictionary

Both sources are USGS public-domain products on mrdata.usgs.gov. The whole-country
archives are not committed (`data/archive/`, gitignored); the deterministic Nevada
extract, the source metadata files and `data/raw/manifest.json` (URLs, HTTP response
headers, SHA-256 of each archive, row counts, extract SHA-256) are committed and
never modified. Rebuild check: `python -m prospectivity.extract --check`.

## nure_nv_sediment.csv (NURE HSSR sediment database, Nevada rows)

- Source: https://mrdata.usgs.gov/nure/sediment/nuresed-csv.zip, retrieved 2026-10-09
  (archive last-modified 2014-12-01 per HTTP headers; SHA-256 in manifest). Public domain.
  Field descriptions: `data/raw/nurehssr.met` (the archive's FGDC metadata; the
  `https://mrdata.usgs.gov/metadata/nuresed.txt` URL in the brief returned 404 on
  2026-10-09) and https://mrdata.usgs.gov/nure/sediment/about.php.
- Extract filter: `state == "NV"` and `smpmedia == "SEDIMENT"` (27,630 of 397,609 rows).
  Rows are copied as text, no type inference.
- One row represents: one analytical record for one sediment sample. A sample can have
  more than one record: `rec_cnt` = 2 marks an additional record on the same sample
  (SRL-W: a second analysis by a different method family), and `replc` codes other
  than 000 mark replicate analyses (LLL: 100 = primary, 101/110/111 = replicates).
- Key: `rec_no` (unique). Sample key: (`doelab`, `prime_id`); 2,459 rows share a sample
  key with another row.
- Fields used downstream (all 145 fields are kept in the extract; see the .met file):
  - `latitude`, `longitude`: decimal degrees, NAD27 (Clarke 1866). Missing or known-bad
    coordinates were set to null by USGS (see `coordprb`). 40 rows have null latitude.
  - `doelab`: DOE laboratory responsible for collection and analysis. Nevada: `SRL-W`
    (Savannah River, western program) and `LLL` (Lawrence Livermore).
  - `methods`: analytical method codes (comma-separated). Nevada families: `LL1-DN`,
    `LL1-NA` (Livermore delayed-neutron U and neutron activation); `SR1`, `SR2`,
    `SR3-...` (Savannah River neutron activation and extras); `OR1`, `OR2`, `OR7`
    (Oak Ridge Gaseous Diffusion Plant methods applied to SRL-W samples); `NONE`
    (no analyses in the record).
  - `quad`: USGS 1 degree by 2 degree quadrangle name. `sampsrc`: STREAM, SOIL, PLAYA,
    LAKE, OTHER. `sizefrxn`: sieve fraction analysed (-100 MESH, -18/+35 MESH, -18/+100 MESH).
  - `sampdat`: YYYY/MM/DD. LLL 1975-1978, SRL-W 1979-1980.
  - Element fields `xx_ppm` (parts per million) and `xx_pct` (percent):
    `al_pct, fe_pct, mn_ppm, na_pct, sc_ppm, th_ppm, v_ppm, ce_ppm, la_ppm, ti_ppm`
    are used as features; others are profiled for the censoring figure only.
  - `u_dn_ppm`, `u_fl_ppm`, `u_na_ppm`: uranium by delayed neutron, fluorometry,
    neutron activation (method-specific; not used as features).
- Null means: not analysed or not recorded (the metadata says no field is fully
  populated). Empty string in the extract.
- Detection-limit convention (from the metadata, verbatim): "Values that were less than
  the lower detection limits of an analytical method were reported as a negative
  number: A value of -2 in the AG_PPM field is equivalent to <2 ppm Ag." So a negative
  value is a censored value whose absolute value is the detection limit. Zero is not a
  censoring marker in this dataset (no zeros observed in the Nevada feature elements).
- Known quirks: four DOE labs with different field forms, methods and element suites;
  within SRL-W Nevada samples two method families (SR, OR) with different suites; 809
  SRL-W samples analysed by both; 520 stream-sediment records with `methods == NONE`
  and no element data; coordinates digitised from 1:24,000 to 1:250,000 maps (about
  11 m implied precision for these labs); distinct samples sharing exact coordinates
  (LLL 92, SRL-W 395).

## mrds_nv.csv (Mineral Resources Data System, Nevada rows)

- Source: https://mrdata.usgs.gov/mrds/mrds-csv.zip, retrieved 2026-10-09 (archive
  last-modified 2022-08-23; systematic updates ceased in 2011). Public domain. Field
  descriptions: `data/raw/mrds.met`.
- Extract filter: `state == "Nevada"` and `country == "United States"` (15,408 of
  304,632 rows), all commodities and development statuses.
- One row represents: one MRDS site record (a deposit, mine, prospect, occurrence or
  plant). The same physical site can appear more than once (different `dep_id`, same or
  different `mrds_id`, same coordinates; e.g. "Lakeshore Mine" appears twice).
- Key: `dep_id` (unique). `mrds_id` is null for about half the records and repeats.
- Fields used downstream:
  - `latitude`, `longitude`: decimal degrees, WGS84. Precision varies (5 decimals for
    most Nevada gold producers, 3 decimals for about 100, 2 decimals for a few).
  - `dev_stat`: Producer, Past Producer, Prospect, Occurrence, Plant, Unknown
    (definitions in the .met; a Plant has no geological information).
  - `commod1`, `commod2`, `commod3`: primary, secondary, tertiary commodities, each a
    comma-separated list of commodity names (e.g. "Silver, Gold"; commodity names can
    themselves contain commas, e.g. "Sand and Gravel, Construction", so matching is on
    the whole word "Gold").
  - `site_name`, `dep_type`, `oper_type`, `prod_size`, `score`: descriptive only.
- Null means: information not available for the record.
- Known quirks: duplicate and near-duplicate sites; gold listed under Silver-primary
  records; 1,206 of the 2,850 Nevada gold-primary producers have data-quality score D.
