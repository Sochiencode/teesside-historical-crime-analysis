# Source, geography and feasibility audit

Audit date: 13 October 2026 (Africa/Lagos). Requested coverage: January 2015 through the latest published street-crime month in 2026. Status: **provisional; authoritative sources could not be retrieved**. No crime data have been acquired or analysed. This document concerns recorded police crime and anti-social behaviour (ASB), independently of news events.

## Evidence and access status

The following HTTPS requests were executed on 13 October 2026 using Python 3.12 `urllib.request`, normal TLS verification and a 25-second timeout. Each failed with `Tunnel connection failed: 403 Forbidden`. This is a proxy access failure before receipt of the source; it does not establish that the source is unavailable publicly. No successful source retrieval date, source contents, licence confirmation or coverage confirmation can be claimed.

| Intended source | URL attempted | Intended evidence | Result |
| --- | --- | --- | --- |
| Police publication metadata | https://data.police.uk/api/crime-last-updated | Latest published street-crime month | Blocked: proxy 403 |
| Police availability metadata | https://data.police.uk/api/crimes-street-dates | Advertised month/force availability | Blocked: proxy 403 |
| Police downloads | https://data.police.uk/data/ | Monthly bulk files and actual selectable coverage | Blocked: proxy 403 |
| Police archive candidate | https://data.police.uk/data/archive/ | Historic retention or archive access; endpoint existence unverified | Blocked: proxy 403 |
| Police source notes | https://data.police.uk/about/ | Licence, anonymisation and quality caveats | Blocked: proxy 403 |
| Police API documentation | https://data.police.uk/docs/ | Endpoint semantics, category and geographic limits | Blocked: proxy 403 |
| ONS population estimates | https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates | Denominators, vintages, revisions and coverage | Blocked: proxy 403 |
| ONS Open Geography Portal | https://geoportal.statistics.gov.uk/ | Dated authority, ward, LSOA and OA boundaries and lookups | Blocked: proxy 403 |
| Redcar and Cleveland council | https://www.redcar-cleveland.gov.uk/elections-and-voting/electoral-wards | Official ward names and community relationship; page existence unverified | Blocked: proxy 403 |

