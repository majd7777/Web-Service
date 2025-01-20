from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")  
JWT_EXPIRATION_TIME = 3600  
