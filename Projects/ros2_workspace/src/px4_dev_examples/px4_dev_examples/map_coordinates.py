"""WGS84-to-world ENU for the campus overview, without a runtime GIS dependency."""
import math


def geodetic_to_enu(latitude, longitude, origin_latitude, origin_longitude):
    """Ellipsoidal ECEF tangent projection at zero height.

    At campus distances this agrees with the generator's WGS84 AEQD plane
    within centimetres; ignores altitude to keep the map position on the ground.
    """
    values = (latitude, longitude, origin_latitude, origin_longitude)
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Non-finite geographic coordinate')
    def ecef(lat, lon):
        lat, lon = math.radians(lat), math.radians(lon)
        eccentricity_squared = 6.6943799901413165e-3
        n = 6378137.0/math.sqrt(1-eccentricity_squared*math.sin(lat)**2)
        return (n*math.cos(lat)*math.cos(lon), n*math.cos(lat)*math.sin(lon),
                n*(1-eccentricity_squared)*math.sin(lat))
    a, b = ecef(latitude, longitude), ecef(origin_latitude, origin_longitude)
    dx, dy, dz = (a[i]-b[i] for i in range(3))
    lat, lon = math.radians(origin_latitude), math.radians(origin_longitude)
    return (-math.sin(lon)*dx + math.cos(lon)*dy,
            -math.sin(lat)*math.cos(lon)*dx-math.sin(lat)*math.sin(lon)*dy+math.cos(lat)*dz)
