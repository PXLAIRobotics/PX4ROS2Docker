# Current cockpit screenshots

Captured on 26 October 2026 from the cockpit in the `px4-uav-cockpit` Docker volume, running with the repository at revision `915d995291ef390bcff5fa3808ecc15a52821d98`.

- `cockpit.png`: real PyQt5 window capture with fresh PX4 telemetry, more than ten received RGB frames, preflight readiness and a disarmed vehicle on the Corda 1 rooftop deck. No flight command was sent.
- `cockpit-campus-map.png`: the same live map widget captured at 800 × 620 for readable geometry. The marker uses live global telemetry. Map features load from the installed `px4_dev_examples/simulation/campus-map.json`.

The capture used Qt widget grabs in the container's X11 desktop. No synthetic telemetry or image editing was used. The image resolution in the cockpit is the sensor's configured 320 × 240, scaled by the application.

Campus geometry is an approximation, not a survey or flight-planning map. Bron: Grootschalig Referentie Bestand Vlaanderen, Digitaal Vlaanderen. See [campus sources and attribution](../../tools/campus/SOURCES.md). Older tutorial images and their capture context are listed [separately](../tutorial/images/README.md).

Additional captures from the same environment on 26 October 2026:

- `gazebo-campus.png`: live Gazebo GUI overview of Corda Campus.
- `gazebo-drone.png`: live Gazebo GUI close-up of the disarmed sensor-equipped x500 on the rooftop deck.
- `qgroundcontrol.png`: connected QGC with Ready / Hold, rooftop vehicle marker and satellite map; map imagery retains the provider’s on-screen presentation.

The cockpit screenshots were refreshed after adding Corda 7’s map callouts: PXL Digital at the lower-left corner and PXL Smart ICT at the lower-right corner of the southern wing, on the north-up map. Building identification was checked against the [official Corda visitor map](https://www.cordacampus.com/wp-content/uploads/2023/11/Visitor-Map_2K.png); these educational callout positions follow the instructor’s placement request. No Gazebo building geometry was changed. Cockpit source remains external to Git.
