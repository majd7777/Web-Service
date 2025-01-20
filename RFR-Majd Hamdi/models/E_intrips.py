from db import db
from collections import OrderedDict


class E_InTripModel(db.Model):
    __tablename__ = 'E_intrips'
    
    # Table columns
    TripNumber = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TripType = db.Column(db.String, nullable=False)
    N_Train = db.Column(db.Integer, unique=True, nullable=False)
    Bougatfa = db.Column(db.Time, unique=True, nullable=False)
    ElHrayria = db.Column(db.Time, unique=True, nullable=False)
    Ezzouhour_2 = db.Column(db.Time, unique=True, nullable=False)
    Etayrane = db.Column(db.Time, unique=True, nullable=False)
    Ennajah = db.Column(db.Time, unique=True, nullable=False)
    Sayda_ElManoubia = db.Column(db.Time, unique=True, nullable=False)
    Tunis = db.Column(db.Time, unique=True, nullable=False)

    __table_args__ = {'extend_existing': True}  


    def to_dict(self):
        return OrderedDict([
            ("TripNumber", self.TripNumber),
            ("TripType", self.TripType),
            ("N_Train", self.N_Train),
            ("Bougatfa", self.Bougatfa.strftime("%H:%M:%S") if self.Bougatfa else None),
            ("ElHrayria", self.ElHrayria.strftime("%H:%M:%S") if self.ElHrayria else None),
            ("Ezzouhour_2", self.Ezzouhour_2.strftime("%H:%M:%S") if self.Ezzouhour_2 else None),
            ("Etayrane", self.Etayrane.strftime("%H:%M:%S") if self.Etayrane else None),
            ("Ennajah", self.Ennajah.strftime("%H:%M:%S") if self.Ennajah else None),
            ("Sayda_ElManoubia", self.Sayda_ElManoubia.strftime("%H:%M:%S") if self.Sayda_ElManoubia else None),
            ("Tunis", self.Tunis.strftime("%H:%M:%S") if self.Tunis else None)  
        ])

