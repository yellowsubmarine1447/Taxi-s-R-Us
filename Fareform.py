from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.fields import DateField, TimeField, EmailField
from wtforms import validators


class FareForm(FlaskForm):
    origin = StringField("Start", validators=[validators.data_required()])
    dest = StringField("Destination", validators=[validators.data_required()])
    trip_time = TimeField("Time of departure:", validators=[validators.data_required()])
    trip_date = DateField("Date of departure:", validators=[validators.data_required()])
    submit = SubmitField("Estimate")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[validators.data_required()])
    password = PasswordField("Password", validators=[validators.data_required()])
    submit = SubmitField("Sign In!", validators=[validators.data_required()])


class RegisterForm(FlaskForm):
    email = EmailField('E-mail', validators=[validators.data_required()])
    password = PasswordField('Password', [
        validators.data_required(),
        validators.equal_to('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password', validators=[validators.data_required()])
    submit = SubmitField("Sign Up!")


class FeedbackForm(FlaskForm):
    title = StringField("Title", validators=[validators.data_required()])
    content = TextAreaField("Content", validators=[validators.data_required()])
    submit = SubmitField("Send Feedback!")


class ForgotPassword(FlaskForm):
    email = EmailField("Email", validators=[validators.data_required()])
    submit = SubmitField("Send email!")
