from argparse import ArgumentParser
import json
import re

GBASE_STATS_SCAN = "const struct BaseStats gBaseStats[] ="
SPECIES_NAME_SCAN = "["
REGEX_SPECIES = r".*?\[(.*)].*"
SPECIES_START_SCAN = "{"
SPECIES_END_SCAN = "}"
FIELD_SCAN = "."
DEFINE_SCAN = "#define"

GENDER_RATIOS = {
    "MON_MALE" : 0x00,
    "MON_FEMALE" : 0xFE,
    "MON_GENDERLESS" : 0xFF
}

def to_snake_case(in_str):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', in_str) 
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() 

def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])

def parse_constant_list_field_gen(constant_namespace):
    constant_namespace += "_"
    def parse_constant_list_field(field, value, species_data):
        field = to_snake_case(field)
        values = []
        array = value[value.find('{')+1:value.find('}')]
        for it in array.split(','):
            it = it.strip()
            it = it.replace(constant_namespace, '').lower()
            values.append(it)
        species_data[field] = values
    return parse_constant_list_field

def parse_constant_field_gen(constant_namespace):
    constant_namespace += "_"
    def parse_constant_field(field, value, species_data):
        field = to_snake_case(field)
        value = value.replace(constant_namespace, '').lower()
        species_data[field] = value 
    return parse_constant_field

def gender_ratio_parser(field, value, species_data):
    field = to_snake_case(field)
    if '(' in value:
        gender_ratio = float(value[value.find('(')+1:value.find(')')])
    else:
        gender_ratio = float(GENDER_RATIOS[value])
    species_data[field] = gender_ratio

def ev_yield_parser(field, value, species_data):
    if "ev_yield" not in species_data:
        species_data["ev_yield"] = {}
    ev_yield = species_data["ev_yield"]
    field = field.replace('evYield_', '')
    field = to_snake_case(field)
    ev_yield[field] = int(value)

def base_stat_parser(field, value, species_data):
    if "base_stats" not in species_data:
        species_data["base_stats"] = {}
    base_stats = species_data["base_stats"]
    field = field.replace('base', '')
    field = to_snake_case(field)
    base_stats[field] = int(value)

def boolean_field_parser(field, value, species_data):
    field = to_snake_case(field)
    species_data[field] = value == "TRUE"

def basic_field_parser(field, value, species_data):
    field = to_snake_case(field)
    species_data[field] = int(value)

