from flask import request, current_app, jsonify
import jwt
from schemas import FeedbackSchema,AddETripSchema,AnnouncementSchema
from werkzeug.security import check_password_hash,generate_password_hash
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import AdminModel, E_InTripModel, E_OutTripModel,FeedbackModel
from db import db
from datetime import datetime, timedelta
from functools import wraps
import re
from flask_jwt_extended import create_access_token,get_jwt_identity ,jwt_required,get_jwt
from blocklist import add_to_blocklist, is_token_blocked
import requests



blp = Blueprint("Admin", "admin", description="Operations related to Admin")

# Login Endpoint
@blp.route("/login", methods=["POST"])
class AdminLogin(MethodView):
    def post(self):
        
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify(message="Username and password required"), 400

        username = auth.username
        password = auth.password

        # Find the admin in the database
        admin = AdminModel.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            # Create JWT token
            token = create_access_token(identity=str(admin.admin_id))

            # Include a welcome message with the admin's full name
            welcome_message = f"Welcome {admin.first_name} {admin.last_name}"

            return jsonify(access_token=token, message=welcome_message), 200

        return jsonify(message="Invalid credentials"), 401

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Token required function triggered!")  
        
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Login is required to use such functions"}), 401

        try:
            token = token.split()[1]  # The token is passed as 'Bearer <token>'
            decoded_token = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            jti = decoded_token["jti"]  # Get the JWT ID (jti)
            request.admin_id = decoded_token["admin_id"]
            
            # Debugging line
            print(f"Checking if token with jti {jti} is blocked...")

            # Check if the token is in the blocklist
            if is_token_blocked(jti):
                print(f"Token with jti {jti} is blocked.")  # Debugging line
                return jsonify({"message": "Please login first."}), 401  # Token is blocked, so request is denied
            else:
                print(f"Token with jti {jti} is NOT blocked.")  # Debugging line

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated_function

#adding a trip to line E schedules
@blp.route("/admin/E/<string:trip_type>/add_trip", methods=["POST"])
class AddETrip(MethodView):

    @jwt_required()
    @blp.arguments(AddETripSchema)
    def post(self, trip_data, trip_type):
        if trip_type not in ['in', 'out']:
            abort(400, message="Invalid trip type. Use 'in' or 'out'.")

        # Choose the correct model
        model = E_InTripModel if trip_type == 'in' else E_OutTripModel

        # Convert string times to datetime.time objects
        def parse_time(time_str):
            return datetime.strptime(time_str, "%H:%M:%S").time() if time_str else None

        # Check if the times already exist in the database
        def check_duplicate_time(time_value, column_name):
            if time_value:
                existing_trip = model.query.filter(getattr(model, column_name) == time_value).first()
                if existing_trip:
                    return f"A trip is already scheduled at {time_value} in {column_name} station."
            return None

        # List of time columns to check
        time_columns = [
            ("Bougatfa", trip_data.get("Bougatfa")),
            ("ElHrayria", trip_data.get("ElHrayria")),
            ("Ezzouhour_2", trip_data.get("Ezzouhour_2")),
            ("Etayrane", trip_data.get("Etayrane")),
            ("Ennajah", trip_data.get("Ennajah")),
            ("Sayda_ElManoubia", trip_data.get("Sayda_ElManoubia")),
            ("Tunis", trip_data.get("Tunis"))
        ]
        
        # Check each time field for duplicates
        duplicate_messages = [
            check_duplicate_time(parse_time(time_str), column_name)
            for column_name, time_str in time_columns if time_str
        ]
        duplicate_messages = [msg for msg in duplicate_messages if msg]  # Filter out None values

        # Return error if any duplicate times exist
        if duplicate_messages:
            return {"message": duplicate_messages}, 400

        # Create a new entry
        new_entry = model(
            TripType=trip_data["TripType"],
            N_Train=trip_data["N_Train"],
            Bougatfa=parse_time(trip_data.get("Bougatfa")),
            ElHrayria=parse_time(trip_data.get("ElHrayria")),
            Ezzouhour_2=parse_time(trip_data.get("Ezzouhour_2")),
            Etayrane=parse_time(trip_data.get("Etayrane")),
            Ennajah=parse_time(trip_data.get("Ennajah")),
            Sayda_ElManoubia=parse_time(trip_data.get("Sayda_ElManoubia")),
            Tunis=parse_time(trip_data.get("Tunis"))
        )

        db.session.add(new_entry)
        db.session.commit()

        return jsonify(new_entry.to_dict()), 201

