import os
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # Secret key from environment variable
    app.secret_key = os.getenv("SECRET_KEY")

    # MongoDB connection
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    app.db = client.get_default_database()

    # Register blueprint
    from .routes import main
    app.register_blueprint(main)

    return app