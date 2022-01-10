from flask import Flask, jsonify

from utils import prepare_data

folder_md = '/app/manifestos'
manifestos, parties = prepare_data(folder_md)


app = Flask(__name__)


@app.route("/manifestos", methods = ['GET'])
def get_manifestos():
    return jsonify(manifestos)

@app.route("/parties", methods = ['GET'])
def get_parties():
    return jsonify(parties)

@app.route("/all", methods = ['GET'])
def get_all():
    return jsonify({
        'parties': parties,
        'manifestos': manifestos
    })
