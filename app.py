import random
from flask import Flask, flash, render_template, request, session, redirect, url_for,jsonify
from flask_cors import cross_origin
from flask_mail import *
import sklearn
import os
import logging
import json
import pickle
import pandas as pd
import sqlite3
app = Flask(__name__)
model = pickle.load(open("flight_rf.pkl", "rb"))
app.secret_key = os.urandom(24)
con = sqlite3.connect('users.db')
con.execute('create table if not exists customer(pid integer primary key,name text,email text, password text)')
con.close()


@app.route('/')
@cross_origin()
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
@cross_origin()
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            con = sqlite3.connect("users.db")
            cur = con.cursor()
            cur.execute("insert into customer(name,email,password)values(?,?,?)", (name, email, password))
            con.commit()
            flash("Record Added  Successfully", "success")
        except:
            flash("Error in Insert Operation", "danger")
        finally:
            return redirect(url_for("login"))
            con.close()
    return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
@cross_origin()
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        con = sqlite3.connect("users.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("select * from customer where email=? and password=?", (email, password))
        data = cur.fetchone()

        if data:
            session["email"] = data["email"]
            session["password"] = data["password"]
            return redirect("predict")
        else:
            flash("Username and Password Mismatch", "danger")
    return render_template('login.html')


@app.route('/predict', methods=['GET', 'POST'])
@cross_origin()
def predict():
    if request.method == "POST":
        # Departure Time
        date_dep = request.form.get("Dep_Time")
        Journey_day = int(pd.to_datetime(date_dep, format="%Y-%m-%dT%H:%M").day)
        Journey_month = int(pd.to_datetime(date_dep, format="%Y-%m-%dT%H:%M").month)
        Dep_hour = int(pd.to_datetime(date_dep, format="%Y-%m-%dT%H:%M").hour)
        Dep_min = int(pd.to_datetime(date_dep, format="%Y-%m-%dT%H:%M").minute)

        # Arrival Time
        date_arr = request.form.get("Arrival_Time")
        Arrival_hour = int(pd.to_datetime(date_arr, format="%Y-%m-%dT%H:%M").hour)
        Arrival_min = int(pd.to_datetime(date_arr, format="%Y-%m-%dT%H:%M").minute)
        dur_hour = abs(Arrival_hour - Dep_hour)
        dur_min = abs(Arrival_min - Dep_min)

        # Stops
        Total_stops = int(request.form.get("stops"))

        # Adults
        adults = int(request.form.get('Adults'))
        children = int(request.form.get('Children'))
        infants = int(request.form.get('Infants'))

        # Airline
        airline = request.form.get('Airline')
        if airline == 'Jet Airways':
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 0
            Jet_Airways = 1
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 0

        elif airline == 'IndiGo':
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 1
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 0


        elif airline == 'Air Asia':
            Air_India = 0
            Air_Asia = 1
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 0
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 0

        elif airline == 'Air India':
            Air_India = 1
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 1
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 0

        elif airline == 'Air India Alliance Air':
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 1
            GoAir = 0
            IndiGo = 1
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 0

        elif airline == 'SpiceJet':
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 0
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 1
            Vistara = 0
            Vistara_Premium_economy = 0

        elif airline == 'Vistara':
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 0
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 1
            Vistara_Premium_economy = 0

        elif airline == 'Vistara Premium economy ':
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 0
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 1

        elif airline == 'Kingfisher':
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 0
            Jet_Airways = 0
            Kingfisher = 1
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 0

        else:
            Air_India = 0
            Air_Asia = 0
            Air_India_Alliance_Air = 0
            GoAir = 0
            IndiGo = 0
            Jet_Airways = 0
            Kingfisher = 0
            SpiceJet = 0
            Vistara = 0
            Vistara_Premium_economy = 0

        # Source
        Source = request.form.get("Source")
        if Source == 'NewDelhi':
            s_Delhi = 1
            s_Banglore = 0
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 0

        elif Source == 'Kolkata':
            s_Delhi = 0
            s_Banglore = 0
            s_Kolkata = 1
            s_Mumbai = 0
            s_Chennai = 0

        elif Source == 'Mumbai':
            s_Delhi = 0
            s_Banglore = 0
            s_Kolkata = 0
            s_Mumbai = 1
            s_Chennai = 0

        elif Source == 'Chennai':
            s_Delhi = 0
            s_Banglore = 0
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 1

        elif Source == 'Banglore':
            s_Delhi = 0
            s_Banglore = 1
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 0

        else:
            s_Delhi = 0
            s_Banglore = 0
            s_Kolkata = 0
            s_Mumbai = 0
            s_Chennai = 0

        # Destination
        Desti = request.form.get("Destination")
        if Desti == 'Cochin':
            d_Cochin = 1
            d_Chennai = 0
            d_Kolkata = 0
            d_Banglore = 0
            d_Delhi = 0
            d_Goa = 0
            d_Hyderabad = 0

        elif Desti == 'Goa':
            d_Cochin = 0
            d_Goa = 1
            d_Hyderabad = 0
            d_Chennai = 0
            d_Kolkata = 0
            d_Banglore = 0
            d_Delhi = 0


        elif Desti == 'Hyderabad':
            d_Cochin = 0
            d_Chennai = 0
            d_Kolkata = 0
            d_Banglore = 0
            d_Delhi = 0
            d_Goa = 0
            d_Hyderabad = 1

        elif Desti == 'Banglore':
            d_Cochin = 0
            d_Chennai = 0
            d_Kolkata = 0
            d_Banglore = 1
            d_Delhi = 0
            d_Goa = 0
            d_Hyderabad = 0

        elif Desti == 'New Delhi':
            d_Cochin = 0
            d_Chennai = 0
            d_Kolkata = 0
            d_Banglore = 0
            d_Delhi = 1
            d_Goa = 0
            d_Hyderabad = 0

        elif Desti == 'Kolkata':
            d_Cochin = 0
            d_Chennai = 0
            d_Kolkata = 1
            d_Banglore = 0
            d_Delhi = 0
            d_Goa = 0
            d_Hyderabad = 0

        elif Desti == 'Chennai':
            d_Cochin = 0
            d_Chennai = 1
            d_Kolkata = 0
            d_Banglore = 0
            d_Delhi = 0
            d_Goa = 0
            d_Hyderabad = 0

        else:
            d_Cochin = 0
            d_Goa = 0
            d_Hyderabad = 0
            d_Chennai = 0
            d_Kolkata = 0
            d_Banglore = 0
            d_Delhi = 0

        journey = request.form.get("Journey")
        if journey == 'Roundtrip':
            roundtrip = 1
            oneway = 0

        if journey == 'OneWay':
            roundtrip = 0
            oneway = 1

        else:
            roundtrip = 0
            oneway = 0

        prediction = model.predict([[
            Total_stops,
            Journey_day,
            Journey_month,
            Dep_hour,
            Dep_min,
            dur_min,
            dur_hour,
            Air_India,
            Air_Asia,
            Air_India_Alliance_Air,
            GoAir,
            IndiGo,
            Jet_Airways,
            Kingfisher,
            SpiceJet,
            Vistara,
            Vistara_Premium_economy,
            s_Delhi,
            s_Banglore,
            s_Kolkata,
            s_Mumbai,
            s_Chennai,
            d_Cochin,
            d_Goa,
            d_Delhi,
            d_Chennai,
            d_Hyderabad,
            d_Kolkata,
            d_Banglore,
            roundtrip,
            oneway,
            adults,
            children,
            infants
        ]])
        if date_dep == date_arr:
            logging.warning('date time of departure and date time of arrival are same')
            return render_template('predict.html', prediction_text="Your Flight price is ₹: 0")
        else:
            logging.info('Successful Prediction')
            output = round(prediction[0], 2)
            logging.info('Output Displayed')

        return render_template('predict.html', prediction_text="Your Flight price is ₹: {}".format(output))
    return render_template('predict.html')


@app.route('/logout')
@cross_origin()
def logout():
    session.clear()
    return redirect(url_for("index"))




if __name__ == '__main__':
    app.debug = True
    app.run()
