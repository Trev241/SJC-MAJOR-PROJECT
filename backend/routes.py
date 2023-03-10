from app import app, db
from flask import jsonify, request, make_response
from flask_jwt_extended import create_access_token
from models import (
    Country,
    country_schema,
    countries_schema,
    EconomicIndicator,
    eco_indicator_schema,
    eco_indicators_schema,
    CountryIndicatorValue,
    country_val_schema,
    country_vals_schema,
    User,
    user_schema,
    users_schema,
    UserType
)
from sqlalchemy.exc import NoResultFound
from predictions.forecaster import Forecaster
from middleware import isNotAuth, isAuth
import json

import bcrypt
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils import sendMail

@app.route('/country', methods=['GET'])
def get_countries():
    countries = Country.query.all()
    result = countries_schema.dump(countries)

    return jsonify({'status': 200, 'countries': jsonify(result).json})

@app.route('/country/<iso_alpha_3_code>', methods=['GET'])
def get_country(iso_alpha_3_code):
    country = Country.query.filter_by(iso_alpha_3_code=iso_alpha_3_code.upper()).one()
    
    return jsonify({'status': 200, 'country': country_schema.jsonify(country).json}) 

@app.route('/indicator', methods=['GET'])
def get_indicators():
    indicators = EconomicIndicator.query.all()
    result = eco_indicators_schema.dump(indicators)

    return jsonify(result), 200

@app.route('/indicator/<short_name>', methods=['GET'])
def get_indicator(short_name):
    indicator = EconomicIndicator.query.filter_by(short_name=short_name).one()

    return eco_indicator_schema.jsonify(indicator), 200

@app.route('/indicator/add', methods=['POST'])
@isAuth()
def add_indicator():
    new_indicator = EconomicIndicator(
        name=request.json.get('name', None),
        short_name=request.json.get('short_name', None),
        description=request.json.get('description', None)
    )

    db.session.add(new_indicator)
    db.session.commit()

    return eco_indicator_schema.jsonify(new_indicator), 200

@app.route('/indicator/update/<id>', methods=['PUT'])
@isAuth()
def update_indicator(id):
    indicator = EconomicIndicator.query.get(int(id))

    indicator.name = request.json.get('name', None)
    indicator.short_name = request.json.get('short_name', None)
    indicator.description = request.json.get('description', None)

    db.session.commit()

    return eco_indicator_schema.jsonify(indicator), 200

@app.route('/indicator/<id>', methods=['DELETE'])
@isAuth()
def delete_indicator(id):
    indicator = EconomicIndicator.query.get(int(id))
    db.session.delete(indicator)
    db.session.commit()

    return eco_indicator_schema.jsonify(indicator), 200

@app.route('/value/<iso_alpha_3_code>', methods=['GET'])
@isAuth()
def get_values(iso_alpha_3_code):
    id = Country.query.filter_by(iso_alpha_3_code=iso_alpha_3_code).one().id
    values = CountryIndicatorValue.query.filter_by(country_id=id).all()
    result = country_vals_schema.dump(values)

    return jsonify(result), 200

@app.route('/value/add', methods=['POST'])
@isAuth()
def add_value():
    new_value = CountryIndicatorValue(
        country_id=request.json.get('country_id', None), 
        indicator_id=request.json.get('indicator_id', None), 
        year=request.json.get('year', None), 
        value=request.json.get('value', None)
    )

    db.session.add(new_value)
    db.session.commit()

    return country_val_schema.jsonify(new_value), 200

@app.route('/value/update/<id>', methods=['PUT'])
@isAuth()
def update_value(id):
    entry = CountryIndicatorValue.query.get(int(id))

    entry.country_id = request.json.get('country_id', None)
    entry.indicator_id = request.json.get('indicator_id', None)
    entry.year = request.json.get('year', None)
    entry.value = request.json.get('value', None)

    db.session.commit()

    return country_val_schema.jsonify(entry), 200

@app.route('/value/<id>', methods=['DELETE'])
@isAuth()
def delete_value(id):
    entry = CountryIndicatorValue.query.get(int(id))
    db.session.delete(entry)
    db.session.commit()

    return country_val_schema.jsonify(entry), 200

