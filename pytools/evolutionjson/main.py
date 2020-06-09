from argparse import ArgumentParser
import re
import json

SCAN_EVOS = "const struct Evolution gEvolutionTable[NUM_SPECIES][EVOS_PER_MON] ="
SCAN_ARRAY_START = "{"
SCAN_ARRAY_END = "};"
EVOLUTION_H_TEMPLATE = """const struct Evolution gEvolutionTable[NUM_SPECIES][EVOS_PER_MON] =
{{
{}
}};"""

FILL_SPECIES_NAME_LEN = 21

def fix_tabs(in_str):
    return in_str.replace('\t', '    ')

def rindex(iterable, element):
    return len(iterable) - iterable[::-1].index(element[::-1]) - len(element)

def in_between(iterable, start, end):
    return iterable[iterable.index(start) + len(start): rindex(iterable, end)]

def convert_sections(in_lines):
    out_lines = []

    lines = []
    in_evos = False
    in_array = False
    for line in in_lines:
        line = line.strip()
        if line.startswith(SCAN_EVOS):
            in_evos = True
            continue

        # Need to double check we're not in array so we don't mistake 
        # an evolution entry as an outer array scan token
        if in_evos and not in_array and line.startswith(SCAN_ARRAY_START):
            in_array = True
            continue

        if not in_array:
            continue

        if line.startswith(SCAN_ARRAY_END):
            in_array = False
            in_evos = False
            break
        lines.append(line)
    return '\n'.join(lines)

def evo_item_parser(evolution):
    evo_type = evolution[0].replace("EVO_", '').lower()
    evo_item = evolution[1].replace("ITEM_", '').lower()
    evo_species = evolution[2].replace("SPECIES_", '').lower()

    return {
        "type" : evo_type,
        "item" : evo_item,
        "species" : evo_species
    }

def evo_level_parser(evolution):
    evo_type = evolution[0].replace("EVO_", '').lower()
    evo_level = int(evolution[1])
    evo_species = evolution[2].replace("SPECIES_", '').lower()

    return {
        "type" : evo_type,
        "level" : evo_level,
        "species" : evo_species
    }

def evo_event_parser(evolution):
    evo_type = evolution[0].replace("EVO_", '').lower()
    evo_species = evolution[2].replace("SPECIES_", '').lower()

    return {
        "type" : evo_type,
        "species" : evo_species
    }

def evo_beauty_parser(evolution):
    evo_type = evolution[0].replace("EVO_", '').lower()
    evo_beauty = int(evolution[1])
    evo_species = evolution[2].replace("SPECIES_", '').lower()

    return {
        "type" : evo_type,
        "beauty" : evo_beauty,
        "species" : evo_species
    }

def evo_default_parser(evolution):
    evo_type = evolution[0].replace("EVO_", '').lower()
    evo_value = evolution[1]
    evo_species = evolution[2].replace("SPECIES_", '').lower()

    return {
        "type" : evo_type,
        "value" : evo_value,
        "species" : evo_species
    }

EVOLUTION_PARSERS = {
    "EVO_BEAUTY" : evo_beauty_parser,
    "EVO_ITEM" : evo_item_parser,
    "EVO_LEVEL" : evo_level_parser,
    "EVO_LEVEL_ATK_LT_DEF" : evo_level_parser,
    "EVO_LEVEL_ATK_GT_DEF" : evo_level_parser,
    "EVO_LEVEL_ATK_EQ_DEF" : evo_level_parser,
    "EVO_LEVEL_CASCOON" : evo_level_parser,
    "EVO_LEVEL_NINJASK" : evo_level_parser,
    "EVO_LEVEL_SHEDINJA" : evo_level_parser,
    "EVO_LEVEL_SILCOON" : evo_level_parser,
    "EVO_FRIENDSHIP" : evo_event_parser,
    "EVO_FRIENDSHIP_DAY" : evo_event_parser,
    "EVO_FRIENDSHIP_NIGHT" : evo_event_parser,
    "EVO_TRADE" : evo_event_parser,
    "EVO_TRADE_ITEM" : evo_item_parser
}

def parse_evolution(evolution):
    evolution = evolution.strip()
    start = 1
    end = len(evolution)
    if evolution.endswith("}"):
        end = -1
    evolution = evolution[start:end]
    evolution = evolution.split(', ')
    evo_type = evolution[0]
    if evo_type in EVOLUTION_PARSERS:
        parser = EVOLUTION_PARSERS[evo_type]
    else:
        parser = evo_default_parser
    return parser(evolution)

def parse_evolutions(evolutions):
    out_evolutions = []
    evolutions = evolutions.strip()
    evolutions = in_between(evolutions, "= {", "},")
    evolutions = evolutions.split("},")
    # print(evolutions)
    for evolution in evolutions:
        out_evolutions.append(parse_evolution(evolution))
    return out_evolutions

