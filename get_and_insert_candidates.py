# get candidates from https://www.legislativas2019.mai.gov.pt/candidatos.html
# and insert it into correct spreadsheet

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time


scopes = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']
path_to_google_cred = 'google_auth.json'

## Connect to Google Sheets
creds = ServiceAccountCredentials.from_json_keyfile_name(path_to_google_cred, scopes)
gs_con = gspread.authorize(creds)

sheet = gs_con.open('Spreadsheet - plataforma')
worksheet = sheet.worksheet('Lista de candidaturas')

district_to_code = {
    'Aveiro': 'LOCAL-010000',
    'Beja': 'LOCAL-020000',
    'Braga': 'LOCAL-030000',
    'Bragança': 'LOCAL-040000',
    'Castelo Branco': 'LOCAL-050000',
    'Coimbra': 'LOCAL-060000',
    'Évora': 'LOCAL-070000',
    'Faro': 'LOCAL-080000',
    'Guarda': 'LOCAL-090000',
    'Leiria': 'LOCAL-100000',
    'Lisboa': 'LOCAL-110000',
    'Portalegre': 'LOCAL-120000',
    'Porto': 'LOCAL-130000',
    'Santarém': 'LOCAL-140000',
    'Setúbal': 'LOCAL-150000',
    'Viana do Castelo': 'LOCAL-160000',
    'Vila Real': 'LOCAL-170000',
    'Viseu': 'LOCAL-180000',
    'Açores': 'LOCAL-400000',
    'Madeira': 'LOCAL-300000',
    'Europa': 'FOREIGN-800000',
    'Fora da europa': 'FOREIGN-900000',
}

def get_party(party):
    if party == 'PCP' or party == 'PEV':
        return 'PCP-PEV'
    return party.replace('/', '-')

url_template = 'https://www.legislativas2019.mai.gov.pt/static-data/candidates/PARTIES-CANDIDATES-AR-{district}-{party}-PAGE-1-ELECTED-FALSE.json'
source = 'https://www.legislativas2019.mai.gov.pt/candidatos.html'

district_order = ['Aveiro','Beja','Braga','Bragança','Castelo Branco','Coimbra','Évora','Faro','Guarda','Leiria','Lisboa','Portalegre','Porto','Santarém','Setúbal','Viana do Castelo','Vila Real','Viseu','Açores','Madeira','Europa','Fora da europa']
party_order = ['A','B.E.','CDS-PP','CH','IL','JPP','L','MAS','NC','PCTP/MRPP','PCP','MPT','PDR','PEV','PNR','PPM','PPD/PSD','PS','PTP','PURP','PAN','R.I.R.']

rows = range(4, 26)
columns = range(14, 80, 3)
for col, district in zip(columns, district_order):
    for row, party in zip(rows, party_order):
        url = url_template.format(district=district_to_code[district], party=get_party(party))

        res = requests.get(url=url).json()
        candidates = res['electionCandidates'][0]['candidates']
        if candidates:
            main_candidates = candidates[0]['effectiveCandidates']
            secundary_candidates = candidates[0]['alternateCandidates']

            main = '\n'.join([f'{i+1} {name}' for i, name in enumerate(main_candidates)])
            secundary = '\n'.join([f'{i+1} {name}' for i, name in enumerate(secundary_candidates)])

            worksheet.update_cell(row, col, main)
            worksheet.update_cell(row, col+1, secundary)
            worksheet.update_cell(row, col+2, source)

            # Avoiding quota limits https://developers.google.com/sheets/api/limits
            time.sleep(5)

print('done!')
