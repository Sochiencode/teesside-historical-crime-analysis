"""Limited source checks; writes raw data/evidence outside Git, never research totals.

Python 3.12 standard library. See docs/feasibility-pilot.md for executed commands.
No command acquires a complete historical archive. Range transfers are capped.
"""

import argparse
import csv
import hashlib
import http.cookiejar
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def retain(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != content:
        raise FileExistsError(f"Refusing to replace retained input: {path}")
    path.write_bytes(content)


def evidence(root, label, url, content, **extra):
    record = dict(url=url, retrieved_utc=datetime.now(timezone.utc).isoformat(),
                  bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), **extra)
    (root / 'evidence').mkdir(parents=True, exist_ok=True)
    # Each retrieval gets a separate evidence record; raw content is immutable.
    name = f"{label}-{time.time_ns()}.json"
    (root / 'evidence' / name).write_text(json.dumps(record, indent=2) + '\n')
    return record


def inspect_csv(content):
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    rows = list(reader)
    required = {'Month', 'Crime type', 'Reported by', 'Falls within', 'Latitude', 'Longitude'}
    if not required <= set(reader.fieldnames or []):
        raise ValueError('Unexpected street CSV schema')
    if not rows:
        raise ValueError('Empty street CSV does not validate feasibility')
    return dict(columns=reader.fieldnames, rows=len(rows),
                months=sorted({r['Month'] for r in rows}),
                categories=sorted({r['Crime type'] for r in rows}),
                reported_by=sorted({r['Reported by'] for r in rows}),
                falls_within=sorted({r['Falls within'] for r in rows}),
                missing_coordinates=sum(not r['Latitude'] or not r['Longitude'] for r in rows),
                missing_crime_ids=sum(not r.get('Crime ID') for r in rows),
                missing_lsoa=sum(not r.get('LSOA code') for r in rows))


class RangeZip(io.RawIOBase):
    """Seekable HTTP file with checked ranges and a hard 8 MiB transfer budget."""

    def __init__(self, url, root, label):
        super().__init__()
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30) as r:
            self.url = r.url
            self.size = int(r.headers['Content-Length'])
            self.etag = r.headers.get('ETag')
            self.last_modified = r.headers.get('Last-Modified')
        self.pos = self.transferred = 0
        self.root, self.label = root, label
        self.chunks = []

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        pos = offset if whence == 0 else (self.pos if whence == 1 else self.size) + offset
        if not 0 <= pos <= self.size:
            raise ValueError('Invalid seek')
        self.pos = pos
        return pos

    def read(self, n=-1):
        n = min(self.size - self.pos, n if n >= 0 else self.size - self.pos)
        if n == 0:
            return b''
        if self.transferred + n > 8 * 1024 * 1024:
            raise ValueError('Pilot transfer budget exceeded')
        start, end = self.pos, self.pos + n - 1
        headers = {'Range': f'bytes={start}-{end}'}
        if self.etag:
            headers['If-Match'] = self.etag
        with urllib.request.urlopen(urllib.request.Request(self.url, headers=headers), timeout=60) as r:
            expected = f'bytes {start}-{end}/{self.size}'
            if r.status != 206 or r.headers.get('Content-Range') != expected:
                raise ValueError('Server ignored/changed range; refusing full archive transfer')
            b = r.read(n + 1)
        if len(b) != n:
            raise ValueError('Incomplete or oversized range')
        name = f'{self.label}-{start}-{end}.range'
        retain(self.root / 'raw' / name, b)
        self.chunks.append(evidence(self.root, name, self.url, b, start=start, end=end,
                                   etag=self.etag, archive_bytes=self.size))
        self.pos += n
        self.transferred += n
        return b


