from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash
from db import db

class AdminModel(db.Model):
    __tablename__ = 'Admin'

    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(30), nullable=False, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email_address = Column(String(80), nullable=False, unique=True)
    password = Column(String(128), nullable=False)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)


 