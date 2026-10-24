# Corda Campus world: sources, attribution and approximations

Generated on 2026-10-24. This is a lightweight simulation reconstruction, not a survey or a flight-planning map. Local axes are metres East/North/Up. The world origin is 50.951737 N, 5.352412 E; flat ground is assumed to be 50 m AMSL, preserving the earlier environment origin. This is not a validated conversion of Belgian TAW heights to WGS84 ellipsoid height.

## Data and attribution

**Bron: Grootschalig Referentie Bestand Vlaanderen, Digitaal Vlaanderen.** Retain this attribution with the source snapshots and generated building geometry. The environment's MIT licence does not replace the source-data attribution requirements.

- Current building polygons: [GRB](https://www.vlaanderen.be/digitaal-vlaanderen/onze-diensten-en-platformen/basiskaart-vlaanderen-grb), official WFS `https://geo.api.vlaanderen.be/GRB/wfs`, feature type `GRB:GBG`. `data/buildings.geojson` is the 82-building subset selected from the bounding box 5.3475,50.9485,5.3575,50.9550 (longitude/latitude, CRS84), then filtered to footprints >=12 m² intersecting the local rectangle [-320,-160,330,360] m. Boundary buildings are kept whole. Source version dates and stable OIDN identifiers remain in the snapshot.
- Building heights: [3D GRB](https://www.vlaanderen.be/digitaal-vlaanderen/onze-diensten-en-platformen/basiskaart-vlaanderen-grb/3d-grb), distributed by the provincial [GRB service, layer 6](https://geo.limburg.be/arcgis/rest/services/GRB/MapServer/6). `data/heights.json` retains only height attributes linked by **exact GRB OIDN**, with HN_P99, H_KWAL and source dates. HN_P99 is a relative building-height estimate, not an absolute terrain elevation. The old height dataset misses newer buildings. In the downloaded provincial layer, same-ID polygons had a systematic positional difference from current GRB; its geometry is deliberately not used or shifted into the world. No spatial-overlap height transfer is performed.
- Corda 1 identification and visual roof direction: official [campus visitor map](https://www.cordacampus.com/wp-content/uploads/2023/11/Visitor-Map_2K.png) and [Corda 1 photograph](https://www.cordacampus.com/wp-content/uploads/2021/01/Corda-building-1.jpg). These images were consulted as references, and are not bundled in the runtime assets.
- Corda 1 maximum height and sloped form: project architect [eld](https://eld.be/projects/corda-campus/) states seven floors and a maximum height of 30 m. The model uses that maximum, with an **approximated** planar roof falling to a 4 m low edge along its footprint's long axis. This is not roof survey/BIM geometry. The companion bar wedge and Corda 2/3/4 heights are visual estimates, explicitly listed in `site.json`.
- Corda 2 and 3 sloping forms: architect [eld describes phases 2/3](https://www.eld.be/next-phases-corda-campus/) as volumes similar to Corda 1; the official visitor map shows the falling roofs. Both are modelled as long-axis wedges, high at the southern end, with **estimated** 18 m high and 4 m low edges. These dimensions and roof angles are visual approximations, not measured heights.
- Corda Arena maximum height: campus [Masterplan 2.0 brochure](https://www.cordacampus.com/wp-content/uploads/2022/04/Masterplan-2.0-brochure-en.pdf), 24 m. Current GRB provides its footprint. Interior and detailed roof structures are omitted.
- GUI layout: based on `gui/gui.config` from [Gazebo Sim 8](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/gui/gui.config), Apache-2.0. `gui.config.in` changes the initial camera, disables the quick-start dialog, and starts unpaused. Gazebo retains its upstream licence; see https://www.apache.org/licenses/LICENSE-2.0.

## Geometry and height rules

The offline generator preserves concave outlines and courtyards, simplifies edges by at most 0.12 m and produces watertight triangle meshes with matching collision and visual geometry. Curved outlines remain polygonal approximations, not bounding boxes. Roof sections are mostly flat; Corda 1, its companion, Corda 2 and Corda 3 are wedges. Corda 1/2/3 use separate green roof surfaces and approximate facade colours (blue-grey glass, light cladding, warm grey brick respectively), based on the visitor map. Colours are simplified solid materials; facade patterns and glazing details are omitted. Detailed facades, windows, balconies, trees, vehicles, roads, terrain detail and interiors are not reconstructed.

Heights come from an explicit architectural override, then an exact-ID positive HN_P99, then an estimate (6 m for footprints <250 m²; otherwise 12 m). Every generated building's height source is listed in `simulation/campus.json`. The mesh has one height per footprint except the four wedge roofs; buildings with real stepped roofs may need future manually authored subdivisions.

The earlier approximate GPS point is on open ground east of Corda 1. The generated launch is **on the actual Corda 1 footprint**: local (-85,-38) m, approximately 50.9513954 N, 5.3512024 E. A **synthetic 4×4 m level launch platform** sits just above the sloping roof, with an H marking and visual supports. This is a simulation aid, not a claim of a real helipad. Generated roof/platform/spawn elevations are in `simulation/campus.json`; the drone should settle on the platform, around 23.8 m above the assumed campus ground.

## Regeneration

Runtime simulation uses the checked-in meshes; it needs no GIS libraries or internet. Changes to outlines/heights require regenerating assets and rebuilding the ROS package. `site.json`, the filtered snapshots and `gui.config.in` are authoritative inputs. The generated report records input hashes and provenance.

Run the generator in Docker with an isolated GIS venv (does not replace the ROS Python environment):

```bash
# Inside the development container, with this repository mounted at /work:
python3 -m venv --system-site-packages /tmp/campus-gis
/tmp/campus-gis/bin/pip install -r /work/tools/campus/requirements.txt
/tmp/campus-gis/bin/python /work/tools/campus/generate.py
build_ros2_workspace --packages-select px4_dev_examples
```

For a source-data refresh, use `fetch.py` in the same venv. It downloads to a separate destination for review, never overwrites the checked-in snapshot automatically. Keep older snapshots until geometry, building IDs, data provenance and the launch roof have been revalidated. The provincial server currently omits an intermediate certificate; the fetcher can load the official GlobalSign intermediate into a request-local trust context, leaving normal TLS verification enabled.
