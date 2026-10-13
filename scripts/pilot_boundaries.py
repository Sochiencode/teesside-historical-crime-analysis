"""Retrieve scoped ONS May 2025 polygons and make a boundary-only review map.

Requires matplotlib, shapely 2.1.2. Raw inputs remain outside the checkout.
No crime records or population rates are mapped.
"""

import argparse
import itertools
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from feasibility_pilot import evidence, retain

SERVICES = {
    'wards': ('WD_MAY_2025_UK_BFC_V2',
              "LAD25CD='E06000003' AND WD25CD IN ('E05012441','E05012442','E05012456')"),
    'lad': ('LAD_MAY_2025_UK_BFC_V2', "LAD25CD IN ('E06000002','E06000003')"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/workspace/crime-pilot'))
    parser.add_argument('--map', type=Path, required=True)
    args = parser.parse_args()
    checkout = Path(__file__).resolve().parents[1]
    if args.root.resolve() == checkout or checkout in args.root.resolve().parents:
        raise ValueError('Raw directory must be outside checkout')
    datasets = {}
    for key, (service, where) in SERVICES.items():
        base = 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/' + service
        query = base + '/FeatureServer/0/query?' + urllib.parse.urlencode({
            'where': where, 'outFields': '*', 'outSR': 27700, 'f': 'geojson', 'returnGeometry': 'true'})
        with urllib.request.urlopen(query, timeout=45) as r:
            content = r.read()
        a = json.loads(content)
        if 'error' in a or a.get('exceededTransferLimit'):
            raise ValueError('Failed/truncated query')
        expected = 3 if key == 'wards' else 2
        if len(a.get('features', [])) != expected:
            raise ValueError('Unexpected feature count')
        retain(args.root / 'raw' / f'scoped-{key}-2025.geojson', content)
        evidence(args.root, f'scoped-{key}', query, content, crs='EPSG:27700',
                 source_vintage='May 2025', features=expected)
        datasets[key] = a

    os.environ.setdefault('MPLCONFIGDIR', str(args.root / 'matplotlib-cache'))
    os.environ.setdefault('XDG_CACHE_HOME', str(args.root / 'cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, PathPatch
    from matplotlib.path import Path as PlotPath
    from shapely.geometry import shape
    from shapely.geometry.polygon import orient

    areas = []
    context = None
    for key, a in datasets.items():
        for f in a['features']:
            props, geom = f['properties'], shape(f['geometry'])
            if not geom.is_valid or geom.is_empty:
                raise ValueError('Invalid boundary; do not repair raw geometry silently')
            if key == 'lad' and props['LAD25CD'] == 'E06000003':
                context = geom
            else:
                code = props['WD25CD'] if key == 'wards' else props['LAD25CD']
                name = props['WD25NM'] if key == 'wards' else props['LAD25NM']
                areas.append((name, code, geom))
    overlaps = []
    for a, b in itertools.combinations(areas, 2):
        overlaps.append(dict(a=a[1], b=b[1], overlap_m2=a[2].intersection(b[2]).area))
    containment = {code: g.difference(context).area for name, code, g in areas if name != 'Middlesbrough'}
    result = dict(valid_geometries=5, pairwise_overlaps=overlaps,
                  ward_area_outside_redcar_cleveland_m2=containment,
                  crs='EPSG:27700', vintage='May 2025')
    (args.root / 'evidence' / 'boundary-checks.json').write_text(json.dumps(result, indent=2) + '\n')

    def draw(ax, geom, face, edge, alpha=1):
        for polygon in getattr(geom, 'geoms', [geom]):
            polygon = orient(polygon, sign=1)
            verts, codes = [], []
            for ring in [polygon.exterior, *polygon.interiors]:
                coords = list(ring.coords)
                verts.extend(coords)
                codes.extend([PlotPath.MOVETO] + [PlotPath.LINETO] * (len(coords) - 2) + [PlotPath.CLOSEPOLY])
            ax.add_patch(PathPatch(PlotPath(verts, codes), facecolor=face, edgecolor=edge,
                                   linewidth=.7, alpha=alpha))

    fig, ax = plt.subplots(figsize=(11, 9))
    draw(ax, context, '#f1f3f5', '#91979d')
    palette = {'Middlesbrough': '#7da8c6', 'South Bank': '#e5aa52',
               'Grangetown': '#75b69b', 'Eston': '#c58abb'}
    for name, code, geom in areas:
        draw(ax, geom, palette[name], '#374151')
        p = geom.representative_point()
        label_pos = {'Grangetown': (461000, 522000), 'Eston': (461000, 517500)}.get(name, (p.x, p.y))
        ax.annotate(f'{name}\n{code}', (p.x, p.y), xytext=label_pos, fontsize=9, ha='center',
                    arrowprops=dict(arrowstyle='-', color='#374151') if label_pos != (p.x, p.y) else None,
                    bbox=dict(boxstyle='round,pad=.3', facecolor='white', alpha=.85, edgecolor='none'))
    ax.text(468000, 515000, 'Redcar and Cleveland\ncontext only (E06000003)', color='#636970', fontsize=9)
    ax.set_xlim(442000, 476000)
    ax.set_ylim(508000, 530000)
    ax.set_aspect('equal')
    ax.set_xlabel('British National Grid easting (metres)')
    ax.set_ylabel('British National Grid northing (metres)')
    ax.set_title('Proposed reporting areas for review\nONS May 2025 full-resolution coastal boundaries (V2)')
    ax.annotate('N', xy=(.95, .94), xytext=(.95, .84), xycoords='axes fraction',
                ha='center', arrowprops=dict(arrowstyle='->'))
    ax.plot([444000, 449000], [509200, 509200], color='#222', linewidth=3)
    ax.text(446500, 509550, '5 km', ha='center', fontsize=9)
    ax.legend(handles=[Patch(facecolor=palette[n], label=n + (' authority' if n == 'Middlesbrough' else ' ward proxy'))
                       for n in ['Middlesbrough', 'South Bank', 'Grangetown', 'Eston']], loc='lower right', fontsize=8)
    fig.text(.1, .025, 'Ward proxies are not confirmed community extents. No crime data shown.\n'
             'Source: ONS Geography / Ordnance Survey; May 2025 BFC V2. Licence verification gap documented in audit.',
             fontsize=8)
    fig.tight_layout(rect=(0, .06, 1, 1))
    args.map.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.map, dpi=170)
    plt.close(fig)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
