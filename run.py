from flask import Flask, jsonify

from utils import update_database

folder_md = '../pt-programas-legislativas-2019'
manifestos, parties = update_database(folder_md)

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/v1/manifestos", methods = ['GET'])
def get_manifestos():
    return jsonify(manifestos)

@app.route("/v1/parties", methods = ['GET'])
def get_parties():
    return jsonify(parties)
