from flask import Flask
from flask_basicauth import BasicAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def update_database():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheet_key = app.config['PPT_CONTENT_GKEY']
    path_to_google_cred = '../host/google_auth.json'

    ## Connect to Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(path_to_google_cred, SCOPES)
    gs_con = gspread.authorize(creds)

    sh = gs_con.open_by_key(spreadsheet_key)
    worksheet = sh.worksheet("parties")
    rows = worksheet.get_all_values()

    basic_structure = []
    is_first = True
    for row in rows:
        if is_first:
             for item in row:
                 basic_structure.append(item)
             is_first = False
             continue

        counter = 0
        new_party = {}
        for item in row:
            new_party[basic_structure[counter]] = item
            counter += 1

        parties[row[0]] = new_party

    print(parties)


app = Flask(__name__)

app.config.from_pyfile('../host/conf.cfg')

parties = {}
update_database()

basic_auth = BasicAuth(app)

@app.route("/hello")
def hello():
    return "Hello World!"

@app.route("/update")
@basic_auth.required
def update_internal_data():
    update_database()
    return "Database updated"
