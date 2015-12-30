import sqlite3
from flask import Flask, jsonify
from flask import request
from config import DEBUG

app = Flask(__name__)
app.debug = DEBUG
app.config.from_pyfile("config.py")


@app.route("/", methods=['GET'])
def frontPage():
    return "front page"


@app.route("/register", methods=['POST'])
def register():
    # check mailbox, phone number
    # insert data into database
    username = request.form["username"]
    password = request.form["password"]
    phoneNum = request.form["phoneNum"]
    mailbox = request.form["mailbox"]
    QQ = request.form["QQ"]
    location = request.form["location"]
    school = request.form["school"]



    return jsonify(stat=1, username=username, password=password)


@app.route("/login", methods=['PUT'])
def login():
    # find user account
    # check password

    account = request.form["account"]
    password = request.form["password"]
    return jsonify(stat=1, account=account, password=password)


def db_connect():
    return sqlite3.connect(app.config["DATABASE"])

if __name__ == "__main__":
    app.run()
