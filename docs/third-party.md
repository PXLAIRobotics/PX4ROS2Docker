# Third-party materials

- `docker/tmux.conf`, `docker/vimrc`, `docker/xfce-terminalrc`, `docker/rviz-persistent-settings`, and fonts were copied from ROSLyricalDocker commit da098840bada205c0a6187e857d2760dec9c7a16. Reference MIT attribution is retained in LICENSE; fonts include their original license.
- `docker/start-vnc.sh` adapts the reference project's desktop startup. Other shell helpers follow its workflow.
- `docker/px4-requirements.txt` comes from PX4/PX4-Autopilot v1.17.0 Tools/setup/requirements.txt. PX4 uses BSD-3-Clause; see the license in the pinned upstream checkout.
- PX4-Autopilot and px4_msgs are independently downloaded upstream repositories; preserve their licenses when redistributing modified sources or images.
- Micro XRCE-DDS Agent and its eProsima dependencies retain their Apache-2.0 and other bundled notices.
- QGroundControl is downloaded from an official stable release and extracted without changing its resources. Its upstream licensing includes Apache-2.0/GPL-3.0 options and bundled dependency notices; consult the exact release before redistribution.
- Vim/tmux plugins are pinned in docker/plugins.lock and retain each upstream repository's license. The image keeps plugin source/license files.
- Ubuntu, ROS 2 and Gazebo packages carry their respective licenses and package notices inside the image.

- Campus footprints and derived building meshes use GRB open data. Attribution: **Bron: Grootschalig Referentie Bestand Vlaanderen, Digitaal Vlaanderen**. Height attributes are distributed by the province of Limburg. See `tools/campus/SOURCES.md` and the model's installed `ATTRIBUTION.md`; the environment MIT licence does not replace their source-data terms.
- `tools/campus/gui.config.in` adapts Gazebo Sim 8's standard GUI configuration under Apache-2.0. Its licence is included in `tools/campus/Gazebo-GUI-LICENSE` and installed beside the runtime assets.

- Parking outlines were manually traced from Digitaal Vlaanderen winter orthophotography and checked against the campus mobility map. Attribution: **Bron: Digitaal Vlaanderen, Orthofotomozaïek, middenschalig, winteropnamen, kleur, meest recent**. Campus images guide approximate landmark geometry and are not redistributed or used as textures.
