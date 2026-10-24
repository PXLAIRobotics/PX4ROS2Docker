#!/usr/bin/env python3
"""Fetch fresh public GRB inputs into a NEW review folder; do not regenerate assets."""
import argparse
import json
from pathlib import Path
import ssl
from urllib.parse import urlencode
from urllib.request import urlopen

from pyproj import Transformer
from shapely.geometry import box, shape
from shapely.ops import transform

SOURCE = Path(__file__).resolve().parent


def get_json(base, params, context=None):
    url = base + '?' + urlencode(params)
    with urlopen(url, context=context, timeout=60) as response:
        data = json.load(response)
    if 'error' in data or data.get('type') == 'ExceptionReport':
        raise RuntimeError(data)
    return data, url


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path,help='New directory to review before replacing snapshots')
    parser.add_argument('--globalsign-intermediate',action='store_true',
                        help='Load the official missing provincial server intermediate, retaining TLS verification')
    args=parser.parse_args()
    args.destination.mkdir(parents=True,exist_ok=False)
    site=json.loads((SOURCE/'site.json').read_text())
    geo=site['origin']
    crs=f'+proj=aeqd +lat_0={geo["latitude"]} +lon_0={geo["longitude"]} +datum=WGS84 +units=m'
    project=Transformer.from_crs('EPSG:4326',crs,always_xy=True)
    data,url=get_json('https://geo.api.vlaanderen.be/GRB/wfs',{
        'service':'WFS','version':'2.0.0','request':'GetFeature','typeNames':'GRB:GBG',
        'srsName':'urn:ogc:def:crs:OGC:1.3:CRS84',
        'bbox':'5.3475,50.9485,5.3575,50.9550,urn:ogc:def:crs:OGC:1.3:CRS84',
        'outputFormat':'application/json','count':1000})
    total = str(data.get('totalFeatures', 'unknown'))
    if len(data['features']) >= 1000 or (total.isdigit() and int(total) > 1000):
        raise RuntimeError('WFS result may be truncated; implement pagination before using it')
    features=[]
    bounds=box(*site['bounds_m'])
    for f in data['features']:
        polygon=transform(project.transform,shape(f['geometry']))
        if polygon.area>=12 and bounds.intersects(polygon): features.append(f)
    data['features']=sorted(features,key=lambda f:f['properties']['OIDN'])
    data.pop('bbox',None);data['numberReturned']=data['totalFeatures']=len(features)
    (args.destination/'buildings.geojson').write_text(json.dumps(data,indent=2)+'\n')
    context=ssl.create_default_context()
    if args.globalsign_intermediate:
        issuer='https://secure.globalsign.com/cacert/gsgccr46ovtlsca2025.crt'
        with urlopen(issuer,timeout=30) as response: certificate=response.read()
        context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(certificate))
    ids=[f['properties']['OIDN'] for f in features]
    heights=[];urls=[url]
    for start in range(0,len(ids),100):
        result,url=get_json('https://geo.limburg.be/arcgis/rest/services/GRB/MapServer/6/query',{
            'f':'json','where':'GRB_OIDN IN ('+','.join(map(str,ids[start:start+100]))+')',
            'outFields':'GRB_OIDN,HN_P99,H_KWAL,DATUM_GRB','returnGeometry':'false',
            'resultRecordCount':3000},context)
        if result.get('exceededTransferLimit'): raise RuntimeError('Height response truncated')
        heights.extend(f['attributes'] for f in result['features']);urls.append(url)
    (args.destination/'heights.json').write_text(json.dumps(sorted(heights,key=lambda f:f['GRB_OIDN']),indent=2)+'\n')
    (args.destination/'requests.json').write_text(json.dumps(urls,indent=2)+'\n')
    print(f'Fetched {len(features)} footprints and {len(heights)} exact-ID heights. Review before replacing checked-in inputs.')


if __name__=='__main__': main()
