from flask import Flask, render_template, flash,request, url_for, redirect, session
from content_management import Content
from dbconnect import connection
from flask_wtf import FlaskForm
from wtforms import Form, TextField, PasswordField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc
from functools import wraps

TOPIC_DIST = Content()
app = Flask(__name__)

app.secret_key = 'some_secret'

@app.route("/")
def homepage():
    return render_template('/main.html')

@app.route("/dashboard/")
def dashboard():
    flash("flash message!!")
    return render_template('/dashboard.html', TOPIC_DIST = TOPIC_DIST)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login_page'))
    return wrap

@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash("you are logged out")
    gc.collect()
    return redirect(url_for('homepage'))

@app.route('/login/', methods = ['GET', 'POST'])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == 'POST':
            data = c.execute("SELECT * FROM users WHERE username = (%s)", [thwart(request.form['username'])])
            data = c.fetchone()[2]

            if(sha256_crypt.verify(request.form['password'], data)):
                session['logged_in'] = True
                session['username'] = request.form['username']
                flash('you are logged in')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Credentials. Try Again'
        gc.collect()        
        return render_template('login.html', error=error)

    except Exception as e:
        error = 'Invalid Credentials. Try Again'
        flash(error)
        return render_template('login_page.html', error = error)

class RegistrationForm(Form):
    username = TextField('Username', validators = [Length(min=4, max=20)])
    email = TextField('Email Address', validators = [Length(min=4, max=50)])
    password = PasswordField('Password', validators = [DataRequired(), EqualTo('confirm', message="Password Must be same.")])
    confirm = PasswordField('Confirm Password')
    accept_tos = BooleanField('I accept the TOS', validators= [DataRequired()])

@app.route('/register/', methods=['GET', 'POST'])
def register_page():
    try:
       form = RegistrationForm(request.form)
       if request.method == 'POST' and form.validate():
           username = form.username.data
           email = form.email.data
           password = sha256_crypt.encrypt((str(form.password.data)))
           c, conn = connection()

           x = c.execute("SELECT * FROM users WHERE username = (%s)", [(thwart(username))])

           if int(x) > 0:
               flash("This username is already taken please try a another one")
               return render_template('register.html', form=form)
           else:
               c.execute("INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)", (thwart(username), thwart(password), thwart(email), thwart('/intro-to-python')))
               conn.commit()
               flash("Thaks for registartion")
               c.close()
               conn.close() 
               gc.collect()

               session['logged_in'] = True
               session['username'] = username
                
               return redirect(url_for('dashboard'))
       return render_template('register.html', form=form)

    except Exception as e:
        return(str(e))

if __name__ == "__main__":
    app.run(debug=True)
