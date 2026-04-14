import math
import logging

# v35.0: Quantum Foresight Engine
# Projecting flight states T+30m to detect operational congestion.

logger = logging.getLogger("AviationSingularity.Foresight")

class ForesightEngine:
    def __init__(self):
        self.projection_minutes = 30
        self.earth_radius_km = 6371.0

    def project_position(self, lat, lon, velocity_kts, track_deg):
        """
        Linear projection of a flight state based on current velocity and heading.
        """
        if lat is None or lon is None or velocity_kts is None or track_deg is None:
            return None

        # Convert knots to km/min
        velocity_km_min = (velocity_kts * 1.852) / 60.0
        distance = velocity_km_min * self.projection_minutes
        
        # Calculate new lat/lon using Great Circle approximation (Small Distance)
        brng = math.radians(track_deg)
        lat1 = math.radians(lat)
        lon1 = math.radians(lon)

        lat2 = math.asin(math.sin(lat1) * math.cos(distance/self.earth_radius_km) +
                         math.cos(lat1) * math.sin(distance/self.earth_radius_km) * math.cos(brng))
        
        lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(distance/self.earth_radius_km) * math.cos(lat1),
                                 math.cos(distance/self.earth_radius_km) - math.sin(lat1) * math.sin(lat2))
        
        return math.degrees(lat2), math.degrees(lon2)

    def generate_congestion_geojson(self, current_fleet):
        """
        Identifies high-density convergence zones T+30.
        Returns GeoJSON FeatureCollection for MapLibre Heatmap.
        """
        features = []
        projected_coords = []

        for flight in current_fleet:
            # We assume current_fleet is a list of dicts from state.df
            res = self.project_position(
                flight.get('lat'), 
                flight.get('lon'), 
                flight.get('velocity'), 
                flight.get('track')
            )
            if res:
                projected_coords.append(res)
                # Add a point for the heatmap
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [res[1], res[0]]},
                    "properties": {"intensity": 1.0}
                })

        # convergence logic: if multiple projected points are near, increase intensity
        # (Simplified for now, MapLibre Heatmap handles this naturally with density)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }

foresight_engine = ForesightEngine()
