from datetime import datetime, timedelta
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import func
from models.E_outtrips import E_OutTripModel
import requests
from dotenv import load_dotenv
import os

blp = Blueprint("E_Outgoing", "E_Outgoing", description="Operations on line E Outgoing trips")

# Helper function to get trip types for today
load_dotenv()
cached_holidays = None

def get_tunisia_holidays():
    global cached_holidays

    if cached_holidays is not None:
        return cached_holidays  
    API_KEY = os.getenv("API_KEY")
    COUNTRY = "TN"  
    YEAR = datetime.now().year  

    url = f"https://calendarific.com/api/v2/holidays?api_key={API_KEY}&country={COUNTRY}&year={YEAR}"
    
    try:
        response = requests.get(url)
        data = response.json()

        if "response" in data and "holidays" in data["response"]:
            holidays = [holiday["date"]["datetime"] for holiday in data["response"]["holidays"]]
            cached_holidays = {f"{h['day']:02d}-{h['month']:02d}" for h in holidays}  
            return cached_holidays
    except Exception as e:
        print(f"Error fetching holidays: {e}")
        
    return set() 

def get_trip_types_for_specific_day(day):
    """Determines trip types for a given day."""
    if not isinstance(day, datetime):  
        raise ValueError("Expected a datetime object")

    weekday = day.weekday()  # Monday is 0, Sunday is 6
    day_date = day.strftime('%d-%m')

    # Fetch Tunisia's holidays
    holidays = get_tunisia_holidays()

    # Determine trip types based on the day
    if day_date in holidays:
        return ['C', 'B']  # Holidays: C and B trips
    elif weekday == 6:  # Sunday
        return ['C', 'B']  # Sunday: C and B trips
    else:
        return ['C', 'A']  # Weekday: C and A trips
def get_trip_types_for_tomorrow():
    tomorrow = datetime.now() + timedelta(days=1)
    weekday = tomorrow.weekday()  # Monday is 0, Sunday is 6
    tomorrow_date = tomorrow.strftime('%d-%m')

    # Fetch Tunisia's holidays
    holidays = get_tunisia_holidays()

    # Determine trip types based on the day
    if tomorrow_date in holidays:
        return ['C', 'B']  # Holidays: C and B trips
    elif weekday == 6:  # Sunday
        return ['C', 'B']  # Sunday: C and B trips
    else:
        return ['C', 'A']  # Weekday: C and A trip
station_id_to_column_map = {
    0: "Tunis",
    1: "Sayda_ElManoubia",
    2: "Ennajah",
    3: "Etayrane",
    4: "Ezzouhour_2",
    5: "ElHrayria",
    6: "Bougatfa",
}

@blp.route("/<int:station_id>/E_outtrips/next_1_hour")
class NextHourTrips(MethodView):
    def get(self, station_id):
        # Validate station ID
        if station_id not in station_id_to_column_map:
            abort(400, message="Invalid station ID provided.")

        # Get the station name for the given station ID
        station_name = station_id_to_column_map[station_id]

        # Get the current time and 1 hour later
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        one_hour_later = (now + timedelta(hours=1)).strftime("%H:%M:%S")

        # Determine trip types for today
        trip_types = get_trip_types_for_specific_day(now)  

        # Query trips based on the current station's column, time range, and trip type
        trips = E_OutTripModel.query.filter(
            E_OutTripModel.TripType.in_(trip_types),
            func.strftime('%H:%M:%S', getattr(E_OutTripModel, station_name)) >= current_time,
            func.strftime('%H:%M:%S', getattr(E_OutTripModel, station_name)) <= one_hour_later
        ).all()

        # If no trips are found, return a 200 OK response with a message
        if not trips:
            return {
                "message": f"No trips scheduled in the next hour for {station_name}."
            }, 200

        # Dynamically exclude earlier station columns
        excluded_columns = [
            column_name
            for idx, column_name in station_id_to_column_map.items()
            if idx < station_id
        ]

        # Filter out unnecessary columns from the result
        def filter_columns(trip_dict):
            return {k: v for k, v in trip_dict.items() if k not in excluded_columns}

        # Return the filtered trips as a list of dictionaries along with a message
        return {
            "message": f"There are {len(trips)} trips scheduled in the next hour at {station_name} station.",
            "trips": [filter_columns(trip.to_dict()) for trip in trips]
        }



@blp.route("/<int:station_id>/E_outtrips/rest_of_day")
class TodayTrips(MethodView):
    def get(self, station_id):
        # Validate station ID
        if station_id not in station_id_to_column_map:
            abort(400, message="Invalid station ID provided.")

        # Get the station name for the given station ID
        station_name = station_id_to_column_map[station_id]

        # Get today's trip types using the correct function
        trip_types = get_trip_types_for_specific_day(datetime.now())  

        # Get the current time
        current_time = datetime.now().strftime('%H:%M:%S')

        # Query trips for today for the specified station and trips yet to occur
        trips = E_OutTripModel.query.filter(
            E_OutTripModel.TripType.in_(trip_types),
            func.strftime('%H:%M:%S', getattr(E_OutTripModel, station_name)) >= current_time
        ).all()

        # Check if there are trips for the rest of today
        if not trips:
            # Return a 200 OK response with a message indicating no trips for the station
            return {
                "message": f"No trips scheduled for the rest of today for station {station_name}."
            }, 200

        # Dynamically exclude earlier station columns
        excluded_columns = [
            column_name
            for idx, column_name in station_id_to_column_map.items()
            if idx < station_id
        ]

        # Filter out unnecessary columns from the result
        def filter_columns(trip_dict):
            return {k: v for k, v in trip_dict.items() if k not in excluded_columns}

        # Return the filtered trips along with a message
        return {
            "message": f"There are {len(trips)} trips scheduled for the rest of today at {station_name} station.",
            "trips": [filter_columns(trip.to_dict()) for trip in trips]
        }



@blp.route("/<int:station_id>/E_outtrips/next_day")
class NextDayTrips(MethodView):
    def get(self, station_id):
        # Validate station ID
        if station_id not in station_id_to_column_map:
            abort(400, message="Invalid station ID provided.")

        # Get the station name for the given station ID
        station_name = station_id_to_column_map[station_id]

        # Calculate next day's date
        next_day = datetime.now() + timedelta(days=1)
        next_day_date = next_day.strftime('%Y-%m-%d')
        next_day_name = next_day.strftime('%A')  

        
        trip_types = get_trip_types_for_tomorrow()  

        # Query trips for the next day for the specified station
        trips = E_OutTripModel.query.filter(
            E_OutTripModel.TripType.in_(trip_types)
        ).all()

        # Check if there are trips for the next day
        if not trips:
            return {
                "message": f"No trips found for {station_name} on {next_day_name} ({next_day_date})."
            }, 200

        # Dynamically exclude earlier station columns
        excluded_columns = [
            column_name
            for idx, column_name in station_id_to_column_map.items()
            if idx < station_id
        ]

        # Filter out unnecessary columns from the result
        def filter_columns(trip_dict):
            return {k: v for k, v in trip_dict.items() if k not in excluded_columns}

        # Return the filtered trips
        return {
            "date": next_day_date,
            "day": next_day_name,
            "trips": [filter_columns(trip.to_dict()) for trip in trips]
        }
