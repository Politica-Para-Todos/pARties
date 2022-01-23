import mistune
import gspread

from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials


# define the scope
scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name('google_auth.json', scope)

# authorize the clientsheet 
client = gspread.authorize(creds)

# open the correct spreadsheet 
# public file: https://docs.google.com/spreadsheets/d/1G1XZS1kA4LZSxNIM1Qjpb7FUTVIE0ZgZIOHwJDlmKWI/edit#gid=0
sheet = client.open_by_key("1G1XZS1kA4LZSxNIM1Qjpb7FUTVIE0ZgZIOHwJDlmKWI")


party_to_manifesto = {
    'PPD/PSD.CDS-PP.PPM': '',
    'A': '',
    'ADN': 'ADN_31122021.md',
    'BE': 'BE_31122021.md',
    'CDS-PP': 'CDS_10012022.md',
    'PCP-PEV': 'CDU_04012022.md',
    'CH': 'CHEGA_29122021.md',
    'E': 'Ergue-te_15012022.md',
    'IL': 'IL_20220117.md',
    'JPP': 'JPP_20012022.md',
    'L': 'LIVRE_30122021.md',
    'PPD/PSD.CDS-PP': '',
    'MAS': 'MAS_29122021.md',
    'NC': 'NC_19012022.md',
    'PCTP/MRPP': '',
    'MPT': 'MPT_11012022.md',
    'PPM': '',
    'PPD/PSD': 'PSD_09012022.md',
    'PS': 'PS_20220107.md',
    'PTP': '',
    'PAN': 'PAN_20220120.md',
    'RIR': 'RIR_20220105.md',
    'VP': 'VP_20211229.md'
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
    html = mistune.html(content)

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
                subsections.append({
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
    for candidate in candidates.strip().split('\n'):
        if candidate:
            s = candidate.split('.')
            position = int(s[0])
            name = s[1].strip()

            c = {
                'position': position,
                'name': name,
                'type': 'main' if is_main else 'secundary',
                'is_lead_candidate': False
            }
            
            # add information regarding lead candidate
            if position == 1 and is_main:
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


def get_main_candidates_info():
    worksheet = sheet.worksheet('cabeca_de_lista')
    rows = worksheet.get_all_values()

    all_main_candidates = {}

    def clean(url):
        return '' if (url.strip() == '-') or (url.strip() == 'Partido') else url

    # rows 1-3 can be ignored
    # cols 1-2 can be ignored
    for col in range(2, len(rows[0]), 6):
        district = rows[1][col].strip()
        for row in rows[3:26]:
            party = row[1].strip()
            
            if party not in all_main_candidates:
                all_main_candidates[party] = {}
            
            all_main_candidates[party][district] = {
                'name': row[col],
                'biography': row[col+1],
                'biography_source': clean(row[col+2]),
                'link_parlamento': clean(row[col+3]),
                'photo': row[col+4],
                'photo_source': row[col+5]
            }

    return all_main_candidates


def get_parties():
    # get main candidates info
    main_candidates_info = get_main_candidates_info()
    
    # get all remaining candidate info
    worksheet = sheet.worksheet("círculos_eleitorais")
    rows = worksheet.get_all_values()

    parties = {}
    headers = rows[2]

    # rows 1-4 can be ignored
    # cols 1 can be ignored
    for row in rows[4:27]:
        acronym = row[3].strip()
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
            'manifesto_source': row[11],
            'manifesto_source_backup_ppt': row[12]
        }

        # load candidates per district
        candidates = {}
        for col in range(13, len(row), 2):
            district = headers[col].strip()
            main_candidate_info = main_candidates_info[acronym].get(district, {})

            candidates[district] = {}
            candidates[district]['main'] = process_candidates(row[col], main_candidate_info, True)
            candidates[district]['secundary'] = process_candidates(row[col+1], None, False)

        parties[acronym]['candidates'] = candidates
    
    return parties


def prepare_data(folder_md):
    print('Loading data..')

    manifestos = {
        party: md_to_json(f'{folder_md}/{md_file}')
        for party, md_file in party_to_manifesto.items()
        if md_file
    }

    parties = get_parties()

    print('Done!')
    return manifestos, parties
