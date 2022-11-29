import os
from os import environ
from dotenv import load_dotenv

load_dotenv('.env')
SECRET_KEY = environ.get('SECRET_KEY')
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = False