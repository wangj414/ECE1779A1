import os
from flask import Flask, app
from werkzeug.contrib.sessions import Session

webapp = Flask(__name__)
webapp.secret_key="lalala"
from app import config
from app import loginpage



