"""Synthetic rooftop drone deck: low-poly structure and flat, flush markings."""
import math
import numpy as np
from shapely.geometry import Point, Polygon, box as rectangle

from details import flat_mesh
from geometry import box, extrude, mesh_part, primitive, static_model


def add_landing_deck(parent,roof_polygon,roof,launch,meshes):
    x,y,size=launch['east_m'],launch['north_m'],launch['pad_size_m']
    half=size/2;chamfer=launch['deck_chamfer_m'];thickness=launch['deck_thickness_m']
    outline=Polygon([(x-half+chamfer,y-half),(x+half-chamfer,y-half),
                     (x+half,y-half+chamfer),(x+half,y+half-chamfer),
                     (x+half-chamfer,y+half),(x-half+chamfer,y+half),
                     (x-half,y+half-chamfer),(x-half,y-half+chamfer)])
    corners=np.asarray(outline.exterior.coords)[:-1]
    if not roof_polygon.contains(outline.buffer(1)):
        raise ValueError('Landing deck needs at least one metre of roof around its outline')
    top=float(roof(corners).max()+launch['pad_clearance_m'])
    model=static_model(parent,'rooftop_landing_deck')
    # Continuous, roof-conforming plinth replaces spindly corner posts. Both
    # the plinth and deck are closed, colliding solids; the finish is flush.
    plinth=outline.buffer(-.35,join_style=2)
    path=meshes/'platform_plinth.stl'
    centre,_,_=extrude(plinth,lambda xy:np.full(len(xy),top-thickness),path,
                       base_z=lambda xy:roof(xy)-.005)
    mesh_part(model,'roof_conforming_plinth',path,centre,'0.25 0.29 0.31 1')
    path=meshes/'platform_deck.stl'
    centre,_,_=extrude(outline,lambda xy:np.full(len(xy),top),path,base_z=top-thickness)
    mesh_part(model,'deck',path,centre,'0.58 0.63 0.65 1')
    # Low-profile perimeter fascia and intermediate support ribs sit below
    # the flight surface, keeping the entire landing zone unobstructed.
    for i,(a,b) in enumerate(zip(corners,np.roll(corners,-1,axis=0))):
        midpoint=(a+b)/2;delta=b-a
        box(model,f'edge_fascia_{i}',(*midpoint,top-thickness/2),
            (np.linalg.norm(delta),.085,thickness*.7),'0.12 0.17 0.19 1',False,
            rpy=(0,0,math.atan2(delta[1],delta[0])))
    for i,dx in enumerate([-1.7,0,1.7]):
        # Roof pitch sets a different support depth at each end of the deck.
        for j,dy in enumerate([-2.67,2.67]):
            px,py=x+dx,y+dy
            bottom=float(roof(np.asarray([[px,py]]))[0])+.025
            length=top-thickness-bottom
            if length>.05:
                box(model,f'support_rib_{i}_{j}',(px,py,bottom+length/2),(.15,.18,length),'0.43 0.48 0.50 1',False)
    def paint(name,polygons,z,colour):
        path=meshes/f'platform_{name}.stl'
        flat_mesh(polygons,path,z)
        mesh_part(model,name,path,(0,0),colour,False)
    paint('surface',[outline.buffer(-.13,join_style=2)],top+.002,'0.12 0.20 0.23 1')
    boundary=outline.buffer(-.25,join_style=2).difference(outline.buffer(-.34,join_style=2))
    radius=launch['landing_circle_radius_m']
    circle=Point(x,y).buffer(radius,resolution=48).difference(Point(x,y).buffer(radius-.12,resolution=48))
    h=[rectangle(x-.65,y-1,x-.44,y+1),rectangle(x+.44,y-1,x+.65,y+1),rectangle(x-.44,y-.11,x+.44,y+.11)]
    paint('white_markings',[boundary,circle]+h,top+.006,'0.94 0.95 0.91 1')
    # Symmetric amber approach/corner brackets, all below one centimetre high.
    chevrons=[]
    for sx in [-1,1]:
        for sy in [-1,1]:
            cx,cy=x+sx*2.30,y+sy*2.30
            chevrons.extend([rectangle(cx-.26,cy-.07,cx+.26,cy+.07),
                             rectangle(cx+sx*.19-.07,cy-sy*.19-.26,cx+sx*.19+.07,cy-sy*.19+.26)])
    paint('amber_markings',chevrons,top+.008,'0.93 0.62 0.13 1')
    # Inset marker lenses are visual only; no point lights or extra sensors.
    for i,(dx,dy) in enumerate([(0,-2.55),(2.55,0),(0,2.55),(-2.55,0)]):
        primitive(model,f'light_bezel_{i}',(x+dx,y+dy,top+.009),(.11,.018),'0.49 0.54 0.56 1',kind='cylinder',collision=False)
        primitive(model,f'light_lens_{i}',(x+dx,y+dy,top+.020),(.075,.008),'0.20 0.76 0.53 1',kind='cylinder',collision=False)
    return top,{'name':'rooftop_landing_deck','size_m':size,'chamfer_m':chamfer,
                'deck_thickness_m':thickness,'landing_circle_radius_m':radius,
                'outline_enu_m':corners.tolist(),'plinth':'closed solid following the existing roof plane',
                'markings':'flush white H/circle/boundary, amber corner brackets, inset green marker lenses',
                'surface_collision':'single level closed deck; paint and lenses visual only',
                'synthetic_level_platform':True}
