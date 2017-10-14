import os
from flask import Flask, session, flash
from flask import render_template, redirect, url_for, request, g, app
from werkzeug.contrib.sessions import Session
from werkzeug.security import generate_password_hash, check_password_hash
from wand.image import Image
from app import webapp

import pymysql

from app.config import db_config

APP_ROOT=os.path.dirname(os.path.abspath(__file__))

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
    query = ''' DELETE FROM userimg'''
    cursor.execute(query)
    cnx.commit()
    return "Delete Success!"


@webapp.route('/welcome', methods=['GET'])
def welcome():
    return render_template("Login.html")


@webapp.route('/welcome', methods=['POST'])
def user_login():
    if request.form['button'] == 'SignUp':
     return redirect(url_for('signup'))
    else:
        userget = request.form.get('Username', "")
        psdget = request.form.get('Password', "")
        if userget == "" or psdget == "":
             error_msg = "Error: All fields are required!"
             flash(error_msg)
             return redirect(url_for('user_login'))
        cnx = get_db()
        cursor = cnx.cursor()
        query = ''' select usr_passwrd from userinfo
            where username=%(username)s'''
        cursor.execute(query, {'username':userget})
        data=cursor.fetchall()
        if len(data)==0:
            error_msg = "Error: No this user!"
            flash(error_msg)
            return redirect(url_for('user_login'))
        psdori=str(data[0][0])
        result=check_password_hash(psdori,psdget)

        if result:
            query = ''' select user_id from userinfo
                        where username=%(username)s'''
            cursor.execute(query, {'username': userget})
            data2 = cursor.fetchall()
            uid=int(data2[0][0])
            session['uid']=uid
            return redirect(url_for('thumbnailsdisplay'))
        else:
            error_msg = "Error: Password not valid!"
            flash(error_msg)
            return redirect(url_for('welcome'))


@webapp.route('/signup', methods=['GET'])
def signup():
    return render_template("Signup.html")

@webapp.route('/signup', methods=['POST'])
def user_create_save():
    username = request.form.get('Username', "")
    password = request.form.get('Password', "")  # Store the user infomation in these variables
    encodedPassword = generate_password_hash(password)

    cnx = get_db()
    cursor = cnx.cursor()

    if username == "" or password == "":
        error_msg = "Error: All fields are required!"
        flash(error_msg)
        return redirect(url_for('user_login'))

    query = ''' INSERT INTO userinfo (username,usr_passwrd)
                           VALUES (%s,%s)'''

    cursor.execute(query, (username, encodedPassword))
    cnx.commit()
    return redirect(url_for('user_login'))

@webapp.route('/homepage', methods=['GET'])
def thumbnailsdisplay():
    return render_template("Homepage.html")

@webapp.route('/homepage', methods=['POST'])
def uploadimg():
    target=os.path.join(APP_ROOT,'images/')
    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("file"):
        filename=file.filename
        destination="/".join([target,filename])
        print(filename)  #? This is what should be stored in my database

        file.save(destination)
        cnx = get_db()
        cursor = cnx.cursor()
        uid=session.pop('uid',None)
        query = ''' INSERT INTO userimg (uid,img_path)
                                   VALUES (%s,%s)'''
        cursor.execute(query, (uid,filename))
        cnx.commit()
    return "Success"
    return None

