# get candidates from a source and insert it into our spreadsheet
# 2019:
#     from: https://www.legislativas2019.mai.gov.pt/candidatos.html
#   commit: https://github.com/Politica-Para-Todos/pARties/blob/9b447717a770be2a0a19b9e31170fd8200fe2383/get_and_insert_candidates.py
# 2022: 
#   from: https://www.cne.pt/content/eleicoes-para-assembleia-da-republica-2022
#     to: https://docs.google.com/spreadsheets/d/1G1XZS1kA4LZSxNIM1Qjpb7FUTVIE0ZgZIOHwJDlmKWI/edit#gid=0

import gspread
import pandas as pd
import time

from oauth2client.service_account import ServiceAccountCredentials
from tqdm import tqdm


# define the scope
scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name('google_auth.json', scope)

# authorize the clientsheet 
client = gspread.authorize(creds)

# open the correct spreadsheet 
# public file: https://docs.google.com/spreadsheets/d/1G1XZS1kA4LZSxNIM1Qjpb7FUTVIE0ZgZIOHwJDlmKWI/edit#gid=0
sheet = client.open_by_key("1G1XZS1kA4LZSxNIM1Qjpb7FUTVIE0ZgZIOHwJDlmKWI")
worksheet = sheet.worksheet("círculos_eleitorais")

# define order of parties and districts in the spreadsheet
district_order = ['Aveiro','Beja','Braga','Bragança','Castelo Branco','Coimbra','Évora','Faro','Guarda','Leiria','Lisboa','Portalegre','Porto','Santarém','Setúbal','Viana do Castelo','Vila Real','Viseu','Açores','Madeira','Europa','Fora da europa']

party_order = ['PPD/PSD - CDS-PP - PPM – AD/Aliança Democrática','ALIANÇA','ADN','BE','CDS/PP','PCP - PEV - CDU','CHEGA','Ergue-te','IL','JPP','LIVRE','PPD/PSD-CDS-PP - MADEIRA PRIMEIRO','MAS','Nós, Cidadãos!','PCTP/MRPP','MPT','PPM','PPD/PSD','PS','PTP','PAN','R.I.R.','Volt Portugal']

# load CSV data - extracted from CNE https://www.cne.pt/content/eleicoes-para-assembleia-da-republica-2022
# public file: https://drive.google.com/file/d/1E12qbndro-TXovELAKnJm3ISCP6W1Llv/view?usp=sharing
df = pd.read_csv("https://drive.google.com/uc?export=download&id=1E12qbndro-TXovELAKnJm3ISCP6W1Llv")

# fix data issues
df["partido"] = df["partido"].str.strip()
df["circulo"] = df["circulo"].str.strip()
df["tipo"] = df["tipo"].str.replace("efectivo", "efetivo")

# nr candidates per district
nr_candidates = {
    'Aveiro': 16,
    'Beja': 3,
    'Braga': 19,
    'Bragança': 3,
    'Castelo Branco': 4,
    'Coimbra': 9,
    'Évora': 3,
    'Faro': 9, 
    'Guarda': 3,
    'Leiria': 10,
    'Lisboa': 48,
    'Portalegre': 2,
    'Porto': 40, 
    'Santarém': 9, 
    'Setúbal': 18,
    'Viana do Castelo': 6, 
    'Vila Real': 5,
    'Viseu': 8,
    'Açores': 5, 
    'Madeira': 6,
    'Europa': 2,
    'Fora da europa': 2
}

# populate spreadsheet
rows = range(5, 28)
columns = range(13, 56, 2)

for col, district in tqdm(zip(columns, district_order), total=len(district_order)):
    for row, party in zip(rows, party_order):
        
        candidates = df[(df["partido"] == party) & (df["circulo"] == district)]
        
        if len(candidates) > 0:
            main_candidates = candidates.loc[candidates["tipo"] == "efetivo", "candidato"]
            secundary_candidates = candidates.loc[candidates["tipo"] == "suplente", "candidato"]

            # https://www.cne.pt/faq2/96/3
            # assess criterias
            if len(main_candidates) < nr_candidates[district]:
                print(f'\nParty "{party}" in district "{district}" with less main candidates that it should have.')

            if len(secundary_candidates) < 2:
                print(f'\nParty "{party}" in district "{district}" with less than 2 secundary candidates.')

            if len(secundary_candidates) > 5:
                print(f'\nParty "{party}" in district "{district}" with more than 5 secundary candidates.')
                
            if len(secundary_candidates) > len(main_candidates):
                print(f'\nParty "{party}" in district "{district}" with more secundary candidates than main candidates.')

            main = '\n'.join([f'{i+1}. {name}' for i, name in enumerate(main_candidates.values)])
            secundary = '\n'.join([f'{i+1}. {name}' for i, name in enumerate(secundary_candidates.values)])

            worksheet.update_cell(row, col, main)
            worksheet.update_cell(row, col+1, secundary)

            # Avoiding quota limits https://developers.google.com/sheets/api/limits
            time.sleep(2)

print('done!')