def to_json(fobj):
    out_json = {}
    data = fobj.read()
    sections_data = convert_sections(data.split('\n'))
    # print(sections_data)
    
    sections = re.split('\[|\]', sections_data)
    # print(sections_data)

    for i in range(1, len(sections), 2):
        name = sections[i]
        evolutions = sections[i+1]
        species_name = name.replace("SPECIES_", "").lower()
        evolutions_json = parse_evolutions(evolutions)
        out_json[species_name] = evolutions_json
    return out_json

def evo_beauty_formatter(evolution):
    evo_type = "EVO_{}".format(evolution["type"].upper())
    evo_beauty = evolution["beauty"]
    evo_species = "SPECIES_{}".format(evolution["species"].upper())
    TEMPLATE = "{{{}, {}, {}}}"
    return TEMPLATE.format(evo_type, evo_beauty, evo_species)

def evo_level_formatter(evolution):
    evo_type = "EVO_{}".format(evolution["type"].upper())
    evo_level = evolution["level"]
    evo_species = "SPECIES_{}".format(evolution["species"].upper())
    TEMPLATE = "{{{}, {}, {}}}"
    return TEMPLATE.format(evo_type, evo_level, evo_species)

def evo_item_formatter(evolution):
    evo_type = "EVO_{}".format(evolution["type"].upper())
    evo_item = "ITEM_{}".format(evolution["item"].upper())
    evo_species = "SPECIES_{}".format(evolution["species"].upper())
    TEMPLATE = "{{{}, {}, {}}}"
    return TEMPLATE.format(evo_type, evo_item, evo_species)

def evo_event_formatter(evolution):
    evo_type = "EVO_{}".format(evolution["type"].upper())
    evo_species = "SPECIES_{}".format(evolution["species"].upper())
    TEMPLATE = "{{{}, {}, {}}}"
    return TEMPLATE.format(evo_type, 0, evo_species)    

def evo_default_formatter(evolution):
    evo_type = "EVO_{}".format(evolution["type"].upper())
    evo_value = evolution["value"]
    evo_species = "SPECIES_{}".format(evolution["species"].upper())
    TEMPLATE = "{{{}, {}, {}}}"
    return TEMPLATE.format(evo_type, evo_value, evo_species)

EVOLUTION_FORMATTERS = {
    "beauty" : evo_beauty_formatter,
    "item" : evo_item_formatter,
    "level" : evo_level_formatter,
    "level_atk_lt_def" : evo_level_formatter,
    "level_atk_gt_def" : evo_level_formatter,
    "level_atk_eq_def" : evo_level_formatter,
    "level_cascoon" : evo_level_formatter,
    "level_ninjask" : evo_level_formatter,
    "level_shedinja" : evo_level_formatter,
    "level_silcoon" : evo_level_formatter,
    "friendship" : evo_event_formatter,
    "friendship_day" : evo_event_formatter,
    "friendship_night" : evo_event_formatter,
    "trade" : evo_event_formatter,
    "trade_item" : evo_item_formatter
}

def format_evolution(evolution):
    evo_type = evolution["type"]
    if evo_type in EVOLUTION_FORMATTERS:
        formatter = EVOLUTION_FORMATTERS[evo_type]
        return formatter(evolution)
    return None


def format_evolutions(evolutions):
    JOIN = ",\n\t" + (" " * (FILL_SPECIES_NAME_LEN + len("= {")))
    formatted_evolutions = []
    for evolution in evolutions:
        formatted_evolution = format_evolution(evolution)
        if formatted_evolution is not None:
            formatted_evolutions.append(formatted_evolution)

    return JOIN.join(
        formatted_evolutions
    )

def from_json(in_json):
    evolutions = []

    ENTRY_TEMPLATE = "\t{}= {{{}}},"
    for species_name, species_evolutions in in_json.items():
        species_name = "[SPECIES_{}]".format(species_name.upper())
        species_name += " " * (FILL_SPECIES_NAME_LEN - len(species_name))
        species_evolutions = format_evolutions(species_evolutions)
        evolutions.append(ENTRY_TEMPLATE.format(species_name, species_evolutions))

    return EVOLUTION_H_TEMPLATE.format(
        '\n'.join(evolutions)
    )

def main():
    argparser = ArgumentParser()
    argparser.add_argument('IN_FILE')
    argparser.add_argument('OUT_FILE')
    vargs = argparser.parse_args()

    in_json = {}
    with open(vargs.IN_FILE, "r") as fobj:
        in_json = json.load(fobj)
    evolution_h = from_json(in_json)
    with open(vargs.OUT_FILE, "w") as fobj:
        fobj.write(evolution_h)
    # out_json = {}
    # with open(vargs.IN_FILE, "r") as fobj:
    #     out_json = to_json(fobj)
    # with open(vargs.OUT_FILE, "w") as fobj:
    #     json.dump(out_json, fobj, indent=4)

if __name__ == "__main__":
    main()