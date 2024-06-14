from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user
from Fareform import *
from datetime import date as d
from datetime import datetime
import urllib.request as urlrequest
import urllib.parse as urlparse
import json

# The database setup (User and Booking classes) is code similar to that used by a youtube tutorial:
# https://www.youtube.com/watch?v=CSHx6eCkmv0


app = Flask(__name__)
app.config["SECRET_KEY"] = "0x|nW,(~-#w.{=u27IUOrg/,xPLCA`Z6"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(uid):
    """
    :param uid: Shorthand for user id
    :return: Gets user with specific user id
    """
    return User.query.get(int(uid))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pass_hash = db.Column(db.String(128), nullable=False)
    bookings = db.relationship('Booking', backref='author', lazy=True)
    feedback = db.relationship('Feedback', backref='author', lazy=True)

    def __repr__(self):
        return "<User {}>".format(self.id)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return "<Feedback {}>".format(self.id)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trip_date = db.Column(db.String, nullable=False)
    trip_time = db.Column(db.String, nullable=False)
    cost = db.Column(db.String, nullable=False)
    distance = db.Column(db.String, nullable=False)
    origin = db.Column(db.String, nullable=False)
    destination = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return "<Booking {}>".format(self.id)


def relevant_time(time):
    """
    :param time: The time to be converted into a usable format
    :return: An integer used for time calculations and an error message
    """
    try:
        hour, minute = time.split(":")
        hour, minute = int(hour), int(minute)
    except:
        return None, "Expected time in the format hour:minute AM/PM. Please use the fare calculator."
    return hour * 60 + minute, None


def get_weekday(date):
    """
    :param date: The date
    :return: The day the date lies on
    """
    try:
        year, month, day = [int(x) for x in date.split("-")]
        return d(year, month, day).weekday(), None
    except:
        return None, "Expected date in the format year-month-day. Please use the fare calculator."