#Deleting a trip from line E schedules by id (aka TripNumber)
@blp.route("/admin/E/<string:trip_type>/delete_trip/<int:trip_id>", methods=["DELETE"])
class DeleteETrip(MethodView):
    @jwt_required()
    def delete(self, trip_type, trip_id):
        # Determine which table to use based on the trip_type ('in' or 'out')
        if trip_type not in ['in', 'out']:
            abort(400, message="Invalid trip type. Use 'in' or 'out'.")

        # Choose the model based on trip_type
        model = E_InTripModel if trip_type == 'in' else E_OutTripModel

        # Attempt to find the trip in the selected model
        trip_to_delete = model.query.get(trip_id)

        # If no trip is found, return a 404 error
        if not trip_to_delete:
            return {"message": f"Trip with id {trip_id} not found in {trip_type} trips."}, 404

        # Delete the trip
        db.session.delete(trip_to_delete)
        db.session.commit()

        # Return a success message
        return {"message": f"Trip with id {trip_id} successfully deleted from {trip_type} trips."}, 200

#Update a trip in Line E.
@blp.route("/admin/E/<string:trip_type>/update_trip/<int:trip_number>", methods=["PUT"])
class UpdateETrip(MethodView):
    @jwt_required()
    def put(self, trip_type, trip_number):
        # Validate the incoming data
        data = request.get_json()

        # Ensure necessary fields are present
        if not data.get("TripType") or not data.get("N_Train"):
            abort(400, message="Missing required fields: TripType or N_Train")

        # Determine which table to use based on the trip_type ('in' or 'out')
        if trip_type not in ['in', 'out']:
            abort(400, message="Invalid trip type. Use 'in' or 'out'.")

        # Choose the model based on trip_type
        model = E_InTripModel if trip_type == 'in' else E_OutTripModel

        # Find the trip by TripNumber
        trip_to_update = model.query.filter_by(TripNumber=trip_number).first()

        # If no trip is found, return a 404 error
        if not trip_to_update:
            return {"message": f"Trip with TripNumber {trip_number} not found in {trip_type}-trips."}, 404

        # Update the trip's data
        trip_to_update.TripType = data["TripType"]
        trip_to_update.N_Train = data["N_Train"]
        trip_to_update.Bougatfa = datetime.strptime(data.get("Bougatfa", ""), "%H:%M:%S").time() if data.get("Bougatfa") else trip_to_update.Bougatfa
        trip_to_update.ElHrayria = datetime.strptime(data.get("ElHrayria", ""), "%H:%M:%S").time() if data.get("ElHrayria") else trip_to_update.ElHrayria
        trip_to_update.Ezzouhour_2 = datetime.strptime(data.get("Ezzouhour_2", ""), "%H:%M:%S").time() if data.get("Ezzouhour_2") else trip_to_update.Ezzouhour_2
        trip_to_update.Etayrane = datetime.strptime(data.get("Etayrane", ""), "%H:%M:%S").time() if data.get("Etayrane") else trip_to_update.Etayrane
        trip_to_update.Ennajah = datetime.strptime(data.get("Ennajah", ""), "%H:%M:%S").time() if data.get("Ennajah") else trip_to_update.Ennajah
        trip_to_update.Sayda_ElManoubia = datetime.strptime(data.get("Sayda_ElManoubia", ""), "%H:%M:%S").time() if data.get("Sayda_ElManoubia") else trip_to_update.Sayda_ElManoubia
        trip_to_update.Tunis = datetime.strptime(data.get("Tunis", ""), "%H:%M:%S").time() if data.get("Tunis") else trip_to_update.Tunis

        # Commit the changes to the database
        db.session.commit()

        return {"message": f"TripNumber {trip_number} successfully updated in {trip_type}-trips.", "data": trip_to_update.to_dict()}, 200


