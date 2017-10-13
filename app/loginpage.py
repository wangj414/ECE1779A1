from flask import Flask, session
from flask import render_template, redirect, url_for, request, g, app
from werkzeug.security import generate_password_hash

from app import webapp

import pymysql

from app.config import db_config


def connect_to_database():
    return pymysql.connect(user=db_config['user'],
                           password=db_config['password'],
                           host=db_config['host'],
                           database=db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/cleanrow', methods=['GET'])
def clean():
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' DELETE FROM userinfo'''
    cursor.execute(query)
    cnx.commit()
    return "Delete Success!"


@webapp.route('/welcome', methods=['GET'])
def welcome():
    return render_template("Login.html")


@webapp.route('/welcome', methods=['POST'])
# Create a new student and save them in the database.
def user_create_save():
    username = request.form.get('Username', "")
    password = request.form.get('Password', "") # Store the user infomation in these variables
    encodedPassword=generate_password_hash(password)

    cnx = get_db()
    cursor = cnx.cursor()

    if  username== "" or password == "" :
        error_msg = "Error: All fields are required!"

    query = ''' INSERT INTO userinfo (username,user_passwrd)
                       VALUES (%s,%s)'''

    cursor.execute(query, (username,encodedPassword))
    cnx.commit()

    return redirect(url_for('sections_list'))