def parse_time(time_taken):
    """
    :param time_taken: The time as seconds
    :return: The time parsed into a string describing the number of hours, minutes and seconds
    """
    ret = []
    if time_taken > 3600:
        ret.append(str(time_taken//3600) + " hours")
        time_taken %= 3600
    if time_taken > 60:
        ret.append(str(time_taken//60) + " minutes")
        time_taken %= 60
    ret.append(str(time_taken) + " seconds")
    if len(ret) == 3:
        return ret[0] + ", " + ret[1] + " and " + ret[2]
    if len(ret) == 2:
        return ret[0] + " and " + ret[1]
    return ret[0]


@app.route("/book")
def book_fare():
    if not current_user.is_authenticated or current_user.bookings:  # check if the user has made any bookings or isn't authenticated
        return redirect("/")
    origin, destination, time, date = [request.args.get(x) for x in ["origin", "destination", "time", "date"]]
    cost, _, distance, e = calculate_fare(origin, destination, date, time)
    if e:
        return redirect("/")
    db.session.add(Booking(trip_date=date, trip_time=time, origin=origin, destination=destination,
                           cost=cost, distance=distance, user_id=current_user.id))  # add the booking details to the database
    db.session.commit()
    flash("Your fare has been booked!", "text-success")
    return redirect("/")


@app.route("/", methods=["GET", "POST"])  # home page that estimates fare
def home():
    form = FareForm()
    if form.validate_on_submit():  # post requests and requests with the valid csrf token
        origin = request.form.get("origin")
        destination = request.form.get("dest")
        time = request.form.get("trip_time")
        date = request.form.get("trip_date")
        cost, time_taken, distance, e = calculate_fare(origin, destination, date, time)
        if e:  # check if any errors occurred from calculating the fare
            return render_template("result.html",
                                   location="Fare estimate",
                                   error=e,
                                   auth=current_user)
        read_date = "/".join(date.split("-")[::-1])
        read_time = datetime.strptime(time, "%H:%M").strftime("%I:%M %p")
        try:  # check if the user has booked any fares
            if current_user.bookings:
                booked = True
            else:
                booked = False
        except:
            booked = False
        return render_template("result.html",
                               location="Fare estimate",
                               cost=cost,
                               time_taken=time_taken,
                               distance=distance,
                               origin=origin,
                               destination=destination,
                               date=date,
                               time=time,
                               read_date=read_date,
                               read_time=read_time,
                               booked=booked,
                               auth=current_user)  # return all this data
    return render_template("index.html", location="Home", form=form, auth=current_user)


def calculate_fare(origin, destination, date, time):
    data = {"wp.0": origin,
            "wp.1": destination,
            "key": "AqbFlmwHJ22y5xeq1bz8VIMq4Pzs3Xbt4BHGlO5EYvey1r8x3XVFPhGzF-4YmeAB"}
    data = urlparse.urlencode(data).encode('utf-8')
    try:
        response = urlrequest.urlopen("http://dev.virtualearth.net/REST/v1/Routes/driving?" + str(data)[2:-1]) # send request to API
    except urlrequest.HTTPError as e:  # catch any errors if the api failed
        try:
            error = json.load(e.fp)
        except:  # the request is not valid json
            e = "A problem has occurred with the tool used to calculate the distance. Please notify us."
            return render_template("result.html", location="Fare estimate", error=e)
        if error["errorDetails"][0] == "One or more locations specified in the waypoint parameter are invalid or " \
                                       "require more information.":  # when either the origin or destination doesn't exist
            location = error["errorDetails"][1]
            if location == origin:
                e = "The starting location " + location + " could not be recognised."
            elif location == destination:
                e = "The destination " + location + " could not be recognised."
            else:
                e = "There's something wrong with our algorithm, please notify us immediately."  # logic error
        else:
            e = "An error occurred while calculating the distance: " + (error["errorDetails"][0])  # some other error
        return None, None, None, e
    response = json.load(response)
    distance = response['resourceSets'][0]['resources'][0]['travelDistance']
    time_taken = response['resourceSets'][0]['resources'][0]['travelDuration']
    
    t, e = relevant_time(time)  # a way of converting time into a single number to easily check time ranges
    if e:
        return None, None, None, e  # if time is not in correct format
    if 1320 <= t <= 1440 or 0 <= t <= 360:  # night distance charge calculations
        rate = 2.63
    else:
        rate = 2.19
    weekday, e = get_weekday(date)
    if e:  # date format is incorrect
        return None, None, None, e
    year, month, day = [int(x) for x in date.split("-")]
    if year*365+month*31+day < d.today().year*365+d.today().month*31+d.today().day:  # check if provided date is before today
        return None, None, None, "Please provide a date that isn't before today"
    hire_charge = 3.6
    if weekday in [4, 5] and (1320 <= t <= 1440 or 0 <= t <= 360):  # peak-time hire charge calculations
        hire_charge += 2.5
    cost = "{0:.2f}".format(float(distance) * rate + hire_charge)  # final cost
    return cost, parse_time(time_taken), distance, None


@app.route("/contact", methods=["GET", "POST"])  # contact page
def contact():
    form = FeedbackForm()
    if current_user.is_authenticated and form.validate_on_submit():
        db.session.add(Feedback(title=form.title.data, content=form.content.data, user_id=current_user.id))
        db.session.commit()
        flash("Your feedback was sent!", "text-success")
        return render_template("contact.html", location="Contact", auth=current_user, form=form)
    return render_template("contact.html", location="Contact", auth=current_user, form=form)


@app.route("/login", methods=["GET", "POST"])  # login page
def login():
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.pass_hash, form.password.data):
            login_user(user, remember=True)
            return redirect("/")
        else:
            flash("The email doesn't exist or the password is incorrect", "text-danger")
    return render_template("login.html", location="Login", form=form, auth=current_user)


@app.route("/register", methods=["GET", "POST"])  # register page
def register():
    if current_user.is_authenticated:
        return redirect("/")
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash("The email provided exists", "text-danger")
        else:
            pass_hash = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
            db.session.add(User(
                pass_hash=pass_hash,
                email=email))
            db.session.commit()
            flash("Successfully registered! Now login with your account", "text-success")
            return redirect("/login")
    elif 'password' in form.errors:
        if form.errors['password'][0] == "Passwords must match":
            flash("Passwords must match", "text-danger")
    return render_template("register.html", location="Register", form=form, auth=current_user)


@app.route("/forgotpassword")
def forgot_password():
    form = ForgotPassword()
    if form.validate_on_submit():
        flash("An email was sent to reset your password. Please check your inbox", "text-success")
        return render_template("form_password.html", form=form)
    return render_template("forgot_password.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/admin/feedback")
def admin_dashboard():
    if not current_user.is_authenticated or current_user.id != 1:
        return redirect("/")
    return render_template("feedback.html", users=User.query.all(), location="Feedback")


@app.route("/admin/bookings")
def admin_bookings():
    if not current_user.is_authenticated or current_user.id != 1:
        return redirect("/")
    return render_template("bookings.html", users=User.query.all(), location="Bookings")


@app.errorhandler(404)  # handling 404 not found errors
def error404(_):
    return render_template("404.html", location="Page not found", auth=current_user)


@app.errorhandler(500)  # handling 500 server errors
def error500(_):
    return render_template("500.html", location="Internal server error", auth=current_user)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)  # access from 127.0.0.1, change port if you want
