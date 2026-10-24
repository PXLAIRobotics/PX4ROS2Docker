# Reference configuration map

Read-only source: `/home/tim/Repositories/ROSLyricalDocker`, commit `da098840bada205c0a6187e857d2760dec9c7a16`.

| Reference | PX4 environment treatment |
| --- | --- |
| docker/tmux.conf, vimrc, xfce-terminalrc | Copied unchanged; plugins fetched at pinned commits |
| docker/fonts and font license | Copied unchanged; installed in both images |
| docker/rviz-persistent-settings | Copied unchanged; seeded only if missing |
| docker/start-vnc.sh | Copied desktop process/session setup; independent PX4 command path |
| docker/bashrc, entrypoint | Adapted to Jazzy, PX4 paths, persistent Data, ROS overlays |
| install-stack | Replaced with Noble/Jazzy/Harmonic plus PX4 compiler/agent/QGC dependencies |
| numbered root and image-directory scripts | Same actions and default/c/b convention, independent PX4 names |
| native X11/GPU setup | Shared host-side implementation, Xauthority cleanup, explicit GPU override |
| Commands/bin | PX4/ROS-specific helpers; no global process-kill helpers |
| Projects | Persistent PX4 checkout + ROS message/example workspace |
| ExampleCode | PX4 walkthroughs; no OpenCV, tugbot or old drone-world assets |
| Data | Persistent settings, flight logs, recordings and caches |

No reference repository files are written by the environment scripts or build context.