FIELD_PARSERS = {
    "baseHP" : base_stat_parser,
    "baseAttack" : base_stat_parser,
    "baseDefense" : base_stat_parser,
    "baseSpeed" : base_stat_parser,
    "baseSpAttack" : base_stat_parser,
    "baseSpDefense" : base_stat_parser,
    "type1" : parse_constant_field_gen("TYPE"),
    "type2" : parse_constant_field_gen("TYPE"),
    "catchRate" : basic_field_parser,
    "expYield" : basic_field_parser,
    "evYield_HP" : ev_yield_parser,
    "evYield_Attack" : ev_yield_parser,
    "evYield_Defense" : ev_yield_parser,
    "evYield_Speed" : ev_yield_parser,
    "evYield_SpAttack" : ev_yield_parser,
    "evYield_SpDefense" : ev_yield_parser,
    "item1" : parse_constant_field_gen("ITEM"),
    "item2" : parse_constant_field_gen("ITEM"),
    "genderRatio" : gender_ratio_parser,
    "eggCycles" : basic_field_parser,
    "friendship" : basic_field_parser,
    "growthRate" : parse_constant_field_gen("GROWTH"),
    "eggGroup1" : parse_constant_field_gen("EGG_GROUP"),
    "eggGroup2" : parse_constant_field_gen("EGG_GROUP"),
    "abilities" : parse_constant_list_field_gen("ABILITY"), # ABILITY_OVERGROW, ABILITY_NONE},
    "safariZoneFleeRate" : basic_field_parser,
    "bodyColor" : parse_constant_field_gen("BODY_COLOR"),
    "noFlip" : boolean_field_parser,
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
            current_species_name = '_'.join(raw_name.split("_")[1:]).lower()
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

BASE_STATS_H_TEMPLATE = """
// Maximum value for a female Pokémon is 254 (MON_FEMALE) which is 100% female.
// 255 (MON_GENDERLESS) is reserved for genderless Pokémon.
#define PERCENT_FEMALE(percent) min(254, ((percent * 255) / 100))

{}
{{
{}
}};
"""
SPECIES_NAME_TEMPLATE = "\t[SPECIES_{}] ="
SPECIES_NONE_TEMPLATE = "\t[SPECIES_{}] = {{0}},"
FIELD_TEMPLATE = "\t\t.{} = {},"

def fix_tabs(data):
    # Tabs are the devil.
    # Always use 4 spaces, they're a better standard
    return data.replace('\t', '    ')

def gender_ratio_formatter(field_name, value, entry):
    field_name = to_camel_case(field_name)
    if value in GENDER_RATIOS.values():
        for ikey, ivalue in GENDER_RATIOS.items():
            if ivalue == value:
                value = ikey
    else:
        if value == int(value):
            value = int(value)
        value = 'PERCENT_FEMALE({})'.format(value)
    field = FIELD_TEMPLATE.format(field_name, value)
    entry.append(field)

def constant_list_field_formatter_gen(constant_namespace):
    def constant_list_field_formatter(field_name, value, entry):
        field_name = to_camel_case(field_name)
        entry_list = []
        for list_entry in value:
            list_entry = "{}_{}".format(constant_namespace, list_entry.upper())
            entry_list.append(list_entry)
        list_field_value = '{{{}}}'.format(', '.join(entry_list))
        field = FIELD_TEMPLATE.format(field_name, list_field_value)
        entry.append(field)
    return constant_list_field_formatter

def constant_field_formatter_gen(constant_namespace):
    def constant_field_formatter(field_name, value, entry):
        field_name = to_camel_case(field_name)
        value = "{}_{}".format(constant_namespace, value.upper())
        field = FIELD_TEMPLATE.format(field_name, value)
        entry.append(field)
    return constant_field_formatter

def base_stats_formatter(field_name, value, entry):
    for stat_name, stat_value in value.items():
        if stat_name == "hp":
            full_field_name = "baseHP"
        else:
            full_field_name = "base_{}".format(stat_name)
            full_field_name = to_camel_case(full_field_name)
        base_stat_field = FIELD_TEMPLATE.format(full_field_name, stat_value)
        entry.append(base_stat_field)

def ev_yield_formatter(field_name, value, entry):
    for stat_name, stat_value in value.items():
        if stat_name == "hp":
            full_field_name = "evYield_HP"
        else:
            full_field_name = to_camel_case(stat_name)
            full_field_name = full_field_name[0].upper() + full_field_name[1:]
            full_field_name = 'evYield_{}'.format(full_field_name)
        ev_yield_field = FIELD_TEMPLATE.format(full_field_name, stat_value)
        entry.append(ev_yield_field)

def boolean_field_formatter(field_name, value, entry):
    field_name = to_camel_case(field_name)
    value = str(value).upper()
    field = FIELD_TEMPLATE.format(field_name, value)
    entry.append(field)

def basic_field_formatter(field_name, value, entry):
    field_name = to_camel_case(field_name)
    field = FIELD_TEMPLATE.format(field_name, value)
    entry.append(field)

FIELD_FORMATTERS = {
    "base_stats" : base_stats_formatter,
    "type1" : constant_field_formatter_gen("TYPE"),
    "type2" : constant_field_formatter_gen("TYPE"),
    "catch_rate" : basic_field_formatter,
    "exp_yield" : basic_field_formatter,
    "ev_yield" : ev_yield_formatter,
    "item1" : constant_field_formatter_gen("ITEM"),
    "item2" : constant_field_formatter_gen("ITEM"),
    "gender_ratio" : gender_ratio_formatter,
    "egg_cycles" : basic_field_formatter,
    "friendship" : basic_field_formatter,
    "growth_rate" : constant_field_formatter_gen("GROWTH"),
    "egg_group1" : constant_field_formatter_gen("EGG_GROUP"),
    "egg_group2" : constant_field_formatter_gen("EGG_GROUP"),
    "abilities" : constant_list_field_formatter_gen("ABILITY"),
    "safari_zone_flee_rate" : basic_field_formatter,
    "body_color" : constant_field_formatter_gen("BODY_COLOR"),
    "no_flip" : boolean_field_formatter,
}

def convert_from_json(in_json):
    base_stats_h = ""
    entries = []
    for species_name, species_data in in_json.items():
        if not species_data:
            # Handles edge case of our beloved SPECIES_NONE
            entry = SPECIES_NONE_TEMPLATE.format(species_name.upper())
            entries.append(entry)
            continue

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
            

def main():
    argparser = ArgumentParser()
    argparser.add_argument('IN_FILE')
    argparser.add_argument('OUT_FILE')
    vargs = argparser.parse_args()
    # print(vargs)

    in_json = {}
    with open(vargs.IN_FILE, 'r') as fobj:
        in_json = json.load(fobj)
    base_stats_h = convert_from_json(in_json)
    with open(vargs.OUT_FILE, 'w') as fobj:
        fobj.write(base_stats_h)

    # convert_from_json
    # out_json = {}
    # with open(vargs.IN_FILE, 'r') as fobj:
    #     out_json = convert_to_json(fobj)
    
    # with open(vargs.OUT_FILE, 'w') as fobj:
    #     json.dump(out_json, fobj, indent=4)

if __name__ == "__main__":
    main()