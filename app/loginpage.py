import os
from flask import Flask, session, flash
from flask import render_template, redirect, url_for, request, g
from werkzeug.security import generate_password_hash, check_password_hash
from wand.image import Image
from app import webapp
from PIL import Image

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
    uid=session.pop('uid',None)
    session['uid'] = uid
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' select img0 from userimg where 
    uid=%(uid)s '''
    cursor.execute(query, {'uid': uid})
    data=cursor.fetchall()
    imgList=[]
    for s in data:
        imgURL=url_for('static',filename=s[0])
        imgList.append(imgURL)
    #imgURL = url_for('static', filename='blackandwhiteWechatIMG40.jpeg')
    return render_template("Homepage.html",data=data, imgList = imgList)

@webapp.route('/homepage', methods=['POST'])
def uploadimg():
    target=os.path.join(APP_ROOT,'static')
    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("file"):
        if len(file.filename)==0:
            return redirect(url_for('thumbnailsdisplay'))
        filename=file.filename
        destination="/".join([target,filename])
        file.save(destination)
        # cnx = get_db()
        # cursor = cnx.cursor()
        # uid=session.pop('uid',None)
        # session['uid'] = uid
        # query = ''' INSERT INTO userimg (uid,img_path)
        #                            VALUES (%s,%s)'''
        # cursor.execute(query, (uid,destination))
        # cnx.commit()
        image = Image.open(destination)
        size = [100, 100]
        image.thumbnail(size)
        array = filename.split("/")
        newname = "thumbnail"+array[-1]
        destination2 = "/".join([target, newname])
        image.save(destination2)
        # cnx = get_db()
        # cursor = cnx.cursor()
        # uid = session.pop('uid', None)
        # session['uid'] = uid
        # query = ''' INSERT INTO userimg (uid,img_path,img0)
        #                                    VALUES (%s,%s, %s)'''
        # cursor.execute(query, (uid,destination,destination2))
        # cnx.commit()
        image2=Image.open(destination)
        newname2 = "scale" + array[-1]
        destination3 = "/".join([target, newname2])
        #image2.transform('<200>x<200>')
        image2=image2.rotate(90)
        print (image2.type)
        #image2=image2.grayscale()

        print (destination3)
        image2.save(destination3)

        image3=Image.open(destination)
        newname3="blackandwhite"+array[-1]
        image3 = image3.rotate(180)
        destination4 = "/".join([target, newname3])
        # image3 = image3.flop()
        image3.save(destination4)


        image4 = Image.open(destination)
        #image4.transform()
        image4=image4.rotate(270)
        newname4 = "sepia" + array[-1]
        destination5 = "/".join([target, newname4])
        image4.save(destination5)

        cnx = get_db()
        cursor = cnx.cursor()
        uid = session.pop('uid', None)
        session['uid'] = uid
        query = ''' INSERT INTO userimg (uid,img_path,img0,img1,img2,img3)
                                           VALUES (%s,%s, %s,%s,%s,%s)'''
        cursor.execute(query, (uid,filename,newname,newname2,newname3,newname4))
        cnx.commit()
    return redirect(url_for('thumbnailsdisplay'))

@webapp.route('/imagedetail', methods=['POST'])
def showimgdetail():
    imgurl=request.form.get('btn', "")
    array=imgurl.split("/")
    imgname=array[-1]
    print (imgname)
    cnx = get_db()
    cursor = cnx.cursor()
    uid = session.pop('uid', None)
    session['uid'] = uid
    query = ''' select img1, img2, img3 from userimg
    where img0=%(imagename)s and uid= %(uid)s'''
    cursor.execute(query, {'imagename':imgname, 'uid':uid})
    cnx.commit()
    data = cursor.fetchall()
    imgList = []
    for s in data[0]:
        imgURL = url_for('static', filename=s)
        print (s)
        imgList.append(imgURL)
    # imgURL = url_for('static', filename='blackandwhiteWechatIMG40.jpeg')
    return render_template("Imagedetail.html", data=data, imgList=imgList)
