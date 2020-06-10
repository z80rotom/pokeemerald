from argparse import ArgumentParser
import json
import re

GBASE_STATS_SCAN = "const struct BattleMove gBattleMoves[MOVES_COUNT] ="
SPECIES_NAME_SCAN = "["
REGEX_SPECIES = r".*?\[(.*)].*"
SPECIES_START_SCAN = "{"
SPECIES_END_SCAN = "}"
FIELD_SCAN = "."
DEFINE_SCAN = "#define"

def to_snake_case(in_str):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', in_str) 
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() 

def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])

def flags_field_parser(field, value, species_data):
    field = to_snake_case(field)
    flags = []
    if value != "0":
        flags = [flag.strip() for flag in value.split('|')]
    species_data[field] = flags

def basic_field_parser(field, value, species_data):
    field = to_snake_case(field)
    species_data[field] = value

def int_field_parser(field, value, species_data):
    field = to_snake_case(field)
    species_data[field] = int(value)

FIELD_PARSERS = {
    "effect" : basic_field_parser,
    "power" : int_field_parser,
    "type" : basic_field_parser,
    "accuracy" : int_field_parser,
    "pp" : int_field_parser,
    "secondaryEffectChance" : int_field_parser,
    "target" : basic_field_parser,
    "priority" : int_field_parser,
    "flags" : flags_field_parser,
}

def convert_to_json(fobj):
    fdata = fobj.read()

    species_data = {}

    gbase_stats = False
    in_species = False
    in_define = False
    current_define_name = None
    current_define_data = None
    current_species_name = None
    current_species_data = None
    last_species_name = None
    last_species_data = None
    defines = {}
    for i, line in enumerate(fdata.split('\n')):
        line = line.strip()
        if line.startswith(GBASE_STATS_SCAN):
            gbase_stats = True
        
        if line.startswith(DEFINE_SCAN):
            define_name = line.split(DEFINE_SCAN)[1]
            if "(" in define_name:
                continue
            in_define = True
            current_define_name = define_name.replace('\\', '').strip()
            current_define_data = {}

        if not gbase_stats and not in_define:
            continue

        if line.startswith(SPECIES_NAME_SCAN):
            # Retrieve from inside of square brackets
            match = re.findall(REGEX_SPECIES, line)
            raw_name = match[0]
            # Remove leading SPECIES_ and lower for simplicity
            last_species_name = current_species_name
            last_species_data = current_species_data
            current_species_name = raw_name # '_'.join(raw_name.split("_")[1:]).lower()
            current_species_data = {}
        
            if not line.endswith(" ="):
                # Need to insert the last species processed
                if last_species_name is not None and \
                   last_species_name not in species_data:
                    species_data[last_species_name] = last_species_data
                define_name = line.split('] = ')[-1].replace(',', '')
                if define_name not in defines:
                    # If not in defines then probably None.
                    # Should probably do a hard check against {0}
                    # but I'm too lazy and it's already 10 PM
                    species_data[current_species_name] = {}
                    current_species_name = None
                    current_species_data = None
                    continue
                current_define_data = defines[define_name]
                species_data[current_species_name] = defines[define_name]

        if line.startswith(SPECIES_START_SCAN):
            # Special case of first entry
            if last_species_name is not None and \
               last_species_name not in species_data:
                species_data[last_species_name] = last_species_data
            in_species = True

        if line.startswith(SPECIES_END_SCAN):
            in_species = False
            if in_define:
                defines[current_define_name] = current_define_data
            in_define = False
            # Don't really need this with the edge case check.
            # species_data[current_species_name] = current_species_data

        if in_species and line.startswith(FIELD_SCAN):
            # Make copy so nothing in future would be affected by change
            field_line = line
            # Get rid of the extra parts for a define
            field_line = field_line.replace('\\', '').strip()
            # Always want to replace scan value so we don't factor that in 
            # as part of the field name.
            # And cut off the end comma
            field_line = field_line[1:-1]
            field, value = field_line.split('=')
            field = field.strip()
            value = value.strip()

            # if field in FIELD_PARSERS:
            field_parser = FIELD_PARSERS[field]
            if in_define:
                field_parser(field, value, current_define_data)
            else:
                field_parser(field, value, current_species_data)
            # TODO: Make it so that we capture any unknown fields

    # Catch the last one, even if Chimecho isn't worth it...
    if current_species_name is not None and \
       current_species_data is not None:
       species_data[current_species_name] = current_species_data

    return species_data

BASE_STATS_H_TEMPLATE = """{}
{{
{}
}};
"""
SPECIES_NAME_TEMPLATE = "\t[{}] ="
SPECIES_NONE_TEMPLATE = "\t[SPECIES_{}] = {{0}},"
FIELD_TEMPLATE = "\t\t.{} = {},"

def fix_tabs(data):
    # Tabs are the devil.
    # Always use 4 spaces, they're a better standard
    return data.replace('\t', '    ')

def flags_field_formatter(field_name, value, entry):
    field_name = to_camel_case(field_name)
    if value == []:
        flags = 0
    else:
        flags = " | ".join(value)

    field = FIELD_TEMPLATE.format(field_name, flags)
    entry.append(field)

def basic_field_formatter(field_name, value, entry):
    field_name = to_camel_case(field_name)
    field = FIELD_TEMPLATE.format(field_name, value)
    entry.append(field)

FIELD_FORMATTERS = {
    "effect" : basic_field_formatter,
    "power" : basic_field_formatter,
    "type" : basic_field_formatter,
    "accuracy" : basic_field_formatter,
    "pp" : basic_field_formatter,
    "secondary_effect_chance" : basic_field_formatter,
    "target" : basic_field_formatter,
    "priority" : basic_field_formatter,
    "flags" : flags_field_formatter,
}

def convert_from_json(in_json):
    base_stats_h = ""
    entries = []
    for species_name, species_data in in_json.items():
        # if not species_data:
        #     # Handles edge case of our beloved SPECIES_NONE
        #     entry = SPECIES_NONE_TEMPLATE.format(species_name.upper())
        #     entries.append(entry)
        #     continue

        entry = [SPECIES_NAME_TEMPLATE.format(species_name.upper())]
        entry.append('\t{}'.format(SPECIES_START_SCAN))
        for field_name, value in species_data.items():
            if field_name in FIELD_FORMATTERS:
                formatter = FIELD_FORMATTERS[field_name]
                formatter(field_name, value, entry)
        entry.append('\t{},'.format(SPECIES_END_SCAN))
        entries.append('\n'.join(entry))
    base_stats_h = BASE_STATS_H_TEMPLATE.format(
        GBASE_STATS_SCAN,
        '\n\n'.join(entries)
    )
    return fix_tabs(base_stats_h)

def build_battlemoves(battle_moves_json_fpath, battle_moves_h_fpath):
    in_json = {}
    with open(battle_moves_json_fpath, 'r') as fobj:
        in_json = json.load(fobj)
    battle_moves_h = convert_from_json(in_json)
    with open(battle_moves_h_fpath, 'w') as fobj:
        fobj.write(battle_moves_h)