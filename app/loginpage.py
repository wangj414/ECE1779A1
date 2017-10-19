import os
from flask import Flask, session, flash
from flask import render_template, redirect, url_for, request, g
from werkzeug.security import generate_password_hash, check_password_hash
from wand.image import Image
from app import webapp

import pymysql

from app.config import db_config

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


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
        cursor.execute(query, {'username': userget})
        data = cursor.fetchall()
        if len(data) == 0:
            error_msg = "Error: No this user!"
            flash(error_msg)
            return redirect(url_for('user_login'))
        psdori = str(data[0][0])
        result = check_password_hash(psdori, psdget)

        if result:
            query = ''' select user_id from userinfo
                        where username=%(username)s'''
            cursor.execute(query, {'username': userget})
            data2 = cursor.fetchall()
            uid = int(data2[0][0])
            session['uid'] = uid
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
    uid = session.pop('uid', None)
    session['uid'] = uid
    cnx = get_db()
    cursor = cnx.cursor()
    query = ''' select img0 from userimg where 
    uid=%(uid)s '''
    cursor.execute(query, {'uid': uid})
    data = cursor.fetchall()
    imgList = []
    for s in data:
        imgURL = url_for('static', filename=s[0])
        imgList.append(imgURL)
    # imgURL = url_for('static', filename='blackandwhiteWechatIMG40.jpeg')
    return render_template("Homepage.html", data=data, imgList=imgList)


@webapp.route('/homepage', methods=['POST'])
def uploadimg():
    target = os.path.join(APP_ROOT, 'static')
    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("file"):
        if len(file.filename) == 0:
            return redirect(url_for('thumbnailsdisplay'))
        filename = file.filename
        destination = "/".join([target, filename])
        file.save(destination)
        array = filename.split("/")
        newname="thumbnail" + array[-1]
        newname2="scale" + array[-1]
        newname3="blackandwhite" + array[-1]
        newname4="sepia" + array[-1]
        with Image(filename=destination) as image:
            destination2 = "/".join([target, newname])
            with image.clone() as thumbimg:
                thumbimg.resize(100,100)
                thumbimg.save(filename=destination2)
            with image.clone() as image2:
                image2.format = 'png'
                image2.flip()
                image2.resize(1024,1024)
                destination3 = "/".join([target, newname2])
                image2.save(filename=destination3)
            with image.clone() as image3:
                image3.format = 'png'
                width = image3.width
                height = image3.height
                image3.crop(int(width/4),int(height/4),width=int(width/2),height=int(height/2))
                image3.resize(1024, 1024)
                destination4 = "/".join([target, newname3])
                image3.save(filename=destination4)
            with image.clone() as image4:
                image4.format = 'png'
                image4.flop()
                image4.resize(1024, 1024)
                destination5 = "/".join([target, newname4])
                image4.save(filename=destination5)

        cnx = get_db()
        cursor = cnx.cursor()
        uid = session.pop('uid', None)
        session['uid'] = uid
        print(uid)
        print(filename)
        print(newname)
        print(newname2)
        print(newname3)
        print(newname4)
        query = ''' INSERT INTO userimg (uid,img_path,img0,img1,img2,img3)
                                           VALUES (%s,%s, %s,%s,%s,%s)'''
        cursor.execute(query, (uid, filename, newname, newname2, newname3, newname4))
        cnx.commit()
    return redirect(url_for('thumbnailsdisplay'))


@webapp.route('/imagedetail', methods=['POST'])
def showimgdetail():
    imgurl = request.form.get('btn', "")
    array = imgurl.split("/")
    imgname = array[-1]
    print(imgname)
    cnx = get_db()
    cursor = cnx.cursor()
    uid = session.pop('uid', None)
    session['uid'] = uid
    query = ''' select img_path, img1, img2, img3 from userimg
    where img0=%(imagename)s and uid= %(uid)s'''
    cursor.execute(query, {'imagename': imgname, 'uid': uid})
    cnx.commit()
    data = cursor.fetchall()
    imgList = []
    for s in data[0]:
        imgURL = url_for('static', filename=s)
        print(s)
        imgList.append(imgURL)
    # imgURL = url_for('static', filename='blackandwhiteWechatIMG40.jpeg')
    return render_template("Imagedetail.html", data=data, imgList=imgList)