@app.route('/auth/signin', methods=['POST'])
@isNotAuth()
def login():
    kwargs = {}

    nameOrEmail = request.json.get('nameOrEmail', "")
    password = request.json.get('password', "")

    errors = {}
    if len(nameOrEmail.strip()) == 0:
        errors['nameOrEmail'] = 'Name/Email must not be empty!'
    if len(password.strip()) < 8:
        errors['password'] = 'Password length must be >= 8!'
    if json.dumps(errors) != "{}":
        return jsonify({"status": 403, "errors": errors})
    
    emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.fullmatch(emailRegex, nameOrEmail):
        kwargs['email'] = nameOrEmail
    else:
        kwargs['username'] = nameOrEmail

    try:
        user = User.query.filter_by(**kwargs).one()
        if not bcrypt.checkpw(password.encode('utf-8'), user.password):
            raise Exception("Wrong credentials!")
        if not user.accepted:
            raise Exception("Admin hasn't accepted your request yet, try again later!")

        token = create_access_token(identity=user.id, expires_delta=False)
        response = make_response(jsonify({'user': user_schema.jsonify(user).json,
            'status': 200}))
        response.set_cookie('token', token, 60 * 60 * 24 * 7)
        return response
        
    except Exception as e:
        print(e)
        return jsonify({
            'status': 401,
            'message': str(e)
        })

@app.route('/auth/signup', methods=['POST'])
@isNotAuth()
def create_user():
    email=request.json.get('email', "")
    username=request.json.get('username', "")
    password=request.json.get('password', "")

    errors = {}
    if len(username.strip()) == 0:
        errors['username'] = 'Username must not be empty!'
    if not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email.strip()):
        errors['email'] = 'Email must be an actual email!'
    if len(password.strip()) < 8:
        errors['password'] = 'Password length must be >= 8!'
    if json.dumps(errors) != "{}":
        return jsonify({"status": 403, "errors": errors})

    user = User(email=email, username=username,
        password=bcrypt.hashpw(password.encode('utf-8'),
            bcrypt.gensalt(12)),
    )

    db.session.add(user)
    db.session.commit()

    admins = User.query.filter_by(type=UserType.ADMINISTRATOR)

    for admin in admins:
        body = f'''
            <p>Hello <b>ADMIN @{admin.username}</b>, a new user has signed up, visit the dashboard to accept/reject the user!</p>
            <span>DASHBOARD: <a href="http://localhost:3000/dashboard">http://localhost:3000/dashboard</a></span>
            <br />
            <span>MEMBER: <b>@{user.username}</b></span>
        '''
        sendMail(admin.email, 'user registration alert!', body)
    return jsonify({'status': 200})

@app.route('/auth/logout', methods=['POST'])
@isAuth()
def logout_user():
    response = make_response(jsonify({'status': 200}))
    response.set_cookie('token', '', 0)
    return response

@app.route('/auth/user', methods=['GET'])
@isAuth()
def get_user():
    user = User.query.get(request.uid)
    return jsonify({'status': 200, 'user': user_schema.jsonify(user).json})

@app.route('/users/<accepted>', methods=['GET'])
@isAuth()
def get_users(accepted):
    users = []
    if int(accepted) == 0:
        users = User.query.filter(User.accepted == False and User.id != request.uid).all()
    else:
        users = User.query.filter(User.accepted == True).all()
    users = users_schema.dump(users)
    return jsonify({'status': 200, 'users': jsonify(users).json})

@app.route('/user/confirm', methods=['POST'])
@isAuth()
def confirm_signup():
    uid = int(request.json.get('uid', "0"))
    user = User.query.get(uid)
    if int(request.json.get('accept')) == 1:
        user.accepted = True
        body = f'''
            <p>Welcome <b>@{user.username}</b>, you are officially a MEMBER of the WORLD INCOME!</p>
            <span>Login: <a href="http://localhost:3000/login">http://localhost:3000/login</a></span>
        '''
        sendMail(user.email, 'user acceptance alert!', body)
    else:
        User.query.filter(User.id == uid).delete()
        body = f'''
            <p>Hello <b>@{user.username}</b>, the admin has rejected your registration!</p>
        '''
        sendMail(user.email, 'user acceptance alert!', body)

    db.session.commit()
    return jsonify({'status': 200})
        
@app.route('/user/promote/<uid>/<promote>', methods=['POST'])
def promote_user(uid, promote):
    user = User.query.get(int(uid))
    types = list(UserType)
    if int(promote) == 1:
        user.type = types[types.index(user.type) - 1].value
    else:
        user.type = types[types.index(user.type) + 1].value

    db.session.commit()
    return jsonify({'status': 200, 'type': user.type})

@app.route('/prediction', methods=['POST'])
@isAuth()
def fetch_predictions():
    iso_alpha_3_code = request.json.get('iso_alpha_3_code', None)
    indicator_short_name = request.json.get('indicator_short_name', None)
    years = request.json.get('years', None)

    try:
        country_id = Country.query.filter_by(iso_alpha_3_code=iso_alpha_3_code).one().id
        indicator_id = EconomicIndicator.query.filter_by(short_name=indicator_short_name).one().id
        
        forecaster = Forecaster()
        result = forecaster.predict(country_id, indicator_id, years)

        return jsonify(result), 200
    except NoResultFound:
        return jsonify({'message': f'The country code or indicator short name specified does not exist.'}), 422
