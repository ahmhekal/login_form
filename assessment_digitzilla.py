from flask import Flask, render_template, url_for, flash, redirect, request
from forms import LoginForm
from flask_mysqldb import MySQL
import yaml


app = Flask(__name__)

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
    form = LoginForm() #instance from login form

#    if form.validate_on_submit():
#        flash(f'Successfully login for {form.email.data}!', 'sucess')

    if request.method =='POST':
        user_details = request.form
        email = user_details['email']
        password = user_details['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(email, password) VALUES(%s, %s)", (email, password))
        mysql.connection.commit()
        cur.close()
        return render_template('success.html', email=email)
    #return redirect(url_for('profile'))
    return render_template('login.html', form=form)


@app.route('/profile')
def profile():
    cur = mysql.connection.cursor()
    ret = cur.execute('SELECT * FROM users')
    if ret > 0:
        user_details = cur.fetchall()
        return render_template('profile.html', user_details=user_details)




if __name__ == '__main__':
    app.run(debug=True)
