from db import db

class FeedbackModel(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.Text, nullable=False)  # Feedback content is required
    email = db.Column(db.String(120), nullable=True)  # Optional email for contact
    phone_number = db.Column(db.String(15), nullable=True)  # Optional phone number
