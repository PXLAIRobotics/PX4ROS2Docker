#!/usr/bin/env python3
"""Offline regression checks for mapped landmarks and traversable Arena geometry.

Run with tools/campus/requirements.txt installed in an isolated GIS environment.
"""
from collections import Counter
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import numpy as np
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform, unary_union

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tools/campus'
ASSETS=ROOT/'Projects/ros2_workspace/src/px4_dev_examples/simulation'
site=json.loads((SOURCE/'site.json').read_text())
report=json.loads((ASSETS/'campus.json').read_text())
features=json.loads((SOURCE/'data/buildings.geojson').read_text())
assert '3812' in features['crs']['properties']['name']
projection=f'+proj=aeqd +lat_0={site["origin"]["latitude"]} +lon_0={site["origin"]["longitude"]} +datum=WGS84 +units=m'
to_local=Transformer.from_crs(3812,projection,always_xy=True)
to_geo=Transformer.from_crs(projection,4326,always_xy=True)
# Independent native-grid/geographic control point from the GRB response:
# catches reintroduction of the shifted service CRS84 conversion.
arena_feature=next(f for f in features['features'] if f['properties']['OIDN']==7690099)
p=arena_feature['geometry']['coordinates'][0][0]
lon,lat=Transformer.from_crs(3812,4326,always_xy=True).transform(*p)
assert abs(lon-5.35440837)<.000002 and abs(lat-50.95296239)<.000002
buildings=[transform(to_local.transform,shape(f['geometry'])) for f in features['features']]
obstacles=unary_union(buildings)
tower=report['landmarks'][0]
assert 90<tower['east_m']<110 and 15<tower['north_m']<35
assert not obstacles.contains(shape({'type':'Point','coordinates':[tower['east_m'],tower['north_m']]}))
assert len(report['parking'])==6 and sum(p['marked_bays'] for p in report['parking'])>200

sdf=ET.parse(ASSETS/'models/corda_campus/model.sdf').getroot()
arena=sdf.find("./model/model[@name='corda_arena']")
assert arena is not None and arena.findtext('static')=='true'
collisions=[]
for link in arena.findall('link'):
    link_pose=np.asarray(list(map(float,link.findtext('pose','0 0 0 0 0 0').split())))
    for collider in link.findall('collision'):
        pose=link_pose+np.asarray(list(map(float,collider.findtext('pose','0 0 0 0 0 0').split())))
        size=collider.findtext('geometry/box/size')
        assert size is not None, 'Arena must not retain the old solid footprint collision'
        collisions.append((np.asarray(pose[:3]),np.asarray(list(map(float,size.split())))/2))

def ray_hits(a,b):
    delta=b-a
    for centre,half in collisions:
        low,high=0.,1.
        for i in range(3):
            if abs(delta[i])<1e-10:
                if abs(a[i]-centre[i])>half[i]:break
            else:
                t0=(centre[i]-half[i]-a[i])/delta[i];t1=(centre[i]+half[i]-a[i])/delta[i]
                low=max(low,min(t0,t1));high=min(high,max(t0,t1))
                if low>high:break
        else:
            if low<=high:return True
    return False

front=np.asarray(list(map(float,arena.find("link/collision[@name='upper_front']/pose").text.split())))
assert not ray_hits(np.array([0.,front[1]-5,1.5]),np.array([0.,0.,1.5])), 'Entrance corridor must be open'
assert ray_hits(np.array([10.,front[1]-5,1.5]),np.array([10.,0.,1.5])), 'Glazing must retain collision'
assert ray_hits(np.array([0.,0.,30.]),np.array([0.,0.,20.])), 'Hall must have a roof'

# Every referenced STL exists and has finite vertices and nonzero normals.
for uri in sdf.iter('uri'):
    if not uri.text.endswith('.stl'):continue
    path=ASSETS/'models/corda_campus/meshes'/uri.text.rsplit('/',1)[1]
    data=path.read_bytes();count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+count*50 and count>0
    for i in range(84,len(data),50):
        values=struct.unpack_from('<12fH',data,i)
        assert all(math.isfinite(x) for x in values[:12])
        assert .99<sum(x*x for x in values[:3])<1.01
# Tank must be closed while the tower beneath it remains open lattice.
tank=ASSETS/'models/corda_campus/meshes/water_tower_tank.stl'
edges=Counter();data=tank.read_bytes()
for off in range(84,len(data),50):
    values=struct.unpack_from('<12fH',data,off)
    verts=[tuple(round(x,5) for x in values[i:i+3]) for i in [3,6,9]]
    for a,b in zip(verts,verts[1:]+verts[:1]):edges[tuple(sorted([a,b]))]+=1
assert all(n==2 for n in edges.values())
print('PASS: native-grid alignment, landmark placement, parking, open entrance, solid glazing/roof and mesh validity')
print('Water tower WGS84:',to_geo.transform(tower['east_m'],tower['north_m']))
print('Approximate marked bays:',sum(p['marked_bays'] for p in report['parking']))

# Scene simplification must retain the launch and named landmarks, and keep
# the original GIS snapshot available for future regeneration.
assert len(report['buildings'])<40 and len(report['culled_buildings'])>40
assert {b['name'] for b in report['buildings']} >= {'corda_1','corda_2','corda_3','corda_4','corda_5','corda_8','corda_arena'}
assert all(b['area_m2']<350 and b['distance_from_launch_m']>160 for b in report['culled_buildings'])
assert len(list(sdf.iter('visual')))<100 and len(list(sdf.iter('link')))<50
c5=next(b for b in report['buildings'] if b['name']=='corda_5')
assert abs(c5['partition_area_m2']-c5['area_m2'])<.1
assert len({p['height_m'] for p in c5['sections']})==3 and max(p['height_m'] for p in c5['sections'])<14
c8=next(b for b in report['buildings'] if b['name']=='corda_8')
assert c8['roof_teeth']==9 and abs(c8['area_m2']-c8['covered_area_m2'])<.05
# Inspect actual roof triangles: alternating valleys and ridges must exist in
# the collision geometry rather than only in decorative surface colours.
z_ranges=[]
for collider in sdf.findall("./model/model[@name='corda_8']/link/collision"):
    uri=collider.findtext('geometry/mesh/uri')
    data=(ASSETS/'models/corda_campus/meshes'/uri.rsplit('/',1)[1]).read_bytes()
    top=[]
    for off in range(84,len(data),50):
        row=struct.unpack_from('<12fH',data,off)
        if row[2]>.2:top.extend(row[5:12:3])
    z_ranges.append((min(top),max(top)))
assert len(z_ranges)==9 and all(lo<8.01 and hi>10.49 for lo,hi in z_ranges)
print('PASS: peripheral culling, batched scene size, Corda 5 sections and nine physical sawtooth ridges')