@webapp.route('/test/FileUpload/Linda/Linda2Tom', methods=['GET'])
def testPage():
 return render_template("uploadForm.html")


@webapp.route('/test/FileUpload/Linda/Linda2Tom', methods=['POST'])
def test():
    isPass=False
    if request.form['button'] == 'Login':
     userget = request.form.get('Username', "")
     psdget = request.form.get('Password', "")
     if userget == "" or psdget == "":
         error_msg = "Error: All fields are required!"
         flash(error_msg)
         return redirect(url_for('test'))
     cnx = get_db()
     cursor = cnx.cursor()
     query = ''' select usr_passwrd from userinfo
         where username=%(username)s'''
     cursor.execute(query, {'username': userget})
     data = cursor.fetchall()
     if len(data) == 0:
         error_msg = "Error: No this user!"
         flash(error_msg)
         return redirect(url_for('test'))
     psdori = str(data[0][0])
     result = check_password_hash(psdori, psdget)
     if result:
         query = ''' select user_id from userinfo
                         where username=%(username)s'''
         cursor.execute(query, {'username': userget})
         data2 = cursor.fetchall()
         uid = int(data2[0][0])
         session['uid'] = uid
         isPass=True
         return redirect(url_for('test'))
     else:
         error_msg = "Error: Password not valid!"
         flash(error_msg)
         return redirect(url_for('test'))
    if isPass:
        target = os.path.join(APP_ROOT, 'static')
        if not os.path.isdir(target):
            os.mkdir(target)
        for file in request.files.getlist("file"):
            if len(file.filename) == 0:
               return redirect(url_for('test'))

            filename = file.filename
            destination = "/".join([target, filename])
            file.save(destination)
            array = filename.split("/")
            newname = "thumbnail" + array[-1]
            newname2 = "scale" + array[-1]
            newname3 = "blackandwhite" + array[-1]
            newname4 = "sepia" + array[-1]
            with Image(filename=destination) as image:
                destination2 = "/".join([target, newname])
                with image.clone() as thumbimg:
                    thumbimg.resize(100, 100)
                    thumbimg.save(filename=destination2)
                with image.clone() as image2:
                    image2.format = 'png'
                    image2.flip()
                    image2.resize(1024, 1024)
                    destination3 = "/".join([target, newname2])
                    image2.save(filename=destination3)
                with image.clone() as image3:
                    image3.format = 'png'
                    width = image3.width
                    height = image3.height
                    image3.crop(int(width / 4), int(height / 4), width=int(width / 2), height=int(height / 2))
                    image3.resize(1024, 1024)
                    destination4 = "/".join([target, newname3])
                    image3.save(filename=destination4)
                with image.clone() as image4:
                    image4.format = 'png'
                    image4.flop()
                    image4.resize(1024, 1024)
                    destination5 = "/".join([target, newname4])
                    image4.save(filename=destination5)

            cnx = get_db()
            cursor = cnx.cursor()
            uid = session.pop('uid', None)
            session['uid'] = uid
            print(uid)
            print(filename)
            print(newname)
            print(newname2)
            print(newname3)
            print(newname4)
            query = ''' INSERT INTO userimg (uid,img_path,img0,img1,img2,img3)
                                                       VALUES (%s,%s, %s,%s,%s,%s)'''
            cursor.execute(query, (uid, filename, newname, newname2, newname3, newname4))
            cnx.commit()
            return redirect(url_for('thumbnailsdisplay'))
    else:
        return redirect(url_for('test'))
