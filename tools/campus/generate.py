#!/usr/bin/env python3
"""Build offline Gazebo campus assets from attributed GRB snapshots (no network)."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from pyproj import Transformer
from shapely.geometry import Point, Polygon, shape
from shapely.ops import transform

from geometry import box, element, extrude, material, roof_function, save_xml
from details import add_arena, add_landscape, add_office_bands, add_corda5, add_sawtooth

from optimize import compact_static

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / 'Projects/ros2_workspace/src/px4_dev_examples/simulation'


def generate(output):
    site = json.loads((SOURCE/'site.json').read_text())
    origin = site['origin']
    projection = (f'+proj=aeqd +lat_0={origin["latitude"]} +lon_0={origin["longitude"]} '
                  '+datum=WGS84 +units=m')
    forward = Transformer.from_crs('EPSG:3812', projection, always_xy=True)
    inverse = Transformer.from_crs(projection, 'EPSG:4326', always_xy=True)
    snapshot = json.loads((SOURCE/'data/buildings.geojson').read_text())
    if '3812' not in snapshot.get('crs',{}).get('properties',{}).get('name',''):
        raise ValueError('Campus footprints must use native EPSG:3812 coordinates; refresh with fetch.py')
    buildings = snapshot['features']
    heights = {str(f['GRB_OIDN']): f for f in json.loads((SOURCE/'data/heights.json').read_text())}
    models = output/'models/corda_campus'; meshes = models/'meshes'; meshes.mkdir(parents=True,exist_ok=True)
    sdf = ET.Element('sdf', version='1.9'); campus = element(sdf,'model',name='corda_campus')
    element(campus,'static','true')
    report = {'origin':origin, 'bounds_m':site['bounds_m'], 'buildings':[], 'culled_buildings':[], 'notes':site['notes']}
    launch_polygon = launch_roof = None
    for feature in buildings:
        oid = str(feature['properties']['OIDN'])
        polygon = transform(forward.transform, shape(feature['geometry'])).simplify(site['simplify_m'], preserve_topology=True)
        if not polygon.is_valid or polygon.geom_type != 'Polygon':
            raise ValueError(f'Invalid/nonpolygon footprint: {oid}')
        override = site['buildings'].get(oid,{})
        perf=site.get('performance',{})
        distance=polygon.distance(Point(site['launch']['east_m'],site['launch']['north_m']))
        if not override and polygon.area<perf.get('small_building_area_m2',0) and distance>perf.get('omit_small_buildings_beyond_m',float('inf')):
            report['culled_buildings'].append({'grb_oidn':int(oid),'area_m2':round(polygon.area,3),'distance_from_launch_m':round(distance,2),'reason':'small peripheral building omitted for performance'})
            continue
        measured = heights.get(oid)
        if 'height_m' in override:
            height = override['height_m']; provenance = override['source']
        elif measured and measured['HN_P99'] and measured['HN_P99'] > 0:
            height = round(measured['HN_P99'],2); provenance = '3D GRB HN_P99, exact GRB OIDN match'
        else:
            height = 6 if polygon.area < 250 else 12
            provenance = 'estimated fallback: 6 m for small buildings, 12 m otherwise'
        low = override.get('low_height_m') if override.get('roof') == 'slope' else None
        roof = roof_function(polygon,height,low)
        if override.get('detail') == 'arena':
            report['buildings'].append(add_arena(campus,polygon,height,meshes,override,int(oid)))
            continue
        if override.get('detail') in ('corda5','sawtooth'):
            builder=add_corda5 if override['detail']=='corda5' else add_sawtooth
            report['buildings'].append(builder(campus,polygon,meshes,override,int(oid)))
            continue
        mesh = meshes/f'building_{oid}.stl'
        centre,nv,nf = extrude(polygon,roof,mesh,split_visual=low is not None)
        name = override.get('name',f'building_{oid}')
        model = element(campus,'model',name=name)
        element(model,'static','true')
        element(model,'pose',f'{centre[0]:.6f} {centre[1]:.6f} 0 0 0 0')
        link = element(model,'link',name='body')
        collision = element(link,'collision',name='building')
        element(element(element(collision,'geometry'),'mesh'),'uri',f'model://corda_campus/meshes/{mesh.name}')
        if low is not None:
            surfaces = [('roof', override.get('roof_colour','0.30 0.46 0.25 1')),
                        ('facade', override.get('facade_colour','0.63 0.65 0.68 1'))]
        else:
            surfaces = [('building',override.get('facade_colour','0.63 0.65 0.68 1'))]
        for surface, colour in surfaces:
            visual = element(link,'visual',name=surface)
            visual_mesh = mesh if surface == 'building' else mesh.with_stem(mesh.stem+'_'+surface)
            element(element(element(visual,'geometry'),'mesh'),'uri',f'model://corda_campus/meshes/{visual_mesh.name}')
            material(visual,colour)
        report['buildings'].append({'name':name,'grb_oidn':int(oid),'area_m2':round(polygon.area,3),
            'height_m':height,'low_height_m':low,'height_source':provenance,
            'height_quality':measured['H_KWAL'] if measured else None,
            'footprint_version_date':feature['properties']['VERSDATUM'],
            'courtyards':len(polygon.interiors),'vertices':nv,'faces':nf})
        if override.get('window_bands'):
            add_office_bands(model,polygon,centre,height)
        if int(oid) == site['launch']['building_oidn']:
            launch_polygon,launch_roof = polygon,roof
    add_landscape(campus,site,forward,meshes,report,SOURCE)
    launch = site['launch']; x,y,size = launch['east_m'],launch['north_m'],launch['pad_size_m']
    corners = np.asarray([[x-size/2,y-size/2],[x+size/2,y-size/2],[x+size/2,y+size/2],[x-size/2,y+size/2]])
    if launch_polygon is None or not launch_polygon.contains(Polygon(corners).buffer(1)):
        raise ValueError('Launch platform is not safely inside the selected roof')
    pad_top = float(launch_roof(corners).max()+launch['pad_clearance_m'])
    box(campus,'simulation_launch_platform',(x,y,pad_top-.075),(size,size,.15),'0.18 0.25 0.32 1')
    for i,(cx,cy) in enumerate(corners):
        bottom=float(launch_roof(np.asarray([[cx,cy]]))[0]); length=pad_top-.15-bottom
        if length > 0:
            box(campus,f'launch_support_{i}',(cx,cy,bottom+length/2),(.08,.08,length),'0.3 0.3 0.3 1',False)
    for name,dx,dy,sx,sy in [('left',-.5,0,.12,1.4),('right',.5,0,.12,1.4),('bar',0,0,1,.12)]:
        box(campus,'launch_mark_'+name,(x+dx,y+dy,pad_top+.008),(sx,sy,.012),'0.95 0.95 0.95 1',False)
    if site.get('performance',{}).get('batch_static_visuals'):
        report['performance']=compact_static(campus,meshes)
    referenced={uri.text.rsplit('/',1)[-1] for uri in sdf.iter('uri') if uri.text and uri.text.endswith('.stl')}
    # This directory contains generated meshes; remove obsolete generated parts
    # so in-place regeneration matches a fresh output folder.
    for path in meshes.glob('*.stl'):
        if path.name.startswith(('building_','parking_','water_tower_','batch_')) and path.name not in referenced:
            path.unlink()
    save_xml(models/'model.sdf',sdf)
    config=ET.Element('model');element(config,'name','corda_campus');element(config,'version','1.0')
    element(config,'sdf','model.sdf',version='1.9');element(config,'description','Untextured GRB campus buildings; sources and approximations in tools/campus/SOURCES.md')
    save_xml(models/'model.config',config)
    (models/'ATTRIBUTION.md').write_text((SOURCE/'SOURCES.md').read_text())
    (output/'Gazebo-GUI-LICENSE').write_bytes((SOURCE/'Gazebo-GUI-LICENSE').read_bytes())
    world=ET.Element('sdf',version='1.9');w=element(world,'world',name='corda_campus')
    physics=element(w,'physics',type='ode');element(physics,'max_step_size',.004);element(physics,'real_time_factor',1)
    element(w,'gravity','0 0 -9.8');element(w,'magnetic_field','6e-06 2.3e-05 -4.2e-05')
    scene=element(w,'scene');element(scene,'ambient','0.6 0.6 0.6 1');element(scene,'background','0.7 0.8 0.9 1');element(scene,'shadows','false')
    ground=element(w,'model',name='ground');element(ground,'static','true')
    box(ground,'ground',(0,0,-.1),(1200,1200,.2),'0.43 0.48 0.40 1')
    light=element(w,'light',name='sun',type='directional');element(light,'pose','0 0 500 0 0 0');element(light,'diffuse','0.9 0.9 0.9 1');element(light,'direction','-0.4 0.2 -0.9');element(light,'cast_shadows','false')
    spherical=element(w,'spherical_coordinates');element(spherical,'surface_model','EARTH_WGS84');element(spherical,'world_frame_orientation','ENU')
    element(spherical,'latitude_deg',origin['latitude']);element(spherical,'longitude_deg',origin['longitude']);element(spherical,'elevation',origin['ground_altitude_m'])
    element(element(w,'include'),'uri','model://corda_campus')
    save_xml(output/'worlds/corda_campus.sdf',world)
    gui = (SOURCE/'gui.config.in').read_text().replace('@CAMERA_POSE@',
        ' '.join(map(str,site.get('overview_camera_pose',[x+55,y-65,pad_top+50,0,.55,2.25]))))
    (output/'campus.gui.config').write_text(gui)
    lon,lat=inverse.transform(x,y)
    report['launch']={'east_m':x,'north_m':y,'latitude':lat,'longitude':lon,
        'roof_height_m':float(launch_roof(np.asarray([[x,y]]))[0]),'platform_top_m':pad_top,
        'model_spawn_z_m':pad_top+.28,'world_ground_altitude_m':origin['ground_altitude_m'],
        'yaw_rad':launch['yaw_rad'],'synthetic_level_platform':True}
    report['input_sha256']={str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [SOURCE/'site.json',SOURCE/'gui.config.in',SOURCE/'SOURCES.md',SOURCE/'data/buildings.geojson',SOURCE/'data/heights.json',SOURCE/'data/landmarks.geojson',SOURCE/'data/reference-requests.json']}
    (output/'campus.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'campus.env').write_text('# Generated; metres ENU, z above flat campus ground.\n'+
        f'export PX4_GZ_MODEL_POSE="{x},{y},{pad_top+.28:.6f},0,0,{launch["yaw_rad"]}"\n')
    print(f'Generated {len(report["buildings"])} buildings ({len(report["culled_buildings"])} small peripheral buildings omitted), rooftop spawn {report["launch"]}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    generate(parser.parse_args().output)
