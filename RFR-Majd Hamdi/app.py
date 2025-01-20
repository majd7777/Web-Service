import os
from flask import Flask, request
from flask_smorest import Api
from db import db
from seed import seed_E_outtrips, seed_E_intrips, seed_A_intrips, seed_A_outtrips, seed_station_locations, seed_admin
from resources.E_Outgoing import blp as E_outtrips_Blueprint
from resources.E_Incoming import blp as E_intrips_Blueprint
from resources.feedback import blp as FeedbackBlueprint
from resources.stations_locations import blp as StationLocationsBlueprint
from resources.admin import blp as Admin
from resources.D_line import blp as DLineBlueprint
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
import logging

load_dotenv()

# Set up logging to file for admin requests
log_filename = 'admin_requests.log'

# Create a file handler to write log messages to a file
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

# Create a formatter for log entries
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Set up the logger
logger = logging.getLogger('admin_logger')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Decorator to log requests to specific endpoints (Admin Blueprint)
def log_admin_request(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Request to Admin endpoint: {request.path} from IP: {request.remote_addr} with User-Agent: {request.user_agent}")
        return func(*args, **kwargs)
    return wrapper

def create_app(db_url=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "super_secret_key"
    app.config["API_TITLE"] = "TBS REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///data.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"

    # Initialize extensions
    jwt = JWTManager(app)
    db.init_app(app)
    api = Api(app)

    # Initialize rate limiter (no need to pass key_func argument)
    limiter = Limiter(app)

    # Set global rate limit for all routes
    app.config["RATELIMIT_DEFAULT"] = "8 per minute"  

    # Apply global rate limiting to all routes
    limiter.limit(app.config["RATELIMIT_DEFAULT"])

    # Database initialization and seeding
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")  
    else:
        db_path = db_uri

    db_exists = os.path.exists(db_path) 

    with app.app_context():
        if not db_exists:
            db.create_all()
            seed_E_intrips()
            seed_E_outtrips()
            seed_A_intrips()
            seed_A_outtrips()
            seed_station_locations()
            seed_admin()

    # Register blueprints
    api.register_blueprint(E_outtrips_Blueprint)
    api.register_blueprint(E_intrips_Blueprint)
    api.register_blueprint(FeedbackBlueprint)
    api.register_blueprint(StationLocationsBlueprint)

    # Apply logging for the Admin blueprint
    @app.before_request
    def log_admin_endpoints():
        if request.blueprint == 'Admin':  # Check if the request is for the 'admin' blueprint
            logger.info(f"Request to {request.path} in Admin blueprint from IP: {request.remote_addr} with User-Agent: {request.user_agent}")

    api.register_blueprint(Admin) 
    api.register_blueprint(DLineBlueprint)

    return app
