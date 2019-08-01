from flask import Flask, render_template, url_for, flash, redirect, request, session,Blueprint, make_response
from flask_mysqldb import MySQL
import re
from flask_mail import Mail, Message
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
import re
import requests
from math import cos, asin, sqrt

#API key for google maps
API_KEY=""

#variables for browser and host information
browser_and_agent_info, browser_name, host, host_url = 0 ,0, 0, 0

#distance between two points on maps
def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295     #Pi/180
    a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) #2*R*asin..


#Server Side Validation for email and passwrod
def is_valid_email(email):
    if len(email) > 7:
        return bool(re.match("^.+@(\[?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", email))

def is_valid_password(password):
    if len(password)>6:
        return True
    else:
        return False


def get_reset_token(id, expires_sec=1800):
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id': id}).decode('utf-8')

def verify_reset_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None
    return user_id


def get_session():
    if 'user' in session:
        return session['user']
    return 0

def drop_session():
    session.pop('user')

app = Flask(__name__)


app.config['SECRET_KEY'] = '5f3e5b6f4c33f8e5ef8b9c24187b3f1c'
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'hekaltesttask@gmail.com',
    MAIL_PASSWORD = 'hekaltesttask123',
))

mail = Mail(app)


#Database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'flaskdatabase'

mysql = MySQL(app)

app.config['SECRET_KEY']  = '5f3e5b6f4c33f8e5ef8b9c24187b3f1c' #any random token for security

@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    global browser_and_agent_info, browser_name, host, host_url
    browser_and_agent_info = request.user_agent
    browser_name = request.user_agent.browser
    host = request.host
    host_url=request.host_url

    if request.method =='POST':
        user_details = request.form
        email = user_details['email']
        password = user_details['password']

        ## Server Side Validating
        if not is_valid_email(email):
            flash(f'You entered an invalid form of email, it must be like \' example@example.example \' ')
            return redirect(url_for('login'))

        if not is_valid_password(password):
            flash(f'You entered an invalid password')
            return redirect(url_for('login'))

        cur = mysql.connection.cursor()

        ret=cur.execute("SELECT * FROM users WHERE email=%s and password =%s", (email, password))
        user_details = cur.fetchall()
        mysql.connection.commit()
        cur.close()


        if ret:
            session['user'] = email
            return render_template('success.html')
        else :
            flash(f'you entered an invalid data, try again')
            return redirect(url_for('login'))

    ret=get_session()
    if ret != 0:
        return redirect(url_for('profile'))
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    ret=get_session()
    if ret != 0:
        drop_session()
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    global browser_and_agent_info, browser_name, host, host_url
    server_browser_details = [browser_and_agent_info, browser_name, host, host_url]
    ret=get_session()
    if ret != 0:
        cur = mysql.connection.cursor()
        user_details=cur.execute("SELECT * FROM users WHERE email=%s", [ret])
        user_details = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('profile.html', user_details=user_details, server_browser_details = server_browser_details)
    else:
        return redirect(url_for('login'))



def send_email(user):
    token = get_reset_token(user)
    msg = Message('Pasword reset link', sender='noreply@digitzillatask.com', recipients=[user])
    print('correct2')

    msg.body = f''' To reset your password, visit the following link:

{url_for('request_password', token=token, _external=True)}
please note that this link will expire after 30 minutes.
    '''
    print('correct3',user)

    mail.send(msg)



@app.route('/register', methods=['GET','POST'])
def register():
    if request.method =='POST':
        user_details = request.form
        email = user_details['email']
        name = user_details['name']
        password = user_details['password']


        if not is_valid_email(email):
            flash(f'You entered an invalid form of email, it must be like \' example@example.example \' ')
            return redirect(url_for('register'))

        if not is_valid_password(name):
            flash(f'You entered an invalid password')
            return redirect(url_for('register'))

        if not is_valid_password(password):
            flash(f'You entered an invalid password')
            return redirect(url_for('register'))



        try :
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (email, name, password )VALUES( %s, %s,%s );", (email, name, password))
            user_details = cur.fetchall()
            mysql.connection.commit()
            cur.close()
            return render_template('register_success.html')
        except:
            return ('There is an error')

    return render_template('register.html')


@app.route('/reset_password', methods=['GET','POST'])
def reset_password():
    if request.method =='POST':
        user_details = request.form
        email = user_details['email']
        cur = mysql.connection.cursor()
        ret=cur.execute("SELECT * FROM users WHERE email= %s", [email])
        user_details = cur.fetchall()
        mysql.connection.commit()
        cur.close()

        if ret:
            send_email(email)
            return render_template('success2.html', email=email)
        else :
            flash(f'Your email is not registered')
            return render_template('reset_password.html')
    return render_template('reset_password.html')


@app.route('/reset_password/<token>', methods=['GET','POST'])
def request_password(token):
    user=verify_reset_token(token)
    if not user:
        flash(f'That is an invalid or an expired token, please login again')
        return redirect(url_for('login'))

    if request.method =='POST':
        passwords = request.form
        password = passwords['password']
        repassword = passwords['repassword']

        if password != repassword:
            flash(f'The two passwords do not match, try again')
            return redirect(url_for('request_password', token=token))

        if not is_valid_password(password):
            flash(f'You entered an invalid form of password, try again')
            return redirect(url_for('request_password', token=token))


        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password = %s WHERE email = %s", (password, user))
        mysql.connection.commit()
        cur.close()
        return render_template('password_reset_success.html')

    return render_template('request_password.html')

@app.route('/upload', methods=['GET','POST'])
def upload():
    return render_template('large_file_upload.html')


@app.route('/map', methods=['GET','POST'])
def map():
    if request.method =='POST':
        details = request.form

        fir=str(details['source'])
        sec=str(details['destination'])

        fir = fir.replace(' ', '+')
        sec = sec.replace(' ', '+')

        response1 = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+fir+'&key='+API_KEY)
        first_place = response1.json()
        first_flag=0
        try:
            loc1=( first_place['results'][0]['geometry']['location'])

        except:
            first_flag = 1


        response1 = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+sec+'&key='+API_KEY)
        second_place = response1.json()
        second_flag=0
        try:
            loc2=(second_place['results'][0]['geometry']['location'])
        except:
            second_flag=1


        if not(first_flag or second_flag):

            dist=get_distance(loc1['lat'], loc1['lng'], loc2['lat'], loc2['lng'])
            dist=str(dist)
            return render_template('map_result.html', dist=dist)

        else:
            dist=distance(30.1255015, 31.3198485, 31.2240349, 30.0949713)
            dist=str(dist)
            flash('API limit.. we will show you the distance between Cairo and Alexandria instead')
            return render_template('map_result.html', dist=dist)

    return render_template('google_maps.html')


if __name__ == '__main__':
    app.run(debug=True)
