import re
import json

SCAN_TEXT_START = "const u8 g"
SCAN_TEXT_END = "PokedexText[] = _("
SCAN_TEXT_DELIM_END = ');'

POKEDEX_TEXT_TEMPLATE = """{}{}{}
{}");"""

def to_snake_case(in_str):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', in_str) 
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() 

def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].capitalize() + ''.join(x.title() for x in components[1:])

def fix_tabs(in_str):
    return in_str.replace('\t', '    ')

def to_json(fobj):
    # Fix pokedex_text.json to use SPECIES_NONE instead of SPECIES_DUMMY
    out_json = {}
    data = fobj.read()
    lines = data.split('\n')

    in_text_sector = False
    current_species_name = None
    current_text_lines = None
    for line in lines:
        line = line.strip()
        if line.startswith(SCAN_TEXT_START) and \
           line.endswith(SCAN_TEXT_END):
            current_species_name = line
            current_species_name = current_species_name.replace(SCAN_TEXT_START, '')
            current_species_name = current_species_name.replace(SCAN_TEXT_END, '')
            current_species_name = to_snake_case(current_species_name).upper()
            current_species_name = "SPECIES_{}".format(current_species_name)
            current_text_lines = []
            in_text_sector = True
            continue 
        
        if in_text_sector and line.endswith(SCAN_TEXT_DELIM_END):
            in_text_sector = False
            line = line.replace(SCAN_TEXT_DELIM_END, '')
            line = line.replace('"', '')
            current_text_lines.append(line)
            out_json[current_species_name] = ''.join(current_text_lines)
            continue
        
        if in_text_sector:
            line = line.replace('"', '')
            current_text_lines.append(line)
            continue
    return out_json

def from_json(in_json):
    species_entries = []
    for species_name, pokedex_text in in_json.items():
        species_name = to_camel_case(species_name.replace('SPECIES_', ''))
        pokedex_text = pokedex_text.split('\\n')
        pokedex_text = map(
            lambda elem: '\t"{}'.format(elem),
            pokedex_text
        )
        pokedex_text = '\\n"\n'.join(pokedex_text)
        species_entries.append(
            POKEDEX_TEXT_TEMPLATE.format(
                SCAN_TEXT_START, 
                species_name,
                SCAN_TEXT_END,
                pokedex_text
            )
        )
    return fix_tabs("\n\n".join(species_entries))

def build_pokedex_text(pokedex_text_json_fpath, pokedex_text_h_fpath):
    in_json = {}
    with open(pokedex_text_json_fpath, "r") as fobj:
        in_json = json.load(fobj)
    pokedex_text_h = from_json(in_json)
    with open(pokedex_text_h_fpath, "w") as fobj:
        fobj.write(pokedex_text_h)