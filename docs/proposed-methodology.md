# Proposed reproducible methodology

Status: proposal for review, 13 October 2026. Read the [source and feasibility audit](source-geography-feasibility-audit.md) for the unresolved access and geography gate. The [limited pilot](feasibility-pilot.md) has exercised small acquisition and boundary checks. This methodology remains a proposal for full acquisition and research analysis, which have not run.

## Workflow and software

After audit approval, use Python with `requests` or `httpx`, `pandas`, `pyarrow`, `geopandas`, `shapely` and `pyproj`; use DuckDB when useful for partitioned queries. Add Streamlit only in the later dashboard milestone. Choose compatible versions, commit a lockfile in that implementation milestone, and document the supported Python version. Reviewing the documents requires no runtime dependencies. The permitted pilot adds small acquisition scripts and a boundary-only review map; its dependencies and executed commands are documented separately.

Separate commands for source discovery, acquisition, validation, geography preparation, assignment, aggregation and dashboard startup. Supply configuration for date range, source force, products, area definitions and boundary vintage. Preserve immutable inputs; all transformed outputs should be rebuildable. Each stage should fail clearly when required coverage or schemas are absent, rather than produce a plausible empty dashboard.

Use the existing isolated cloud checkout; do not create a Git worktree unless explicitly requested. No service, database server, API key or application startup is required for this milestone. Future startup instructions and dependency setup should be saved and exercised when those components exist.

## Manageable storage and provenance

Keep source ZIP/CSV files unchanged outside Git, grouped by source/product/month. Download only required force/month products where the source permits; do not acquire all England and Wales merely for these areas. Preserve an unfiltered force-level source if that is the smallest official unit. Estimate size from a representative file before committing to the full period.

Store a manifest in JSON/CSV with source URLs, retrieval timestamps, reference periods, licence, response metadata, bytes, SHA-256 and validation status. Preserve archive-member names and record counts. Download to temporary paths, verify, then atomically rename; retry only transient failures with bounded backoff. Skip existing content only after checksum/manifest validation. A rerun must not silently replace a revised publisher file: retain the old version and record a new retrieval.

Use compressed Parquet for normalised working data, partitioned by product/year/month; retain coordinates and source provenance. Keep street crime, outcomes and stop-and-search in separate datasets and schemas. DuckDB can query Parquet without a long-running database. GeoPackage is suitable for a small reviewed boundary collection with explicit CRS and vintage. Keep raw files and large working outputs out of commits. Git should hold code, configuration, small manifests, documentation and test fixtures with appropriate licences; document storage location and backup requirements.

## Pilot-derived source-vintage policy

The pilot identifies a minimum four-snapshot advertised cover, with September–December 2023 overlapping. Proposed canonical selection uses the newest of the selected snapshots for each `(product, force, month)`, retaining every raw vintage without concatenation. This does not guarantee the latest historic revisions. December 2023 sample files already demonstrate outcome-field revision across snapshots. Verify all member inventories, gaps, schemas and recording conventions before treating the chosen blocks as a comparable series.

The review map uses May 2025 ward proxies. Retrieved population tables return 2022 ward geography, whose polygons differ even where codes match. Consider adopting verified 2022 fixed ward polygons for future population rates, or resolve a justified alignment; do not assume the map and denominator extents coincide. No 2026 denominator was advertised in the relevant inspected tables. Count-based preparation remains possible while rate alignment is unresolved.

## Acquisition and comparability gates

Use the audit's [endpoint-level source register](source-geography-feasibility-audit.md#source-register-endpoints-coverage-and-acquisition-route). Resolve versioned URLs, formats, dates, licences and official geography before implementing acquisition. Separate automatic metadata/file requests from manual edition, table and boundary decisions. A manually supplied official export needs recorded selections and provenance, and must pass the same validation as an automatically acquired file; do not accept typed counts or undocumented replacements.

Maintain two independent records: an acquisition matrix (advertised, retrieved, parsed and validated status by product/force/month) and a comparability log for each proposed combination or comparison. The latter must assess observational unit, date semantics, inclusion rules, categories, recording practice, source revisions, spatial anonymisation, boundary vintage and denominator population universe. Assign compatible, compatible with a documented transformation, incompatible or unresolved status, with evidence. A successful download or parse must never set comparability status automatically. Block affected trends, combined sources or rates until their required comparability checks pass, even where file integrity is valid.