def archive_sample(root, snapshot, months):
    if not re.fullmatch(r'20\d\d-\d\d', snapshot):
        raise ValueError('Expected YYYY-MM snapshot')
    source = f'https://data.police.uk/data/archive/{snapshot}.zip'
    remote = RangeZip(source, root, snapshot)
    profiles = []
    with zipfile.ZipFile(remote) as z:
        for month in months:
            matches = [n for n in z.namelist() if n.endswith(f'{month}-cleveland-street.csv')]
            if len(matches) != 1:
                raise ValueError(f'Expected exactly one Cleveland street member for {month}: {matches}')
            member = matches[0]
            info = z.getinfo(member)
            if info.file_size > 5 * 1024 * 1024:
                raise ValueError('Unexpectedly large pilot CSV')
            content = z.read(member)  # zipfile verifies the member CRC, not the whole archive MD5.
            profile = inspect_csv(content)
            if profile['months'] != [month] or profile['reported_by'] != ['Cleveland Police']:
                raise ValueError('Member content does not match requested month/force')
            retain(root / 'raw' / f'{snapshot}__{Path(member).name}', content)
            record = evidence(root, f'{snapshot}__{month}', source, content, member=member,
                              crc32=f'{info.CRC:08x}', archive_url=remote.url,
                              archive_bytes=remote.size, archive_etag=remote.etag,
                              archive_last_modified=remote.last_modified,
                              whole_archive_checksum_verified=False,
                              profile=profile)
            profiles.append(record)
    result = dict(snapshot=snapshot, transfer_bytes=remote.transferred, samples=profiles)
    (root / 'evidence' / f'sample-{snapshot}.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


def current(root):
    url = 'https://data.police.uk/data/'
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    with opener.open(url, timeout=30) as r:
        page = r.read().decode()
    token = re.search("name='csrfmiddlewaretoken' value='([^']+)'", page).group(1)
    fields = dict(csrfmiddlewaretoken=token, date_from='2026-08', date_to='2026-08',
                  forces='cleveland', include_crime='on')
    request = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(),
                                     headers={'Referer': url})
    with opener.open(request, timeout=60) as r:
        page = r.read().decode()
        fetch_url = r.url
    progress = re.search(r'"url":\s*"(/data/progress/[^\"]+)"', page).group(1)
    for _ in range(30):
        with opener.open('https://data.police.uk' + progress, timeout=30) as r:
            result = json.load(r)
        if result['status'] == 'ready':
            break
        if result['status'] == 'error':
            raise RuntimeError('Publisher export failed')
        time.sleep(2)
    else:
        raise TimeoutError(f'Export not ready; resume from {fetch_url}')
    with opener.open(result['url'], timeout=60) as r:
        content = r.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise ValueError('Current export exceeds pilot budget')
    retain(root / 'raw' / 'cleveland-2026-08.zip', content)
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        names = z.namelist()
        if names != ['2026-08/2026-08-cleveland-street.csv']:
            raise ValueError(f'Unexpected export members: {names}')
        csv_bytes = z.read(names[0])
    profile = inspect_csv(csv_bytes)
    if profile['months'] != ['2026-08'] or profile['reported_by'] != ['Cleveland Police']:
        raise ValueError('Current export content does not match requested month/force')
    retain(root / 'raw' / Path(names[0]).name, csv_bytes)
    report = evidence(root, 'current', result['url'], content, fetch_url=fetch_url,
                      selections={k: v for k, v in fields.items() if k != 'csrfmiddlewaretoken'},
                      member=names[0], member_sha256=hashlib.sha256(csv_bytes).hexdigest(),
                      profile=profile)
    (root / 'evidence' / 'current-profile.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def archive_plan(root):
    url = 'https://data.police.uk/data/archive/'
    with urllib.request.urlopen(url, timeout=30) as r:
        page = r.read()
    label = f'archive-listing-{time.time_ns()}'
    retain(root / 'raw' / (label + '.html'), page)
    evidence(root, label, url, page)
    rows = []
    for block in re.findall(r'<div class="download">([\s\S]*?)</div>', page.decode()):
        link = re.search(r'href="(/data/archive/\d{4}-\d{2}\.zip)"', block)
        dates = re.search(r'Contains data from (\w+ \d{4}) to (\w+ \d{4})', block)
        size = re.search(r'\(([\d.]+)\s*([^<)]+)\)', block)
        checksum = re.search(r'class="md5sum">([^<]+)', block)
        if link and dates and size and checksum:
            start, end = [datetime.strptime(d, '%b %Y').strftime('%Y-%m') for d in dates.groups()]
            rows.append(dict(url='https://data.police.uk' + link[1], start=start, end=end,
                             size=size[1] + ' ' + size[2], md5=checksum[1],
                             publisher_md5_valid=bool(re.fullmatch(r'[0-9a-fA-F]{32}', checksum[1]))))
    need, chosen = '2015-01', []
    while need <= '2026-08':
        candidates = [r for r in rows if r['start'] <= need <= r['end']]
        if not candidates:
            raise ValueError(f'No advertised archive covering {need}')
        best = max(candidates, key=lambda r: r['end'])
        if not best['publisher_md5_valid']:
            raise ValueError('Chosen archive has malformed publisher MD5; do not repair it')
        chosen.append(best)
        y, m = map(int, best['end'].split('-'))
        need = f'{y + 1}-01' if m == 12 else f'{y}-{m + 1:02}'
    def index(month):
        y, m = map(int, month.split('-'))
        return y * 12 + m
    maximum = max(min(index(r['end']), index('2026-08')) -
                  max(index(r['start']), index('2015-01')) + 1 for r in rows)
    result = dict(advertised_snapshots=len(rows), requested_months=140,
                  maximum_requested_months_per_snapshot=maximum, chosen=chosen,
                  lower_bound=(140 + maximum - 1) // maximum,
                  malformed_unselected_md5=[r['url'] for r in rows if not r['publisher_md5_valid']],
                  caveat='Listing coverage only; not member completeness or comparability')
    (root / 'evidence' / 'archive-plan.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


def population(root):
    jobs = []
    for dataset in ['NM_2002_1', 'NM_2010_1', 'NM_2014_1']:
        for suffix in ['def.sdmx.json', 'time.def.sdmx.json']:
            jobs.append((f'{dataset}-{suffix}',
                         f'https://www.nomisweb.co.uk/api/v01/dataset/{dataset}/{suffix}'))
    for label, dataset, geography, dates in [
        ('population-la-pilot', 'NM_2002_1', 'E06000002', '2015,2025'),
        ('population-wards-pilot', 'NM_2014_1', 'E05012441,E05012442,E05012456', '2024'),
        ('population-wards-2015-pilot', 'NM_2014_1', 'E05012441,E05012442,E05012456', '2015'),
    ]:
        query = urllib.parse.urlencode(dict(geography=geography, date=dates,
                                           gender=0, c_age=200, measures=20100))
        jobs.append((label, f'https://www.nomisweb.co.uk/api/v01/dataset/{dataset}.data.csv?{query}'))
    jobs.append(('nomis-copyright', 'https://www.nomisweb.co.uk/home/copyright.asp'))
    records = []
    for label, url in jobs:
        with urllib.request.urlopen(url, timeout=30) as r:
            b = r.read(1024 * 1024 + 1)
        if len(b) > 1024 * 1024:
            raise ValueError('Population pilot response exceeds budget')
        if '.data.csv?' in url:
            rows = list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
            if not rows or any(not x.get('OBS_VALUE') for x in rows):
                raise ValueError('Population query returned no usable observations')
            profile = [dict(code=x['GEOGRAPHY_CODE'], geography_type=x['GEOGRAPHY_TYPE'],
                            year=x['DATE_NAME'], status=x['OBS_STATUS_NAME'],
                            age=x['C_AGE_NAME'], gender=x['GENDER_NAME']) for x in rows]
            retain(root / 'raw' / (label + '.csv'), b)
        else:
            profile = None
            retain(root / 'raw' / f'{label}-{time.time_ns()}.response', b)
        records.append(evidence(root, label, url, b, profile=profile))
    (root / 'evidence' / 'population-pilot.json').write_text(json.dumps(records, indent=2) + '\n')
    print('Retrieved population metadata and 8 population observations; no rates calculated.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/workspace/crime-pilot'))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('current')
    sub.add_parser('archive-plan')
    sub.add_parser('population')
    sample = sub.add_parser('archive-sample')
    sample.add_argument('snapshot')
    sample.add_argument('months', nargs='+')
    args = parser.parse_args()
    if Path(__file__).resolve().parents[1] in args.root.resolve().parents or args.root.resolve() == Path(__file__).resolve().parents[1]:
        raise ValueError('Raw data directory must be outside the checkout')
    if args.command == 'current':
        current(args.root)
    elif args.command == 'archive-plan':
        archive_plan(args.root)
    elif args.command == 'population':
        population(args.root)
    else:
        archive_sample(args.root, args.snapshot, args.months)


if __name__ == '__main__':
    main()
