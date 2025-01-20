from db import db

class StationLocationModel(db.Model):
    __tablename__ = "station_locations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_name = db.Column(db.String(80), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    line = db.Column(db.String(10), nullable=False)


