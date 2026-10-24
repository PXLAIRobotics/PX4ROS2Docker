"""Bake static visuals by material, preserving collision shapes and openings."""
from copy import deepcopy
import math
import struct
import numpy as np

from geometry import element, write_stl


def rotation(rpy):
    r,p,y=rpy
    cr,sr,cp,sp,cy,sy=math.cos(r),math.sin(r),math.cos(p),math.sin(p),math.cos(y),math.sin(y)
    return np.asarray([[cy*cp,cy*sp*sr-sy*cr,cy*sp*cr+sy*sr],
                       [sy*cp,sy*sp*sr+cy*cr,sy*sp*cr-cy*sr],[-sp,cp*sr,cp*cr]])


def triangles(geometry,meshes):
    mesh=geometry.find('mesh')
    if mesh is not None:
        data=(meshes/mesh.findtext('uri').rsplit('/',1)[1]).read_bytes()
        result=[]
        for off in range(84,len(data),50):
            result.append(struct.unpack_from('<12fH',data,off)[3:12])
        return np.asarray(result).reshape(-1,3,3)
    box=geometry.find('box')
    if box is not None:
        half=np.asarray(list(map(float,box.findtext('size').split())))/2
        v=np.asarray([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])*half
        f=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
        return v[f]
    cyl=geometry.find('cylinder')
    if cyl is None:raise ValueError('Unsupported static visual geometry')
    radius=float(cyl.findtext('radius'));half=float(cyl.findtext('length'))/2
    # Thin structural members need fewer facets than Gazebo's default cylinders.
    n=16;angles=np.arange(n)*2*math.pi/n
    v=np.vstack([np.column_stack([radius*np.cos(angles),radius*np.sin(angles),np.full(n,-half)]),
                 np.column_stack([radius*np.cos(angles),radius*np.sin(angles),np.full(n,half)]),[[0,0,-half],[0,0,half]]])
    f=[]
    for i in range(n):
        j=(i+1)%n
        f.extend([[i,j,j+n],[i,j+n,i+n],[2*n,j,i],[2*n+1,i+n,j+n]])
    return v[f]


def compact_static(parent,meshes):
    before={tag:len(list(parent.iter(tag))) for tag in ['link','visual','collision']}
    for model in [parent]+list(parent.findall('.//model')):
        links=list(model.findall('link'))
        if not links:continue
        groups={};colliders=[]
        for link in links:
            pose=list(map(float,link.findtext('pose','0 0 0 0 0 0').split()))
            offset=np.asarray(pose[:3]);rot=rotation(pose[3:])
            for visual in link.findall('visual'):
                if visual.find('pose') is not None:raise ValueError('Bake visual poses explicitly before batching')
                mat=visual.find('material')
                key=(mat.findtext('ambient'),mat.findtext('diffuse'),visual.findtext('transparency','0'))
                data=triangles(visual.find('geometry'),meshes)@rot.T+offset
                if key not in groups:groups[key]=[deepcopy(mat),[]]
                groups[key][1].append(data)
            for collision in link.findall('collision'):
                if collision.find('pose') is not None:raise ValueError('Unexpected nested collision pose')
                collider=deepcopy(collision);collider.set('name',link.get('name'))
                element(collider,'pose',' '.join(map(str,pose)))
                colliders.append(collider)
            model.remove(link)
        body=element(model,'link',name='body')
        for collider in colliders:body.append(collider)
        for i,(key,(mat,parts)) in enumerate(groups.items()):
            path=meshes/f'batch_{model.get("name")}_{i}.stl'
            tris=np.concatenate(parts)
            vertices=tris.reshape(-1,3);faces=np.arange(len(vertices)).reshape(-1,3)
            write_stl(path,vertices,faces)
            visual=element(body,'visual',name=f'material_{i}')
            element(element(element(visual,'geometry'),'mesh'),'uri',f'model://corda_campus/meshes/{path.name}')
            visual.append(mat)
            if float(key[2]):element(visual,'transparency',key[2])
    after={tag:len(list(parent.iter(tag))) for tag in before}
    return {'before_batching':before,'after_batching':after,'cylinder_visual_segments':16,
            'collisions':'Original analytic/mesh collisions retained; link transforms baked into collider poses'}
