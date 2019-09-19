import mistune
from bs4 import BeautifulSoup, NavigableString
import gspread
from oauth2client.service_account import ServiceAccountCredentials


markdown = mistune.Markdown()

party_to_manifesto = {
    'A': 'alianca_020919.md',
    'BE': 'be_120919.md',
    'CDS-PP': '',
    'CH': 'CHEGA.md',
    'IL': '',
    'JPP': '',
    'L': 'livre.md',
    'MAS': '',
    'NC': '',
    'PCTP/MRPP': '',
    'PCP': '',
    'MPT': '',
    'PDR': '',
    'PEV': '',
    'PNR': '',
    'PPM': '',
    'PPD/PSD': 'psd.md',
    'PS': 'PS_01092019.md',
    'PTP': '',
    'PURP': '',
    'PAN': 'pan_31082019.md',
    'RIR': '',
}


def between(cur, end):
    """ Get all html tags between two tags """
    while cur and cur != end:
        #if isinstance(cur, NavigableString):
        yield str(cur)
        cur = cur.next_sibling


def md_to_json(path):
    # read full markdown manifesto
    content = open(path, 'r').read()
    # convert markdown to html
    html = markdown(content)

    # html parser
    parsed_html = BeautifulSoup(html)
    # get all h1 tags, this should be manifesto and section headers
    all_sections = parsed_html.findAll('h1')

    def get_tags(begin, end):
        all_tags = [tag for tag in between(begin, end)]
        section_header = all_tags[0]
        section_content = all_tags[1:]
        return section_header, section_content

    manifesto_header, intro_content = between(all_sections[0], all_sections[1])

    #
    section_header, section_content = [text for text in between(all_sections[0], all_sections[1])][1:]

    ''.join(section)


    parsed_html.body.find('div', attrs={'class':'container'}).text

    return


def process_candidates(candidates, main_candidate_info, is_main):
    all_candidates = []
    for candidate in candidates.split('\n'):
        if candidate:
            s = candidate.split(' ')
            position = int(s[0][:-1] if '.' in s[0] else s[0])
            name = ' '.join(s[1:])

            c = {
                'position': position,
                'name': name,
                'type': 'main' if is_main else 'secundary',
                'is_lead_candidate': False
            }
            # add information regarding lead candidate
            if position == 1 and is_main:
                # debug purposes
                if not main_candidate_info:
                    raise RuntimeError(f'No main candidate: {candidates}')
                if name != main_candidate_info['name']:
                    raise RuntimeError(f'Name mismatch: {candidates} - "{main_candidate_info["name"]}"')

                c.update({
                    'is_lead_candidate': True,
                    'description': main_candidate_info['description'],
                    'description_source': main_candidate_info['description_source'],
                    #'photo': main_candidate_info['photo'],
                })

            all_candidates.append(c)

    return all_candidates


def get_main_candidates_info(sheet):
    worksheet = sheet.worksheet('Info sobre os candidatos')
    rows = worksheet.get_all_values()

    all_main_candidates = {}

    def clean(x):
        return '' if x == '?' else x

    for i in range(0, len(rows[0]), 6):
        district = rows[0][i]
        for row in rows[2:]:
            if row[i]:
                party = row[i]
                if party not in all_main_candidates:
                    all_main_candidates[party] = {}
                all_main_candidates[party][district] = {
                    'name': clean(row[i+1]),
                    'description': clean(row[i+3]),
                    'description_source': clean(row[i+5]),
                    # TBD
                    'photo': '', #row[i+4],
                }

    return all_main_candidates


def get_acronym(acronym):
    if acronym == 'PCP' or acronym == 'PEV':
        return 'PCP-PEV'
    return acronym


def build_cdu(path, parties):
    pcp = parties.pop('PCP')
    pev = parties.pop('PEV')

    parties['PCP-PEV'] = {
        'logo': f'{path}/cdu.png',
        'name': 'CDU - Coligação Democrática Unitária',
        'website': 'https://www.cdu.pt',
        'email': '',
        'description': f'{pcp["description"]}\n\n{pev["description"]}',
        'description_source': f'{pcp["description_source"]}\n\n{pev["description_source"]}',
        'facebook': 'https://www.facebook.com/cdupcppev',
        'twitter': 'https://www.twitter.com/cdupcppev',
        'instagram': 'https://www.instagram.com/cdupcppev',
    }

    return parties


def get_parties(path):
    scopes = ['https://spreadsheets.google.com/feeds',
              'https://www.googleapis.com/auth/drive']
    path_to_google_cred = 'google_auth.json'

    ## Connect to Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(path_to_google_cred, scopes)
    gs_con = gspread.authorize(creds)

    sheet = gs_con.open('Spreadsheet - plataforma')
    worksheet = sheet.worksheet('Lista de candidaturas')
    rows = worksheet.get_all_values()

    main_candidates_info = get_main_candidates_info(sheet)

    parties = {}
    headers = rows[1]

    # indexes 0-2 can be ignored
    for row in rows[3:]:
        # if defined is a party to load
        if row[1]:
            acronym = row[3]
            parties[acronym] = {
                'logo': f'{path}/{row[1]}',
                'name': row[2],
                'website': row[4],
                'email': row[5],
                'description': row[6],
                'description_source': row[7],
                'facebook': row[8],
                'twitter': row[9],
                'instagram': row[10],
            }

            # load candidates per district
            candidates = {}
            for i in range(13, len(row), 3):
                district = headers[i]
                # we are using get_acronym because main candidates have PCP and PEV together
                main_candidate_info = main_candidates_info[get_acronym(acronym)].get(district, {})

                candidates[district] = {}
                candidates[district]['main'] = process_candidates(row[i], main_candidate_info, True)
                candidates[district]['secundary'] = process_candidates(row[i+1], main_candidate_info, False)

            parties[acronym]['candidates'] = candidates

    # join PEV and PCP
    parties = build_cdu(path, parties)

    return parties


def update_database(folder_md, folder_logos):
    print('Loading data..')

    # TBD
    manifestos = {
        #party: md_to_json(f'{folder_md}/{md_file}')
        #for party, md_file in party_to_manifesto.items()
        #if md_file
    }

    parties = get_parties(folder_logos)

    return manifestos, parties
