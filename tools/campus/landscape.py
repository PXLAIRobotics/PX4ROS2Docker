"""Lightweight campus-wide ground surfaces traced from the attributed orthophoto."""
import json
from shapely.geometry import box, shape
from shapely.ops import unary_union
from geometry import mesh_part, static_model


def surface_geometry(source, site, obstacles):
    data = json.loads((source/'data/landscape.json').read_text())
    if data['origin'] != site['origin']:
        raise ValueError('Landscape and world origins differ')
    groups = {'road': [], 'path': [], 'green': []}
    boundary = box(*site['bounds_m'])
    for feature in data['features']:
        geom = shape(feature['geometry'])
        if not geom.is_valid:
            raise ValueError(f'Invalid landscape trace: {feature["name"]}')
        if geom.geom_type == 'LineString':
            geom = geom.buffer(feature['width_m']/2, cap_style=1, join_style=1, resolution=4)
        geom = geom.intersection(boundary).difference(obstacles.buffer(.15))
        groups[feature['kind']].append(geom)
    groups = {kind: unary_union(parts) for kind, parts in groups.items()}
    groups['path'] = groups['path'].difference(groups['road'])
    groups['green'] = groups['green'].difference(groups['road'].union(groups['path']))
    return groups, data


def add_surfaces(parent, groups, data, meshes, report):
    from details import components, flat_mesh
    styles = {'road': ('landscape_roads', .012, '0.22 0.24 0.25 1'),
              'path': ('landscape_walkways', .018, '0.69 0.67 0.60 1'),
              'green': ('landscape_green', .009, '0.28 0.43 0.19 1')}
    report['landscape'] = {'source': data['source'], 'method': data['method'],
                           'feature_count': len(data['features']), 'surfaces': {}}
    for kind, (name, z, colour) in styles.items():
        polygons = components(groups[kind])
        if not polygons: continue
        model = static_model(parent, name)
        path = meshes/f'{name}.stl'
        flat_mesh(polygons, path, z)
        mesh_part(model, 'surface', path, (0, 0), colour, False)
        report['landscape']['surfaces'][kind] = {'area_m2': round(groups[kind].area, 2),
                                                'polygons': len(polygons), 'visual_only': True}
