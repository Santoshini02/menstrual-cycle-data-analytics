from flask import Flask,render_template,redirect,request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,login_user,login_required,logout_user,current_user,UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,timedelta,date
import random

app=Flask(__name__)

app.config['SECRET_KEY']='secret'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///period.db'

db=SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"

# ------------------
# DATABASE MODELS
# ------------------

class User(UserMixin,db.Model):

    id=db.Column(db.Integer,primary_key=True)

    username=db.Column(db.String(100),unique=True)

    password=db.Column(db.String(200))

    last_period=db.Column(db.Date)

    cycle_length=db.Column(db.Integer)

    period_duration=db.Column(db.Integer)

    height=db.Column(db.Float)

    weight=db.Column(db.Float)


class Symptoms(db.Model):

    id=db.Column(db.Integer,primary_key=True)

    user_id=db.Column(db.Integer)

    symptom_list=db.Column(db.Text)

    date_logged=db.Column(db.Date,default=date.today)


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# ------------------
# HOME
# ------------------

@app.route("/")
def index():

    return render_template("index.html")


# ------------------
# REGISTER
# ------------------

@app.route("/register",methods=['GET','POST'])
def register():

    if request.method=="POST":

        user=User(

        username=request.form['username'],

        password=generate_password_hash(request.form['password']),

        last_period=datetime.strptime(request.form['last_period'],"%Y-%m-%d").date(),

        cycle_length=int(request.form['cycle_length']),

        period_duration=int(request.form['period_duration']),

        height=float(request.form['height']),

        weight=float(request.form['weight'])

        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ------------------
# LOGIN
# ------------------

@app.route("/login",methods=['GET','POST'])
def login():

    if request.method=="POST":

        user=User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password,request.form['password']):

            login_user(user)

            return redirect("/dashboard")

    return render_template("login.html")


# ------------------
# DASHBOARD
# ------------------

@app.route("/dashboard")
@login_required
def dashboard():

    today=date.today()

    next_period=current_user.last_period+timedelta(days=current_user.cycle_length)

    ovulation=next_period-timedelta(days=14)

    fertile_start=ovulation-timedelta(days=2)

    fertile_end=ovulation+timedelta(days=2)

    days_left=(next_period-today).days

    bmi=round(current_user.weight/((current_user.height/100)**2),2)

    notification=None

    if days_left<=3:

        notification="⚠ Your period is approaching soon!"

    return render_template(

    "dashboard.html",

    next_period=next_period,

    ovulation=ovulation,

    fertile_start=fertile_start,

    fertile_end=fertile_end,

    days_left=days_left,

    bmi=bmi,

    notification=notification

    )


# ------------------
# CALENDAR
# ------------------
@app.route("/calendar")
@login_required
def calendar():

    today=date.today()

    next_period=current_user.last_period+timedelta(days=current_user.cycle_length)

    ovulation=next_period-timedelta(days=14)

    fertile_start=ovulation-timedelta(days=2)

    fertile_end=ovulation+timedelta(days=2)

    return render_template(

        "calendar.html",

        last_period=current_user.last_period,

        next_period=next_period,

        ovulation=ovulation,

        fertile_start=fertile_start,

        fertile_end=fertile_end
    )


# ------------------
# SYMPTOMS
# ------------------

@app.route("/symptoms",methods=['GET','POST'])
@login_required
def symptoms():

    if request.method=="POST":

        selected=request.form.getlist("symptoms")

        record=Symptoms(

        user_id=current_user.id,

        symptom_list=", ".join(selected)

        )

        db.session.add(record)
        db.session.commit()

        return redirect("/history")

    return render_template("symptoms.html")


# ------------------
# HISTORY
# ------------------

@app.route("/history")
@login_required
def history():

    records=Symptoms.query.filter_by(user_id=current_user.id).all()

    return render_template("history.html",records=records)


# ------------------
# ANALYTICS
# ------------------

@app.route("/analytics")
@login_required
def analytics():

    records=Symptoms.query.filter_by(user_id=current_user.id).all()

    symptom_count={}

    for r in records:

        for s in r.symptom_list.split(","):

            symptom_count[s]=symptom_count.get(s,0)+1

    labels=list(symptom_count.keys())
    values=list(symptom_count.values())

    return render_template("analytics.html",labels=labels,values=values)


# ------------------
# PCOS
# ------------------

@app.route("/pcos",methods=['GET','POST'])
@login_required
def pcos():

    bmi=round(current_user.weight/((current_user.height/100)**2),2)

    risk=None

    if request.method=="POST":

        symptoms=request.form.getlist("symptoms")

        score=len(symptoms)

        if score>=15:

            risk="High Risk"

        elif score>=8:

            risk="Moderate Risk"

        else:

            risk="Low Risk"

    return render_template("pcos.html",risk=risk,bmi=bmi)


# ------------------
# PCOD
# ------------------

@app.route("/pcod",methods=['GET','POST'])
@login_required
def pcod():

    risk=None

    if request.method=="POST":

        symptoms=request.form.getlist("symptoms")

        score=len(symptoms)

        if score>=15:

            risk="High Risk"

        elif score>=8:

            risk="Moderate Risk"

        else:

            risk="Low Risk"

    return render_template("pcod.html",risk=risk)


# ------------------
# MOOD BOOSTER
# ------------------

@app.route("/mood")
@login_required
def mood():

    jokes=[

    "Why did the uterus break up with the ovary? Too much monthly drama!",

    "Chocolate understands mood swings better than humans.",

    "Periods are like software updates — inconvenient but necessary."

    ]

    questions=[

    "Have you taken a deep breath today?",

    "Did you drink enough water today?",

    "What made you smile today?"

    ]

    return render_template("mood.html",

    joke=random.choice(jokes),

    question=random.choice(questions)

    )


# ------------------
# EXERCISE
# ------------------

@app.route("/exercise")
@login_required
def exercise():

    return render_template("exercise.html")


# ------------------
# RUN APP
# ------------------

if __name__=="__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)