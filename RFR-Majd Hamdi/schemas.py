from marshmallow import Schema, fields
from marshmallow.validate import Range
from marshmallow import ValidationError
from datetime import datetime




class AnnouncementSchema(Schema):
    message = fields.String(required=True)

class AddETripSchema(Schema):
    TripType = fields.String(required=True, description="Type of trip (e.g., 'C', 'A', 'B')")
    N_Train = fields.Integer(required=True, description="Train number")
    Bougatfa = fields.String(required=False, description="Time at Bougatfa station (format: HH:MM:SS)")
    ElHrayria = fields.String(required=False, description="Time at ElHrayria station (format: HH:MM:SS)")
    Ezzouhour_2 = fields.String(required=False, description="Time at Ezzouhour_2 station (format: HH:MM:SS)")
    Etayrane = fields.String(required=False, description="Time at Etayrane station (format: HH:MM:SS)")
    Ennajah = fields.String(required=False, description="Time at Ennajah station (format: HH:MM:SS)")
    Sayda_ElManoubia = fields.String(required=False, description="Time at Sayda_ElManoubia station (format: HH:MM:SS)")
    Tunis = fields.String(required=False, description="Time at Tunis station (format: HH:MM:SS)")

class DLineInfoResponseSchema(Schema):
    message = fields.Str()

class E_OutTripSchema(Schema):
    TripNumber = fields.Int(dump_only=True)
    TripType = fields.Str(required=True)
    N_Train = fields.Int(required=True, validate=Range(min=1))

    # Custom serialization for time fields
    Tunis = fields.Method("format_time", deserialize="parse_time")
    Sayda_ElManoubia = fields.Method("format_time", deserialize="parse_time")
    Ennajah = fields.Method("format_time", deserialize="parse_time")
    Etayrane = fields.Method("format_time", deserialize="parse_time")
    Ezzouhour_2 = fields.Method("format_time", deserialize="parse_time")
    ElHrayria = fields.Method("format_time", deserialize="parse_time")
    Bougatfa = fields.Method("format_time", deserialize="parse_time")

    def format_time(self, obj):
        return obj.strftime("%H:%M") if obj else None

    def parse_time(self, value):
        try:
            return datetime.strptime(value, "%H:%M").time()
        except ValueError:
            raise ValidationError("Invalid time format. Expected HH:MM.")

class E_InTripSchema(Schema):
    TripNumber = fields.Int(dump_only=True)
    TripType = fields.Str(required=True)
    N_Train = fields.Int(required=True, validate=Range(min=1))
    Bougatfa = fields.Time(required=True, format="%H:%M")
    ElHrayria = fields.Time(required=True, format="%H:%M")
    Ezzouhour_2 = fields.Time(required=True, format="%H:%M")
    Etayrane = fields.Time(required=True, format="%H:%M")
    Ennajah = fields.Time(required=True, format="%H:%M")
    Sayda_ElManoubia = fields.Time(required=True, format="%H:%M")
    Tunis = fields.Time(required=True, format="%H:%M")

class FeedbackSchema(Schema):
    id = fields.Int(dump_only=True)
    feedback = fields.Str(required=True)  # Feedback is required
    email = fields.Email(required=False)  # Optional email field
    phone_number = fields.Str(required=False)  # Optional phone number

class StationWithLinkOutputSchema(Schema):
    message = fields.Str(required=True)
    stations = fields.List(fields.Dict(keys=fields.Str(), values=fields.Str()))

class AdminSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Str(required=True)
    password = fields.Str(load_only=True, required=True)

class FeedbackSchema(Schema):
    id = fields.Int(dump_only=True)
    feedback = fields.Str(required=True)
    email = fields.Str()
    phone_number = fields.Str()
