import os
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")

    client = MongoClient(os.getenv("MONGO_URI"))

    # Choose your database name
    app.db = client["livestock_db"]
    print("Connected to DB:", client.list_database_names())

    from .routes import main
    app.register_blueprint(main)

    return app