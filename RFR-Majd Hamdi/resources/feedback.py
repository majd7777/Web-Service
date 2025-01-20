from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from db import db
from models.feedback import FeedbackModel
from schemas import FeedbackSchema

# Define the Blueprint
blp = Blueprint("Feedback", "feedback", description="Operations on feedback")

@blp.route("/feedback")
class Feedback(MethodView):
    @blp.arguments(FeedbackSchema)
    @blp.response(201)
    def post(self, feedback_data):
        """Add new feedback to the database."""
        feedback = FeedbackModel(**feedback_data)
        try:
            db.session.add(feedback)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message="An error occurred while saving the feedback.")
        return {"message": "Your feedback was sent successfully."}, 201