from flask.views import MethodView
from flask_smorest import Blueprint
from models.stations_locations import StationLocationModel
from schemas import StationWithLinkOutputSchema
from math import radians, sin, cos, sqrt, atan2
from db import db
from flask import jsonify, request
import requests
from dotenv import load_dotenv
import os

load_dotenv()



blp = Blueprint("StationLocations", "stationlocations", description="Operations on station locations")
#locations for E stations
@blp.route("/E/stations")
class LineEStations(MethodView):
    @blp.response(200, StationWithLinkOutputSchema)
    def get(self):
        stations = StationLocationModel.query.filter_by(line="E").all()

        if not stations:
            return {"message": "No stations found for Line E.", "stations": []}, 404

        # Transform station data to include Google Maps links
        stations_with_links = [
            {
                "station_name": station.station_name,
                "google_maps_link": f"https://www.google.com/maps?q={station.latitude},{station.longitude}"
            }
            for station in stations
        ]

        return {
            "message": f"These are the {len(stations)} stations in Line E and their locations.",
            "stations": stations_with_links
        }

#locations for D stations
@blp.route("/D/stations")
class LineDStations(MethodView):
    @blp.response(200, StationWithLinkOutputSchema)
    def get(self):
        stations = StationLocationModel.query.filter_by(line="D").all()

        if not stations:
            return {"message": "No stations found for Line D.", "stations": []}, 404

        # Transform station data to include Google Maps links
        stations_with_links = [
            {
                "station_name": station.station_name,
                "google_maps_link": f"https://www.google.com/maps?q={station.latitude},{station.longitude}"
            }
            for station in stations
        ]

        return {
            "message": f"These are the {len(stations)} stations in Line D and their locations.",
            "stations": stations_with_links
        }
    
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
def get_location_by_ip(ip):
    # Use Google's Geolocation API to get approximate location
    url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_MAPS_API_KEY}"
    payload = {"considerIp": True}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json()}
@blp.route('/get-location', methods=['GET'])
def get_location():
    # Get the user's IP address 
    client_ip = request.remote_addr or "8.8.8.8"  
    location_data = get_location_by_ip(client_ip)

    if "error" in location_data:
        return jsonify({"message": "Failed to retrieve location", "error": location_data["error"]}), 400

    return jsonify(location_data), 200

#a function to calculate distance between 2 coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two lat/lon points in kilometers using Haversine formula."""
    # The radius of the Earth in kilometers
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Differences in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    # Distance in kilometers
    distance = R * c
    return distance
#just for testing
@blp.route("/nearest_station", methods=["GET"])
def get_nearest_station():
    
    
    # Your fixed coordinates
    user_lat = 36.675561
    user_lon = 10.153520

    # Fetch all station locations from the database
    stations = StationLocationModel.query.all()

    # Initialize variables to track the nearest stations for lines D, E, and A
    nearest_d_station = None
    nearest_e_station = None
    nearest_a_station = None
    min_d_distance = float('inf')
    min_e_distance = float('inf')
    min_a_distance = float('inf')

    for station in stations:
        # Calculate the distance from the user's location to the station
        distance = calculate_distance(user_lat, user_lon, station.latitude, station.longitude)
        
        if station.line == "D" and distance < min_d_distance:
            nearest_d_station = station
            min_d_distance = distance
        elif station.line == "E" and distance < min_e_distance:
            nearest_e_station = station
            min_e_distance = distance
        elif station.line == "A" and distance < min_a_distance:
            nearest_a_station = station
            min_a_distance = distance

    messages = []

    if nearest_d_station:
        d_location = {
            "latitude": nearest_d_station.latitude,
            "longitude": nearest_d_station.longitude
        }
        d_google_maps_url = f"https://www.google.com/maps?q={d_location['latitude']},{d_location['longitude']}&z=15&output=embed"
        messages.append({
            "line": "D",
            "station": nearest_d_station.station_name,
            "message": f"The closest station in line D to you is: {nearest_d_station.station_name}. See it on Google Maps: {d_google_maps_url}"
        })
    else:
        messages.append({"line": "D", "message": "No station found for line D."})

    if nearest_e_station:
        e_location = {
            "latitude": nearest_e_station.latitude,
            "longitude": nearest_e_station.longitude
        }
        e_google_maps_url = f"https://www.google.com/maps?q={e_location['latitude']},{e_location['longitude']}&z=15&output=embed"
        messages.append({
            "line": "E",
            "station": nearest_e_station.station_name,
            "message": f"The closest station in line E to you is: {nearest_e_station.station_name}. See it on Google Maps: {e_google_maps_url}"
        })
    else:
        messages.append({"line": "E", "message": "No station found for line E."})

    fixed_lat = 36.7695138
    fixed_lon = 10.2233826
    a_station_name = "A Station"  
    a_google_maps_url = f"https://www.google.com/maps?q={fixed_lat},{fixed_lon}&z=15&output=embed"
    messages.append({
        "line": "A",
        "station": a_station_name,
        "message": f"The closest location in A station to you is Megrine: {a_station_name}. See it on Google Maps: {a_google_maps_url}"
    })

    return jsonify({"messages": messages}), 200