## Assignment and overlap policy

1. Validate official polygons, codes, vintage, CRS, geometry validity and extent. Reproject publication coordinates from their documented CRS for distance calculations; British National Grid (EPSG:27700) is a candidate metric CRS once verified. Never calculate metre distances in longitude/latitude degrees.
2. Retain all raw rows and mark malformed coordinates, missing coordinates and records outside the selected geography separately. Preserve source row number and file checksum as a provenance key. Do not deduplicate records just because coordinates, category and month match: multiple incidents can share these values, especially ASB.
3. Join points to reviewed polygons with an explicit edge rule. A point covered by exactly one disjoint reporting polygon receives that area. A point on a shared edge or covered by multiple reporting areas is flagged ambiguous, counted once in an ambiguity bucket and excluded from mutually exclusive area counts pending a documented rule. Repeated executions must produce the same result.
4. Define one **exclusive reporting partition** for Middlesbrough and the three community proxies. Confirm pairwise overlaps are empty apart from edges before aggregation. Keep overlapping descriptive geography as separate memberships; never sum overlapping memberships into a combined total. If an authority and its subareas are later added, display the authority and subareas separately or aggregate the union from records, not summed subtotals.
5. Report assigned, outside, missing-coordinate and ambiguous counts at each stage. Confirm exclusive area totals equal the relevant uniquely assigned source-row total. Boundary sensitivity analysis should report counts near edges and how alternative rules change results, without pretending to know true incident locations.

Investigate potential duplicated source deliveries using file hashes and publisher identifiers where present. Missing or repeated Crime IDs require product-specific investigation. Stable source-row provenance is not proof of distinct real-world incidents; document limitations rather than dropping valid-looking duplicate rows indiscriminately.

## Validation and measures

Check ZIP integrity, encoding, schema, month consistency, force labels, category inventories, coordinate ranges and file-level row counts. Build a month-by-product-by-force coverage matrix. Record zero-row files separately from unavailable files. Test reviewed spatial rules with points inside, outside, on an edge, in an overlap and with missing coordinates. Test that acquisition reruns do not create duplicate partitions and that aggregates reconcile to assigned rows. Later tests should exercise actual pipeline behaviour, not merely imports or syntax.

Produce monthly street-crime counts by original category and a separately labelled ASB series. Describe these as published records, with source limitations. Link outcomes to street crime only after validating identifier and date semantics; report linkage rates, one-to-many relationships and unmatched rows. Do not add outcome rows or stop-and-search events to crime totals.

For a confirmed latest month M in 2026, compare January–M with January–M in each eligible previous year, requiring complete comparable coverage. Exclude or clearly mark incomplete historical periods. Show counts and changes with base counts; avoid percentage change from zero. If recent files can be revised, store acquisition vintage and use a common snapshot policy.

Population rates are optional until compatible denominators are verified. Use an authority population only for that authority extent. For community proxies, prefer sums of published estimates for whole statistical areas that exactly match the chosen boundary, or official estimates explicitly supplied for that boundary. Do not allocate populations solely by polygon land area or assume a ward lookup gives an exact crosswalk. If residentially weighted estimation is necessary, document assumptions and uncertainty and obtain review first.

Select denominators consistent with each observation period and geography vintage, record revision status, and disclose the rate unit and population reference date. A census snapshot can support a labelled snapshot comparison, not an unexplained annual rate series. If no suitably aligned 2026 denominator exists, show matching-month counts without population-adjusted rates. Never silently carry forward a population estimate or mix geographic vintages.

## Review gates and later deliverables

Gate 1: resolve blocked authoritative access; verify latest month, achievable historical coverage, licences, boundary versions and proposed maps. Gate 2: approve definitions and denominator policy before writing acquisition/analysis code. Later milestones can then implement and execute acquisition, validation and analysis, followed by a Streamlit dashboard with separate product views, explicit ASB and matching-month 2026 comparisons.

Every later report should distinguish confirmed results, assumptions, missingness, failed checks and unrun checks. Keep a transformation log and reproducible run metadata including source hashes, software versions, configuration and code commit. The dashboard must carry the same limitations as the underlying analysis. The pull request now contains the audit, methodology, limited pilot scripts, evidence metadata and a boundary-only review map. It must not be merged automatically.
