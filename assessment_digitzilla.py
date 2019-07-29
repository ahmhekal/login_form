from flask import Flask, render_template, url_for, flash, redirect, request, session
from flask_mysqldb import MySQL
import yaml
import re
from flask_mail import Mail, Message
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
import re


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
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


app.config['SECRET_KEY']  = '5f3e5b6f4c33f8e5ef8b9c24187b3f1c' #any random token for security



@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method =='POST':
        user_details = request.form
        email = user_details['email']
        password = user_details['password']


        ## Server Side Validating
        if not is_valid_email(email):
            return "You entered an invalid form of email"

        if not is_valid_password(password):
            return "You entered an invalid form of password"


        cur = mysql.connection.cursor()


        ret=cur.execute("SELECT * FROM users WHERE email=%s and password =%s", (email, password))
        user_details = cur.fetchall()
        mysql.connection.commit()
        cur.close()


        if ret:
            return render_template('success.html', email=email)
        else :
            return ('you entered an invalid data')


    #return redirect(url_for('profile'))
    return render_template('login.html')


@app.route('/profile')
def profile():
    cur = mysql.connection.cursor()
    ret = cur.execute('SELECT * FROM users')
    if ret > 0:
        user_details = cur.fetchall()
        return render_template('profile.html', user_details=user_details)



def send_email(user):
    token = get_reset_token(user)
    msg = Message('Pasword reset link', sender='noreply@digitzillatask.com', recipients=[user])
    print('correct2')

    msg.body = f''' To reset your password, visit the following link:

{url_for('request_password', token=token, _external=True)}

    '''
    print('correct3',user)

    mail.send(msg)

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

        print('correct')


        if ret:
            send_email(email)
            return render_template('success2.html', email=email)
        else :
            return ('Your email is not registered')

    return render_template('reset_password.html')


@app.route('/reset_password/<token>', methods=['GET','POST'])
def request_password(token):
    user=verify_reset_token(token)
    if not user:
        return ('That is an invalid token')

    if request.method =='POST':
        passwords = request.form
        password = passwords['password']
        repassword = passwords['repassword']

        if password != repassword:
            return 'the two passwords don\'t match.. try again'

        if not is_valid_password(password):
            return "You entered an invalid form of password"

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password = %s WHERE email = %s", (password, user))
        mysql.connection.commit()
        cur.close()
        return ('Your Password has been changed successfully')

    return render_template('request_password.html')



if __name__ == '__main__':
    app.run(debug=True)