Additional authoritative discovery locations, **not retrieved**: Middlesbrough council (https://www.middlesbrough.gov.uk/), Local Government Boundary Commission for England (https://www.lgbce.org.uk/), Nomis census tables (https://www.nomisweb.co.uk/), and the Open Government Licence text (https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

### Licence and source register requirements

Police open data and ONS/council geographic products are candidates for use under the Open Government Licence, but that is an expectation, **not a verified licence grant for any selected asset**. Geographic products can include separate OS copyright and attribution conditions. Census tables, population estimates and boundary files each need their own verified licence, required attribution and version. No third-party mirror or news account substitutes for provenance.

For every subsequently retrieved asset, record exact download and metadata URLs, publisher, UTC retrieval timestamp, HTTP status, publication/reference date, licence URL and attribution, geography vintage, covered months/areas, filename, bytes and SHA-256. Record this failed audit attempt separately from successful retrieval. Resolve direct dataset URLs before acquisition; portal landing pages are discovery sources, not reproducible download specifications.

## Latest month and historical feasibility

**Latest published month: unverified.** Do not substitute October 2026, the latest completed calendar month, or an assumed publication lag. Retrieve publication and availability metadata, then confirm the latest advertised month has a usable Cleveland street-crime download. Availability of one force or product does not establish completeness of another. Confirm the latest month separately for outcomes and stop-and-search if those products are later included.

**January 2015 onward: not established as downloadable.** The police service may expose a rolling history; neither its exact retention window nor a historic archive was accessible here. A current API cannot be assumed to recover older monthly records. When access works, enumerate actual bulk-download months, compare them with API availability, and probe the earliest requested month and each gap. Record month/force/product presence and file validity, rather than interpreting an absent file as zero crime.

If the official live service lacks early years, seek an authoritative archive or a documented response from the publisher. Do not silently fill gaps with scraped news, substitute force-wide aggregate statistics for street records, or use an unverified mirror. If a trustworthy compatible archive cannot be obtained, recommend a shorter confirmed window and retain January 2015 as an unmet research objective.

## Proposed geography for review

Middlesbrough local authority is one analysis area. South Bank, Grangetown and Eston are proposed separate communities in neighbouring Redcar and Cleveland; that administrative relationship and the precise selected ward names/codes must be checked against official products. These communities must not be treated as neighbourhoods inside the Middlesbrough authority polygon.

| Requested area | Recommended initial operational definition | Review needed |
| --- | --- | --- |
| Middlesbrough | Official local-authority boundary with its code and vintage frozen | Check authority extent changes since 2015; select appropriate boundary resolution |
| South Bank | Official ward polygon matching South Bank, if verified | Check extent against the named settlement and historic ward versions |
| Grangetown | Official ward polygon matching Grangetown, if verified | Check settlement extent, industrial land and historic versions |
| Eston | Official ward polygon matching Eston, if verified | Check whether the community extends into adjoining wards |

These are **ward-based proxies**, not confirmed settlement boundaries. A community is a social/place name; a ward is an electoral division; an OA/LSOA is a census/statistical area. Their names and extents are not interchangeable. Do not invent polygons from postcode labels, neighbourhood centroids or a radius around a town centre.

Preferred first option: use one verified ward vintage as fixed operational community proxies throughout the time series, title results “South Bank ward proxy” etc., and publish maps and codes for review. Check council maps and boundary-review reports before adopting that vintage. Alternative: agree settlement polygons built from whole census OAs/LSOAs with official maps and local review. This is more work but can make denominators defensible. No final community polygon is approved by this audit.

Fixed boundaries allow comparable geography over time; historical ward polygons instead describe changing administrative populations and must be reported as separate versions. Catalogue effective dates, ward creation/abolition and code/name changes. Do not assume a shared name means an unchanged polygon. Check both electoral reviews and the 2011-to-2021 statistical geography transition, including splits, merges and lookup limitations.

## Risks to comparisons

- **Anonymised geography:** published street coordinates are approximate, not exact incident addresses. Snapping can move incidents across borders; some records lack usable coordinates. Boundary assignment cannot recover the true location. Quantify ambiguous and unlocated records and test a documented boundary-distance sensitivity band.
- **Coverage:** street data are published police records, not a census of crime or victimisation. Force-wide figures, unlocated records and crimes outside the published location scope may differ from local street counts. Obtain publisher notes on excluded offences and reporting practices.
- **Missing months:** maintain expected versus available versus successfully parsed months for every product and force. Empty areas, missing files, failed downloads and genuine zero observations are distinct.
- **Categories:** retrieve category definitions for applicable periods, inspect actual labels/codes, and document changes in classifications or recording practice. Retain original categories; only harmonise with an explicit versioned mapping. Broad totals may still be affected by recording changes.
- **ASB:** report it as its own series and denominator convention. Do not fold ASB into a crime total, infer unique incidents from missing identifiers, or treat it as an outcome record.
- **Outcomes and stop-and-search:** these have different units, timing, coverage and geography. Keep separate; outcome publication month is not necessarily incident month and multiple outcome rows must not inflate crime counts.
- **Population:** ONS mid-year authority estimates and suitable small-area estimates are candidate annual denominators; census 2011/2021 populations are snapshots, not annual estimates. Confirm exact years and geographic bases. Avoid interpolated precision or blanket use of 2021 populations for 2015–2026.
- **2026:** use only the confirmed published months, compare the same calendar months in earlier years and flag incomplete periods. Do not describe partial counts as annual totals or annualise by default. Publication coverage and population-reference coverage are separate constraints.

## Feasibility decision and next gate

A Python geospatial workflow is plausible, but full-period feasibility, latest month, licences, actual boundary versions and aligned population denominators remain unresolved. Required source-domain additions have been saved to the cloud configuration draft. Apply settings and verify access before claiming those questions answered; further downloads may expose additional asset-host requirements.

Before implementation approval, complete the source register, confirm the available month matrix, map and review the community proxies, inspect changes and identify a compatible denominator strategy. The first milestone must remain provisional until these checks succeed. No full analysis or dashboard should begin merely because these documents exist.
