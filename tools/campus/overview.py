"""Export the actual generated Gazebo visuals as a north-up ENU overview.

Project triangles and union them, retaining concave footprints and courtyards.
Includes analytic boxes/cylinders and full nested transforms (not convex hulls
of collision meshes). No external geographic basemap is involved.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Polygon
from shapely import union_all
from optimize import rotation, triangles


def projected_models(sdf_path):
    sdf_path = Path(sdf_path)
    meshes = sdf_path.parent/'meshes'
    root = ET.parse(sdf_path).getroot().find('model')
    models = {}
    hashes = {sdf_path.name: hashlib.sha256(sdf_path.read_bytes()).hexdigest()}
    def visit(el, rot, offset, model_name):
        pose = list(map(float, el.findtext('pose', '0 0 0 0 0 0').split()))
        if el.find('pose') is not None and el.find('pose').get('relative_to'):
            raise ValueError('Resolve relative_to frames before map export')
        offset = offset + rot @ np.asarray(pose[:3])
        rot = rot @ rotation(pose[3:])
        if el.tag == 'model' and el is not root: model_name = el.get('name')
        if el.tag == 'visual':
            geom = el.find('geometry')
            uri = geom.findtext('mesh/uri')
            if uri:
                file = meshes/uri.rsplit('/', 1)[-1]
                hashes['meshes/'+file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
            data = triangles(geom, meshes)
            scale = list(map(float, geom.findtext('mesh/scale', '1 1 1').split()))
            data = (data*np.asarray(scale)) @ rot.T + offset
            polygons = [Polygon(tri[:, :2]) for tri in data]
            models.setdefault(model_name, []).extend(p for p in polygons if p.area > 1e-7 and p.is_valid)
        for child in el:
            if child.tag in ('model', 'link', 'visual'):
                visit(child, rot, offset, model_name)
    visit(root, np.eye(3), np.zeros(3), root.get('name'))
    return {name: union_all(parts, grid_size=.001).buffer(0).simplify(.035, preserve_topology=True)
            for name, parts in models.items()}, hashes


def export_overview(sdf_path, report, output):
    from details import components
    models, hashes = projected_models(sdf_path)
    buildings = {b['name'] for b in report['buildings']}
    features = []
    for name, geom in models.items():
        if name in buildings: kind = 'building'
        elif name.startswith('parking_'): kind = 'parking'
        elif name == 'landscape_roads': kind = 'road'
        elif name == 'landscape_walkways': kind = 'path'
        elif name == 'landscape_green': kind = 'green'
        elif name == 'philips_water_tower': kind = 'tower'
        elif name == 'rooftop_landing_deck': kind = 'launch'
        else: continue
        parts = components(geom)
        if not parts: continue
        anchor = max(parts, key=lambda p:p.area).representative_point()
        features.append({'name': name, 'kind': kind, 'label_enu_m': [anchor.x, anchor.y],
                         'polygons': [{'outer': list(p.exterior.coords),
                                       'holes': [list(r.coords) for r in p.interiors]} for p in parts]})
    extent = union_all(list(models.values())).bounds
    bounds = [min(report['bounds_m'][0], extent[0])-5, min(report['bounds_m'][1], extent[1])-5,
              max(report['bounds_m'][2], extent[2])+5, max(report['bounds_m'][3], extent[3])+5]
    data = {'schema_version': 2, 'origin': report['origin'], 'bounds_m': bounds,
            'coordinate_system': 'Gazebo world ENU metres',
            'source': 'Projected union of generated Gazebo visual triangles and analytic primitives',
            'source_sha256': hashes, 'features': features}
    Path(output).write_text(json.dumps(data, separators=(',', ':'))+'\n')
    return data
