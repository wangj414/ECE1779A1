from flask import Flask, session
from flask import render_template, redirect, url_for, request, g, app
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


@webapp.route('/welcome', methods=['GET'])
def welcome():
    return render_template("Login.html")
# def welcome():
#     cnx = get_db()
#     cursor = cnx.cursor()
#
#     query = '''INSERT INTO userinfo
# VALUES (1,'Linda','Linda2Tom')'''
#     cursor.execute(query)
#     cnx.commit()
#     return "Hello world!!!"
