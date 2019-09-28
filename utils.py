import mistune
from bs4 import BeautifulSoup, NavigableString
import gspread
from oauth2client.service_account import ServiceAccountCredentials


markdown = mistune.Markdown()

party_to_manifesto = {
    'A': 'alianca_020919.md',
    'BE': 'be_120919.md',
    'CDS-PP': 'cdspp.md',
    'CH': 'CHEGA.md',
    'IL': 'Iniciativa Liberal.md',
    'JPP': '',
    'L': 'livre.md',
    'MAS': 'mas.md',
    'NC': 'NOS_CIDADAOS_Set2019',
    'PCTP/MRPP': 'PCTP.md',
    'PCP': 'PCP.md',
    'MPT': '',
    'PDR': 'PDR_22092019.md',
    'PEV': 'pev_31082019.md',
    'PNR': 'pnr.md',
    'PPM': '',
    'PPD/PSD': 'psd.md',
    'PS': 'PS_01092019.md',
    'PTP': '',
    'PURP': '',
    'PAN': 'pan_31082019.md',
    'RIR': 'RIR',
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
    parsed_html = BeautifulSoup(html,features="html.parser")
    # get all h1 tags, this should be manifesto and section headers
    all_sections = parsed_html.findAll('h1')

    def get_tags(begin, end):
        all_tags = [tag for tag in between(begin, end)]
        section_header = all_tags[0]
        section_content = all_tags[1:]
        return section_header, section_content

    def proccess_section(begin, end):
        section_header, section_content = get_tags(begin, end)

        # find all h2 tags
        subsections_indexes = [i for i, x in enumerate(section_content) if x.startswith('<h2>')]
        if not subsections_indexes:
            # there is no h2 tag, let's try h3 tags
            subsections_indexes = [i for i, x in enumerate(section_content) if x.startswith('<h3>')]

        if subsections_indexes:
            subsections = []
            position = 1

            # can be empty
            intro = section_content[:subsections_indexes[0]]
            if not(len(intro) == 1 and intro[0].strip() == ""):
                section_intro = subsections.append({
                    'title': 'Introdução',
                    'content': process_content(section_content[:subsections_indexes[0]]),
                    'position': position,
                })
                position += 1

            # process subsections
            if len(subsections_indexes) > 1:
                for subsection_id in range(len(subsections_indexes) - 1):
                    # TODO: maybe a subsection can have an introduction
                    header = section_content[subsections_indexes[subsection_id]]
                    content = section_content[subsections_indexes[subsection_id]+1:subsections_indexes[subsection_id+1]]
                    subsections.append({
                        'title': BeautifulSoup(header, features="html.parser").text,
                        'content': process_content(content),
                        'position': position,
                    })
                    position += 1

                # process last subsection
                header = section_content[subsections_indexes[-1]]
                content = section_content[subsections_indexes[-1]+1:]
                subsections.append({
                    'title': BeautifulSoup(header, features="html.parser").text,
                    'content': process_content(content),
                    'position': position,
                })
            else:
                header = section_content[subsections_indexes[0]]
                content = section_content[subsections_indexes[0]+1:]
                subsections.append({
                    'title': BeautifulSoup(header, features="html.parser").text,
                    'content': process_content(content),
                    'position': position,
                })

            return section_header, subsections
        else:
            return section_header, process_content(section_content)

    def process_content(content):
        return [{
            'position': i+1,
            'html': x
        } for i, x in enumerate(content)]

    # json with full manifesto
    manifesto = {}

    manifesto['sections'] = []
    if len(all_sections) > 1:
        position = 1

        # get header and intro
        manifesto_header, intro_content = get_tags(all_sections[0], all_sections[1])
        manifesto['title'] = BeautifulSoup(manifesto_header, features="html.parser").text

        if not(len(intro_content) == 1 and intro_content[0].strip() == ""):
            manifesto['sections'].append({
                'title': 'Introdução',
                'content': process_content(intro_content),
                'position': position,
            })
            position += 1

        # process sections
        for section_id in range(1, len(all_sections) - 1):
            section_header, content = proccess_section(all_sections[section_id], all_sections[section_id+1])
            manifesto['sections'].append({
                'title': BeautifulSoup(section_header, features="html.parser").text,
                'content': content,
                'position': position,
            })
            position += 1

        # process last section
        section_header, section_content = proccess_section(all_sections[-1], None)
        manifesto['sections'].append({
            'title': BeautifulSoup(section_header, features="html.parser").text,
            'content': section_content,
            'position': position,
        })
    else:
        # get header and intro
        manifesto_header, content = proccess_section(all_sections[0], None)
        manifesto['title'] = BeautifulSoup(manifesto_header, features="html.parser").text

        manifesto['sections'].append({
            'title': 'Programa',
            'content': content,
            'position': 1,
        })

    return manifesto


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
                #if not main_candidate_info:
                #    raise RuntimeError(f'No main candidate: {candidates}')
                #if name != main_candidate_info['name']:
                #    raise RuntimeError(f'Name mismatch: {candidates} - "{main_candidate_info["name"]}"')

                c.update({
                    'is_lead_candidate': True,
                    'biography': main_candidate_info['biography'],
                    'biography_source': main_candidate_info['biography_source'],
                    'link_parlamento': main_candidate_info['link_parlamento'],
                    'photo': main_candidate_info['photo'],
                    'photo_source': main_candidate_info['photo_source'],
                })

            all_candidates.append(c)

    return all_candidates


def get_main_candidates_info(sheet):
    worksheet = sheet.worksheet('Info sobre os cabeças de lista')
    rows = worksheet.get_all_values()

    all_main_candidates = {}

    def clean(x):
        return '' if x == '?' else x

    for i in range(0, len(rows[0]), 9):
        district = rows[0][i]
        for row in rows[2:]:
            if row[i]:
                party = row[i]
                if party not in all_main_candidates:
                    all_main_candidates[party] = {}
                all_main_candidates[party][district] = {
                    'name': clean(row[i+1]),
                    'biography': clean(row[i+4]),
                    'link_parlamento': clean(row[i+5]),
                    'biography_source': clean(row[i+6]),
                    'photo': row[i+7],
                    'photo_source': row[i+8],
                }

    return all_main_candidates


def get_acronym(acronym):
    if acronym == 'PCP' or acronym == 'PEV':
        return 'PCP-PEV'
    return acronym


def build_cdu(parties):
    pcp = parties.pop('PCP')
    pev = parties.pop('PEV')

    parties['PCP-PEV'] = {
        'logo': 'cdu.png',
        'name': 'CDU - Coligação Democrática Unitária',
        'website': 'https://www.cdu.pt',
        'email': '',
        'description': f'PCP\n\n{pcp["description"]}\n\nPEV\n\n{pev["description"]}',
        'description_source': f'{pcp["description_source"]}\n{pev["description_source"]}',
        'facebook': 'https://www.facebook.com/cdupcppev',
        'twitter': 'https://www.twitter.com/cdupcppev',
        'instagram': 'https://www.instagram.com/cdupcppev',
    }

    # pcp and pev have same candidates in the spreadsheet
    parties['PCP-PEV']['candidates'] = pcp['candidates']

    return parties


def get_parties():
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
                'logo': row[1],
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
    parties = build_cdu(parties)

    return parties


def update_database(folder_md):
    print('Loading data..')

    manifestos = {
        party: md_to_json(f'{folder_md}/{md_file}')
        for party, md_file in party_to_manifesto.items()
        if md_file
    }

    parties = get_parties()

    print('Done!')
    return manifestos, parties
