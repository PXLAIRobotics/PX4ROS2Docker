"""Small deterministic SDF and watertight mesh helpers for the campus generator."""
import struct
import xml.etree.ElementTree as ET
import mapbox_earcut
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

def element(parent, tag, text=None, **attributes):
    child = ET.SubElement(parent, tag, attributes)
    if text is not None:
        child.text = str(text)
    return child


def save_xml(path, root):
    ET.indent(root, space='  ')
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def roof_function(polygon, height, low=None):
    if low is None:
        return lambda xy: np.full(len(xy), height, dtype=float)
    # Follow the long footprint axis, with the high facade on its southern end.
    rectangle = np.asarray(polygon.minimum_rotated_rectangle.exterior.coords)[:-1]
    sides = np.roll(rectangle, -1, axis=0) - rectangle
    axis = sides[np.argmax(np.linalg.norm(sides, axis=1))]
    axis = axis / np.linalg.norm(axis)
    if axis[1] < 0:
        axis = -axis
    projection = np.asarray(polygon.exterior.coords)[:, :2] @ axis
    lo, hi = projection.min(), projection.max()
    return lambda xy: height - (np.asarray(xy) @ axis - lo) / (hi - lo) * (height - low)


def extrude(polygon, roof, path, split_visual=False, base_z=0):
    """Watertight concave extrusion, including courtyard holes and sloped caps."""
    polygon = orient(polygon, sign=1.0)
    rings = [np.asarray(polygon.exterior.coords)[:-1, :2]]
    rings += [np.asarray(r.coords)[:-1, :2] for r in polygon.interiors]
    xy = np.concatenate(rings)
    ends = np.cumsum([len(r) for r in rings], dtype=np.uint32)
    triangles = mapbox_earcut.triangulate_float64(xy, ends).reshape(-1, 3)
    # Earcut's top triangles must face upward for ray-based sensors.
    for i, triangle in enumerate(triangles):
        a, b, c = xy[triangle]
        cross = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        if cross < 0:
            triangles[i] = triangle[::-1]
    centre = np.asarray([polygon.centroid.x, polygon.centroid.y])
    n = len(xy)
    vertices = np.vstack([np.column_stack([xy-centre, np.full(n,base_z)]),
                          np.column_stack([xy-centre, roof(xy)])])
    faces = [t[::-1].tolist() for t in triangles] + [(t+n).tolist() for t in triangles]
    start = 0
    for ring in rings:
        for i in range(len(ring)):
            a, b = start+i, start+(i+1) % len(ring)
            faces.extend([[a, b, b+n], [a, b+n, a+n]])
        start += len(ring)
    write_stl(path, vertices, faces)
    if split_visual:
        cap_count = len(triangles)
        # Keep one closed collision mesh; separate visible surfaces share its
        # exact vertices so roof and facade can have independent materials.
        write_stl(path.with_stem(path.stem+'_roof'), vertices, faces[cap_count:2*cap_count])
        write_stl(path.with_stem(path.stem+'_facade'), vertices, faces[:cap_count]+faces[2*cap_count:])
    # Check closed topology and cap coverage; holes must not be filled accidentally.
    edges = {}
    for face in faces:
        for a,b in zip(face, face[1:]+face[:1]):
            edge = tuple(sorted((a,b))); edges[edge] = edges.get(edge, 0) + 1
    if not all(count == 2 for count in edges.values()):
        raise ValueError(f'Non-manifold mesh: {path}')
    cap_area = sum(Polygon(xy[t]).area for t in triangles)
    if abs(cap_area-polygon.area) > 0.001:
        raise ValueError(f'Cap does not match footprint: {path}')
    return centre, len(vertices), len(faces)


def write_stl(path, vertices, faces):
    # Binary STL supplies explicit triangle normals to both Ogre and DART/ODE.
    data = bytearray(b'GRB campus mesh; attribution in tools/campus/SOURCES.md'.ljust(80,b' '))
    data.extend(struct.pack('<I',len(faces)))
    for face in faces:
        a,b,c = vertices[face]
        normal = np.cross(b-a,c-a)
        normal /= np.linalg.norm(normal)
        data.extend(struct.pack('<12fH',*normal,*a,*b,*c,0))
    path.write_bytes(data)


def material(visual, colour):
    mat = element(visual, 'material')
    element(mat, 'ambient', colour); element(mat, 'diffuse', colour)


def primitive(parent, name, xyz, size, colour, kind='box', collision=True,
              rpy=(0,0,0), transparency=0):
    link = element(parent, 'link', name=name)
    element(link,'pose',' '.join(map(str,(*xyz,*rpy))))
    for tag in (['visual','collision'] if collision else ['visual']):
        part=element(link,tag,name=name)
        geom=element(element(part,'geometry'),kind)
        if kind=='box': element(geom,'size',' '.join(map(str,size)))
        elif kind=='cylinder':
            element(geom,'radius',size[0]);element(geom,'length',size[1])
        if tag=='visual':
            material(part,colour)
            if transparency: element(part,'transparency',transparency)
    return link


def box(parent, name, xyz, size, colour, collision=True, rpy=(0,0,0), transparency=0):
    return primitive(parent,name,xyz,size,colour,collision=collision,rpy=rpy,transparency=transparency)


def static_model(parent,name,xyz=(0,0,0),yaw=0):
    model=element(parent,'model',name=name)
    element(model,'static','true')
    element(model,'pose',' '.join(map(str,(*xyz,0,0,yaw))))
    return model


def mesh_part(parent,name,path,centre,colour,collision=True):
    link=element(parent,'link',name=name)
    element(link,'pose',f'{centre[0]} {centre[1]} 0 0 0 0')
    for tag in (['visual','collision'] if collision else ['visual']):
        part=element(link,tag,name=name)
        element(element(element(part,'geometry'),'mesh'),'uri',f'model://corda_campus/meshes/{path.name}')
        if tag=='visual': material(part,colour)
    return link


