import os
from server import app
from flask import request, jsonify
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
f = Fernet(SECRET_KEY)


@app.route('/api/v1/auth/login/', methods=['POST'])
def login():
    user, passwd = request.form['user'], request.form['password']

    # check if user exists in db
    # if not, create user
    # if exists, return error

    # encrypt password
    passwd = f.encrypt(passwd.encode('utf-8'))

    # save user to db
    return jsonify({'message': 'success', 'code': 200})


@app.route('/api/v1/auth/register', methods=['POST'])
def register():

    print(request.json)

    return jsonify({'message': 'registro exitoso', 'code': 200})