announcement_message = None  # Store the announcement in-memory (no database)

@blp.route("/admin/announcement")
class Announcement(MethodView):
    @jwt_required()  # Ensure that the user is logged in
    def post(self):
        """Post a new announcement"""
        data = request.get_json()
        if not data.get("message"):
            return {"message": "Announcement message is required."}, 400

        global announcement_message

        # Check if the same announcement is being posted again
        if announcement_message == data.get("message"):
            return {"message": "You already posted this announcement."}, 400

        announcement_message = data.get("message")
        return {"message": "Announcement posted successfully."}, 201

    @jwt_required()  # Ensure that the user is logged in
    def delete(self):
        """Delete the current announcement"""
        global announcement_message

        # Check if there is no announcement to delete
        if announcement_message is None:
            return {"message": "There is no announcement to delete."}, 404

        announcement_message = None
        return {"message": "Announcement deleted successfully."}, 200
#Create a new admin account
# Mailgun Configuration

from dotenv import load_dotenv
import os

load_dotenv()

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_FROM_EMAIL = f"Registration Complete <mailgun@{MAILGUN_DOMAIN}>"

PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")

@blp.route("/admin/create_admin", methods=["POST"])
class CreateAdmin(MethodView):

    @jwt_required()
    def post(self):
        """Handles admin creation and sends a confirmation email via Mailgun."""
        admin_id = get_jwt_identity()
        current_admin = AdminModel.query.get(admin_id)

        if not current_admin:
            return {"message": "Please login first."}, 403

        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email_address = data.get("email_address")

        if not username or not password or not first_name or not last_name or not email_address:
            return {"message": "Missing required fields: username, password, first_name, last_name, email_address."}, 400

        if not PASSWORD_REGEX.match(password):
            return {"message": "Password does not meet security requirements."}, 400

        if AdminModel.query.filter_by(username=username).first():
            return {"message": "Username already exists."}, 400
        if AdminModel.query.filter_by(email_address=email_address).first():
            return {"message": "Email address already exists."}, 400

        hashed_password = generate_password_hash(password)
        new_admin = AdminModel(
            username=username,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            email_address=email_address,
        )

        db.session.add(new_admin)
        db.session.commit()

        print(f"DEBUG: Sending email to {email_address}...")

        success, response_message = send_confirmation_email(email_address, first_name, last_name, username)

        if not success:
            return {"message": "Admin created but email failed.", "error": response_message}, 500

        return {"message": "Admin account created successfully! A confirmation email has been sent."}, 201

def send_confirmation_email(to_email, first_name, last_name, username):
    """ Sends a confirmation email using Mailgun """
    subject = "Admin Account Created Successfully"
    body = f"""
    Hello {first_name} {last_name},

    Your admin account has been successfully created.

    Username: {username}
    Password: same as username
    You can now log in using the credentials you set.
    Please make sure to change your current password to one you prefer.

    Best regards,
    Your Team
    """

    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": MAILGUN_FROM_EMAIL,
            "to": to_email,
            "subject": subject,
            "text": body,
        }
    )

    print(f"DEBUG: Mailgun Response Code: {response.status_code}")
    print(f"DEBUG: Mailgun Response: {response.text}")

    return response.status_code == 200, response.json()

