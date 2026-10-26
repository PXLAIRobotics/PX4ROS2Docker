"""Reference-based campus landmarks and lightweight architectural detail.

Dimensions other than mapped footprints are explicit approximations in site.json.
"""
import json
import math

import mapbox_earcut
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box as rectangle, shape
from shapely.ops import transform, unary_union

from geometry import box, element, extrude, material, mesh_part, primitive, static_model, write_stl

STEEL='0.72 0.74 0.71 1'
DARK='0.12 0.16 0.19 1'
GLASS='0.25 0.42 0.49 1'


def components(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type=='Polygon':
        return [geometry]
    return [p for p in geometry.geoms if p.geom_type=='Polygon' and p.area>0.001]


def beam(model,name,a,b,radius=.10,colour=STEEL):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    delta=b-a
    length=float(np.linalg.norm(delta))
    primitive(model,name,(a+b)/2,(radius,length),colour,kind='cylinder',
              rpy=(0,math.atan2(np.linalg.norm(delta[:2]),delta[2]),math.atan2(delta[1],delta[0])))


def add_arena(parent,polygon,height,meshes,config,oid):
    # The survey footprint contains the unfinished hall opening. It is not a
    # 24 m deep outdoor courtyard: build a roofed shell around an empty hall.
    outer=Polygon(polygon.exterior)
    rect=np.asarray(outer.minimum_rotated_rectangle.exterior.coords)[:4]
    sides=np.roll(rect,-1,axis=0)-rect
    u=max(sides,key=lambda v:abs(v[0])/np.linalg.norm(v))
    u=u/np.linalg.norm(u)
    if u[0]<0:u=-u
    v=np.asarray([-u[1],u[0]])
    centre=rect.mean(axis=0)
    width=float(np.ptp(rect@u));depth=float(np.ptp(rect@v))
    yaw=math.atan2(u[1],u[0]);wall=.55;entry=8;glazing=4.2
    model=static_model(parent,'corda_arena',(*centre,0),yaw)
    ivory='0.72 0.70 0.66 1'
    box(model,'floor',(0,0,.08),(width,depth,.16),'0.36 0.37 0.36 1')
    box(model,'roof',(0,0,height-.22),(width,depth,.44),'0.40 0.43 0.43 1')
    for side in [-1,1]:
        box(model,f'side_{side}',(side*(width-wall)/2,0,height/2),(wall,depth,height),ivory)
    box(model,'rear',(0,(depth-wall)/2,height/2),(width,wall,height),ivory)
    front=-(depth-wall)/2
    box(model,'upper_front',(0,front,(height+glazing)/2),(width,wall,height-glazing),ivory)
    # The centre doors are held open for this simulation. Glass panels retain
    # physical collisions; the door opening has no hidden full-footprint mesh.
    panel_count=max(1,int((width-entry)/2/2.8))
    panel_width=(width-entry)/2/panel_count
    for side in [-1,1]:
        for i in range(panel_count):
            x=side*(entry/2+(i+.5)*panel_width)
            box(model,f'glass_{side}_{i}',(x,front,glazing/2),(panel_width-.09,.10,glazing),GLASS,transparency=.58)
            box(model,f'mullion_{side}_{i}',(side*(entry/2+i*panel_width),front,glazing/2),(.09,.16,glazing),DARK)
    box(model,'door_lintel',(0,front,3.8),(entry,.25,.35),DARK)
    box(model,'entrance_canopy',(0,front-1.4,4.4),(entry+3,3,.24),DARK)
    # Thin internal galleries leave the main hall open, following the venue's
    # three-level reference; seating, stairs and room layout are not surveyed.
    for level in [6,12,18]:
        for side in [-1,1]:
            box(model,f'gallery_{level}_{side}',(side*(width/2-2.4),0,level),(4,depth-1,.32),'0.40 0.39 0.37 1')
        box(model,f'gallery_rear_{level}',(0,depth/2-2.4,level),(width-8,4,.32),'0.40 0.39 0.37 1')
    # Simplified projecting cube frames and coloured panels from the current
    # campus renders, not the unrelated unbuilt 2022 competition proposal.
    colours=['0.52 0.12 0.40 1','0.73 0.28 0.18 1','0.30 0.19 0.48 1']
    for group,cx in enumerate([-width*.33,0,width*.33]):
        for j in range(3):
            x=cx+(j-1)*2.8;z=9+3.0*((group+j)%4);y=front-.85;size=2.6
            for k,d in enumerate([-size/2,size/2]):
                box(model,f'frame_v_{group}_{j}_{k}',(x+d,y,z),(.10,1.4,size),DARK)
                box(model,f'frame_h_{group}_{j}_{k}',(x,y,z+d),(size,1.4,.10),DARK)
            box(model,f'panel_{group}_{j}',(x,front-.33,z),(size-.2,.12,size-.2),colours[(group+j)%3])
    # Forecourt connects the doors to open campus ground.
    box(model,'entrance_plaza',(0,front-8,.025),(width*.8,16,.05),'0.58 0.57 0.53 1',False)
    doorway=centre+v*(front-1)
    return {'name':'corda_arena','grb_oidn':oid,'area_m2':round(outer.area,3),
            'height_m':height,'height_source':config['source'],'detail':'hollow roofed hall with glazed entrance',
            'door_width_m':entry,'door_height_m':3.625,'door_centre_enu_m':doorway.tolist(),
            'local_yaw_rad':yaw,'survey_courtyard_replaced_by_roof':len(polygon.interiors),
            'interior_layout':'approximate empty hall with three gallery levels; simulation doors held open'}


def add_office_bands(model,polygon,centre,height):
    coords=np.asarray(polygon.exterior.coords)-centre
    index=0
    for z in np.arange(2.7,height-1,3):
        for a,b in zip(coords[:-1],coords[1:]):
            delta=b-a;length=float(np.linalg.norm(delta))
            if length<1:continue
            box(model,f'window_band_{index}',(*(a+b)/2,z),(length*.90,.06,1.25),GLASS,False,
                rpy=(0,0,math.atan2(delta[1],delta[0])))
            index+=1


def add_tower(parent,config,forward,meshes,source):
    features=json.loads((source/'data/landmarks.geojson').read_text())['features']
    feature=next(f for f in features if f['properties']['OIDN']==config['grb_knw_oidn'])
    footprint=transform(forward.transform,shape(feature['geometry']))
    centre=footprint.centroid
    model=static_model(parent,'philips_water_tower',(centre.x,centre.y,0))
    height=config['height_m'];deck=height-4.5
    leg_base=4.4;leg_top=3.0
    corners=[(-1,-1),(1,-1),(1,1),(-1,1)]
    for i,(sx,sy) in enumerate(corners):
        box(model,f'footing_{i}',(sx*leg_base,sy*leg_base,.25),(1.7,1.7,.5),'0.55 0.54 0.50 1')
        beam(model,f'leg_{i}',(sx*leg_base,sy*leg_base,.5),(sx*leg_top,sy*leg_top,deck),.24)
    for level,z in enumerate([6,12,18,24]):
        r=leg_base+(leg_top-leg_base)*z/deck
        r2=leg_base+(leg_top-leg_base)*(z+6)/deck
        for i,(sx,sy) in enumerate(corners):
            tx,ty=corners[(i+1)%4]
            beam(model,f'tie_{level}_{i}',(sx*r,sy*r,z),(tx*r,ty*r,z),.10)
            if z+6<=deck:
                beam(model,f'brace_a_{level}_{i}',(sx*r,sy*r,z),(tx*r2,ty*r2,z+6),.09)
                beam(model,f'brace_b_{level}_{i}',(tx*r,ty*r,z),(sx*r2,sy*r2,z+6),.09)
    # A closed revolved saucer tank, with a sloping underside and shallow cap.
    profile=[(.0,deck), (2.9,deck), (8.2,height-1.5), (8.2,height-.8), (7.9,height), (.0,height)]
    vertices=[];faces=[];segments=64
    # Nonzero rings plus two axial vertices avoid degenerate cap triangles.
    for radius,z in profile[1:-1]:
        vertices.extend([(radius*math.cos(t),radius*math.sin(t),z) for t in np.arange(segments)*2*math.pi/segments])
    for ring in range(3):
        for i in range(segments):
            a=ring*segments+i;b=ring*segments+(i+1)%segments;c=b+segments;d=a+segments
            faces.extend([[a,b,c],[a,c,d]])
    bottom=len(vertices);vertices.append((0,0,deck));top=len(vertices);vertices.append((0,0,height))
    for i in range(segments):
        j=(i+1)%segments
        faces.extend([[bottom,j,i],[top,3*segments+i,3*segments+j]])
    path=meshes/'water_tower_tank.stl'
    write_stl(path,np.asarray(vertices),faces)
    mesh_part(model,'saucer_tank',path,(0,0),'0.62 0.65 0.62 1')
    primitive(model,'tank_top',(0,0,height+.015),(7.8,.03),'0.23 0.29 0.28 1',kind='cylinder',collision=False)
    # A coarse spiral stair keeps the tower recognisable without an expensive
    # detailed stair asset. All support members and treads have collisions.
    primitive(model,'stair_axis',(0,0,deck/2),(.16,deck),STEEL,kind='cylinder')
    for i in range(96):
        angle=i*2*math.pi/24;z=.5+i*(deck-1)/96
        box(model,f'stair_{i}',(.9*math.cos(angle),.9*math.sin(angle),z),(1.5,.45,.12),STEEL,
            rpy=(0,0,angle))
    return {'name':'philips_water_tower','east_m':centre.x,'north_m':centre.y,'height_m':height,
            'grb_knw_oidn':config['grb_knw_oidn'],'dimensions':'approximate photo-based tank, supports and stairs',
            'position_source':'native GRB KNW footprint, manually identified against official orthophoto; source label is mast'}


def flat_mesh(polygons,path,z):
    vertices=[];faces=[]
    for poly in polygons:
        rings=[np.asarray(poly.exterior.coords)[:-1]]+[np.asarray(r.coords)[:-1] for r in poly.interiors]
        xy=np.concatenate(rings);ends=np.cumsum([len(r) for r in rings],dtype=np.uint32)
        tris=mapbox_earcut.triangulate_float64(xy,ends).reshape(-1,3)
        for tri in tris:
            a,b,c=xy[tri]
            if np.cross(b-a,c-a)<0:tri=tri[::-1]
            faces.append((tri+len(vertices)).tolist())
        vertices.extend(np.column_stack([xy,np.full(len(xy),z)]))
    write_stl(path,np.asarray(vertices),faces)


def add_parking(parent,config,obstacles,meshes,exclusions=None):
    polygon=Polygon(config['outline_enu_m'])
    surface=polygon.difference(obstacles.buffer(1.5))
    if exclusions is not None: surface=surface.difference(exclusions)
    if surface.is_empty:raise ValueError(f'Parking inside buildings: {config["name"]}')
    model=static_model(parent,config['name'])
    for i,p in enumerate(components(surface)):
        path=meshes/f'{config["name"]}_paving_{i}.stl'
        centre,_,_=extrude(p,lambda xy:np.full(len(xy),.025),path)
        mesh_part(model,f'paving_{i}',path,centre,'0.25 0.26 0.25 1',False)
    centre=polygon.centroid;angle=config.get('yaw_rad',0)
    local=affinity.rotate(affinity.translate(surface,-centre.x,-centre.y),-angle,origin=(0,0),use_radians=True)
    xmin,ymin,xmax,ymax=local.bounds
    marks=[];stalls=[]
    # Five-metre bays, 2.6 m spacing and 6 m driving aisles. This is a simplified
    # marked layout within traced areas, not a claim of exact current capacity.
    for row,y in enumerate(np.arange(ymin+1,ymax-4,16)):
        for side in [0,1]:
            base=y+side*11
            for x in np.arange(xmin+1,xmax-2.6,2.6):
                bay=rectangle(x,base,x+2.6,base+5)
                if not local.covers(bay):continue
                stalls.append((x+1.3,base+2.5))
                for line in [LineString([(x,base),(x,base+5)]),LineString([(x,base),(x+2.6,base)]),LineString([(x+2.6,base),(x+2.6,base+5)])]:
                    marks.append(line.buffer(.055,cap_style=2))
    world_marks=[affinity.translate(affinity.rotate(p,angle,origin=(0,0),use_radians=True),centre.x,centre.y) for p in marks]
    if marks:
        path=meshes/f'{config["name"]}_markings.stl'
        flat_mesh(world_marks,path,.035)
        mesh_part(model,'bay_markings',path,(0,0),'0.93 0.92 0.84 1',False)
    return {'name':config['name'],'area_m2':round(surface.area,2),'marked_bays':len(stalls),
            'source':config['source'],'outline_enu_m':config['outline_enu_m'],'yaw_rad':angle,'layout':'approximate 2.6 x 5 m bays with 6 m aisles'}


def add_landscape(parent,site,forward,meshes,report,source):
    report['landmarks']=[add_tower(parent,site['water_tower'],forward,meshes,source)]
    features=json.loads((source/'data/buildings.geojson').read_text())['features']
    obstacles=unary_union([transform(forward.transform,shape(f['geometry'])) for f in features])
    from landscape import surface_geometry, add_surfaces
    surfaces, reference = surface_geometry(source, site, obstacles)
    add_surfaces(parent, surfaces, reference, meshes, report)
    exclusions = surfaces['green'].union(surfaces['road']).union(surfaces['path'])
    report['parking']=[add_parking(parent,p,obstacles,meshes,exclusions) for p in site['parking']]


def add_corda5(parent,polygon,meshes,config,oid):
    """Separate the entrance drum, office wings and curved low hall."""
    model=static_model(parent,'corda_5')
    drum=Point(*config['drum_centre_enu_m']).buffer(config['drum_radius_m'],resolution=20)
    remaining=polygon
    masks=[('entrance_drum',drum,config['drum_height_m']),
           ('north_offices',Polygon(config['north_wing_outline_enu_m']),config['office_height_m']),
           ('south_offices',Polygon(config['south_wing_outline_enu_m']),config['office_height_m'])]
    pieces=[]
    for name,mask,height in masks:
        region=remaining.intersection(mask)
        remaining=remaining.difference(mask)
        for i,p in enumerate(components(region)):
            if p.area>.1:pieces.append((f'{name}_{i}',p,height))
    for i,p in enumerate(components(remaining)):
        if p.area>.1:pieces.append((f'curved_hall_{i}',p,config['hall_height_m']))
    for name,p,height in pieces:
        path=meshes/f'building_{oid}_{name}.stl'
        centre,_,_=extrude(p,lambda xy,h=height:np.full(len(xy),h),path)
        mesh_part(model,name,path,centre,config['facade_colour'])
        add_office_bands(model,p,(0,0),height)
    # Red entrance accent beside the pale cylindrical stair/reception drum.
    x,y=config['drum_centre_enu_m']
    box(model,'entrance_accent',(x-9.2,y-5,config['drum_height_m']/2),(1.3,2,config['drum_height_m']),'0.53 0.12 0.11 1',False)
    return {'name':'corda_5','grb_oidn':oid,'area_m2':round(polygon.area,3),
            'height_m':max(p[2] for p in pieces),'height_source':config['source'],
            'detail':'separate low curved hall, three-storey office wings and entrance drum',
            'sections':[{'name':name,'height_m':height,'area_m2':round(p.area,3)} for name,p,height in pieces],
            'partition_area_m2':round(sum(p.area for name,p,height in pieces),3)}


def add_sawtooth(parent,polygon,meshes,config,oid):
    model=static_model(parent,config['name'])
    rect=np.asarray(polygon.minimum_rotated_rectangle.exterior.coords)[:4]
    sides=np.roll(rect,-1,axis=0)-rect
    axis=max(sides,key=np.linalg.norm);axis=axis/np.linalg.norm(axis)
    if axis[1]<0:axis=-axis
    angle=math.atan2(axis[1],axis[0])
    local=affinity.rotate(polygon,-angle,origin=(0,0),use_radians=True)
    xmin,ymin,xmax,ymax=local.bounds
    count=config['roof_teeth'];pitch=(xmax-xmin)/count
    high=config['height_m'];low=config['low_height_m'];covered=0
    for i in range(count):
        a=xmin+i*pitch;b=a+pitch
        mask=affinity.rotate(rectangle(a,ymin-1,b,ymax+1),angle,origin=(0,0),use_radians=True)
        for j,p in enumerate(components(polygon.intersection(mask))):
            if p.area<.001:continue
            # Slice intersections can leave sub-millimetre collinear edges;
            # remove them before float32 STL export to avoid collapsed faces.
            p=p.simplify(.002,preserve_topology=True)
            path=meshes/f'building_{oid}_tooth_{i}_{j}.stl'
            roof=lambda xy,a=a:low+(np.asarray(xy)@axis-a)/pitch*(high-low)
            centre,_,_=extrude(p,roof,path,split_visual=True)
            # One closed wedge per tooth gives the steep clerestory face real
            # collision geometry, not just a painted zig-zag on a flat roof.
            link=element(model,'link',name=f'tooth_{i}_{j}')
            element(link,'pose',f'{centre[0]} {centre[1]} 0 0 0 0')
            collision=element(link,'collision',name=f'tooth_{i}_{j}')
            element(element(element(collision,'geometry'),'mesh'),'uri',f'model://corda_campus/meshes/{path.name}')
            for surface,colour in [('roof',config['roof_colour']),('facade',config['facade_colour'])]:
                visual=element(link,'visual',name=surface)
                element(element(element(visual,'geometry'),'mesh'),'uri',f'model://corda_campus/meshes/{path.stem}_{surface}.stl')
                material(visual,colour)
            covered+=p.area
        # Clerestory strip across the high edge, clipped to the footprint.
        section=local.intersection(LineString([(b-.015,ymin-1),(b-.015,ymax+1)]))
        if section.geom_type=='LineString' and section.length>.3:
            mid=section.centroid
            world=affinity.rotate(mid,angle,origin=(0,0),use_radians=True)
            box(model,f'clerestory_{i}',(world.x,world.y,(high+low)/2),(.05,section.length,high-low-.12),GLASS,False,rpy=(0,0,angle))
    if abs(covered-polygon.area)>.05:raise ValueError('Sawtooth roof does not cover its mapped footprint')
    return {'name':config['name'],'grb_oidn':oid,'area_m2':round(polygon.area,3),
            'height_m':high,'low_height_m':low,'height_source':config['source'],
            'roof':'sawtooth','roof_teeth':count,'pitch_m':pitch,'axis_enu':axis.tolist(),
            'covered_area_m2':round(covered,3),'roof_colour':config['roof_colour']}
