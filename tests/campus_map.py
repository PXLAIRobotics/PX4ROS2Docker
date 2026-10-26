"""Check generated map coverage, actual Gazebo poses and geographic alignment."""
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import numpy as np
from pyproj import Transformer
from shapely.geometry import Point, Polygon, shape
from shapely.ops import transform, unary_union

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Projects/ros2_workspace/src/px4_dev_examples'))
from px4_dev_examples.map_coordinates import geodetic_to_enu
SOURCE=ROOT/'tools/campus';ASSETS=ROOT/'Projects/ros2_workspace/src/px4_dev_examples/simulation'
data=json.loads((ASSETS/'campus-map.json').read_text());report=json.loads((ASSETS/'campus.json').read_text())
assert data['schema_version']==2 and data['origin']==report['origin']
def polygon(feature):return unary_union([Polygon(p['outer'],p['holes']) for p in feature['polygons']])
features={f['name']:f for f in data['features']};geoms={name:polygon(f) for name,f in features.items()}
assert all(g.is_valid and g.area>0 for g in geoms.values())
assert set(b['name'] for b in report['buildings']) <= features.keys()
for path,expected in data['source_sha256'].items():
 assert hashlib.sha256((ASSETS/'models/corda_campus'/path).read_bytes()).hexdigest()==expected,path
origin=data['origin'];projection=f'+proj=aeqd +lat_0={origin["latitude"]} +lon_0={origin["longitude"]} +datum=WGS84 +units=m'
to_enu=Transformer.from_crs(3812,projection,always_xy=True)
to_geo=Transformer.from_crs(projection,4326,always_xy=True)
for east,north in [(-11,-10),(0,0),(-246,-132),(404,388),(100,24)]:
 lon,lat=to_geo.transform(east,north)
 actual=geodetic_to_enu(lat,lon,origin['latitude'],origin['longitude'])
 assert math.dist(actual,(east,north))<.01,(actual,east,north)
# Independent source footprints: retaining concavity must not fill the courtyards.
footprints=json.loads((SOURCE/'data/buildings.geojson').read_text())['features']
for name in ['corda_1','corda_2','corda_3','corda_8']:
 oid=next(b['grb_oidn'] for b in report['buildings'] if b['name']==name)
 source=next(f for f in footprints if f['properties']['OIDN']==oid)
 expected=transform(to_enu.transform,shape(source['geometry'])).simplify(.12,preserve_topology=True)
 assert geoms[name].symmetric_difference(expected).area<expected.area*.015,name
 assert geoms[name].area<=expected.convex_hull.area+1
# Arena is made of boxes: it was missing from the old mesh-collision-only map.
sdf=ET.parse(ASSETS/'models/corda_campus/model.sdf').getroot()
a=sdf.find("./model/model[@name='corda_arena']")
pose=list(map(float,a.findtext('pose').split()));roof=a.find("link/collision[@name='roof']")
size=list(map(float,roof.findtext('geometry/box/size').split()))
for x,y in [(-size[0]/2,-size[1]/2),(size[0]/2,size[1]/2)]:
 p=Point(pose[0]+x*math.cos(pose[5])-y*math.sin(pose[5]),pose[1]+x*math.sin(pose[5])+y*math.cos(pose[5]))
 assert geoms['corda_arena'].buffer(.02).covers(p)
assert geoms['philips_water_tower'].covers(Point(report['landmarks'][0]['east_m'],report['landmarks'][0]['north_m']))
assert geoms['rooftop_landing_deck'].covers(Point(-11,-10))
for name in ['parking_corda_1','parking_southwest','parking_southeast']:
 assert next(p for p in report['parking'] if p['name']==name)['yaw_rad']==.28
for kind,name in [('road','landscape_roads'),('path','landscape_walkways'),('green','landscape_green')]:
 assert geoms[name].area>500
 assert geoms[name].bounds[0]<-100 and geoms[name].bounds[2]>150
 assert geoms[name].bounds[1]<0 and geoms[name].bounds[3]>200
assert report['performance']['after_batching']['visual']<100
print('PASS: source hashes, all 29 buildings, concave footprints, rotated Arena boxes, landmarks, WGS84 alignment, straight parking rows and campus-wide surfaces')