#Get admins list
@blp.route("/admin/admins_list", methods=["GET"])
class GetAdmins(MethodView):
    @jwt_required()  # Ensure the request has a valid JWT
    def get(self):
        # Extract the admin_id from the JWT
        admin_id = get_jwt_identity()

        # Check if the admin still exists in the database
        admin = AdminModel.query.filter_by(admin_id=admin_id).first()
        if not admin:
            return {"message": "Please log in first"}, 401  # Unauthorized
        
        # Query all admins
        admins = AdminModel.query.all()

        # Serialize the admins' data
        admin_list = [
            {
                "admin_id": admin.admin_id,
                "first_name": admin.first_name,
                "last_name": admin.last_name,
                "email_address": admin.email_address,
            }
            for admin in admins
        ]

        return jsonify(admin_list), 200

#Get feedback list
@blp.route("/admin/feedback")
class FeedbackList(MethodView):
    @jwt_required()  # Ensure that only logged-in users can access
    @blp.response(200, FeedbackSchema(many=True))
    def get(self):
        
        feedback_list = FeedbackModel.query.all()
        return feedback_list
    
#Get/Delete feedback by id
@blp.route("/admin/feedback/<int:id>")
class Feedback(MethodView):
    @jwt_required()  # Ensure the user is authenticated
    @blp.response(200, FeedbackSchema)  # Return the feedback details
    def get(self, id):
       
        feedback = FeedbackModel.query.filter_by(id=id).first()
        if not feedback:
            abort(404, message=f"There is no feedback with ID {id} to retrieve.")
        return feedback

    @jwt_required()  # Ensure the user is authenticated
    def delete(self, id):
       
        feedback = FeedbackModel.query.filter_by(id=id).first()
        if not feedback:
            abort(404, message=f"There is no feedback with ID {id} to delete.")
        db.session.delete(feedback)
        db.session.commit()
        return {"message": f"The feedback with ID {id} was deleted successfully."}, 200

#Delete Own Account
@blp.route("/admin/delete_own_account", methods=["DELETE"])
class DeleteOwnAccount(MethodView):
    @jwt_required()
    def delete(self):
        admin_id = get_jwt_identity()  # Get the admin_id from the JWT token

        # Convert admin_id to integer for comparison
        if int(admin_id) == 1:  # Admin with ID 1 is protected
            return {"message": "The admin account with ID 1 cannot be deleted."}, 403
        
        # Find the admin by the ID from the token
        admin = AdminModel.query.filter_by(admin_id=admin_id).first()

        if not admin:
            return {"message": f"Admin with ID {admin_id} not found."}, 404

        db.session.delete(admin)
        db.session.commit()

        return {"message": f"Admin account with ID {admin_id} deleted successfully."}, 200
    
#logout
@blp.route("/admin/logout", methods=["POST"])
class AdminLogout(MethodView):
    @jwt_required()
    def post(self):
        # Get the JWT ID (jti)
        jti = get_jwt()["jti"]

        # Add the JWT to the blocklist
        add_to_blocklist(jti)

        return jsonify(message="Successfully logged out"), 200
    
#update admin password
@blp.route("/admin/update_password", methods=["POST"])
class UpdatePassword(MethodView):
    @jwt_required()
    def post(self):
        current_admin_id = get_jwt_identity()
        data = request.get_json()

        # Check if `old_password` and `new_password` are provided
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        if not old_password or not new_password:
            return {"message": "Both old and new passwords are required."}, 400

        # Find the current admin by ID
        admin = AdminModel.query.filter_by(admin_id=current_admin_id).first()
        if not admin:
            return {"message": "Admin not found. Please log in again."}, 401

        # Verify the old password
        if not check_password_hash(admin.password, old_password):
            return {"message": "Old password is incorrect."}, 401

        # Validate the new password against the regex
        if not PASSWORD_REGEX.match(new_password):
            return {
                "message": "New password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one number, and one symbol."
            }, 400

        # Update and hash the new password
        admin.password = generate_password_hash(new_password)
        db.session.commit()

        return {"message": "Password updated successfully."}, 200

