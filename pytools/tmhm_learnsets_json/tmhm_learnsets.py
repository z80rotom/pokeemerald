import re
import json

SCAN_EMPTY = "= {(0), (0)},"
SCAN_DEFINE = "#define"
SCAN_COMMENT = "//"
SCAN_EVOS = "const u32 gTMHMLearnsets[][2] ="
SCAN_ARRAY_START = "{"
SCAN_ARRAY_END = "};"
TMHM_LEARNSETS_H_TEMPLATE = """#define TMHM_LEARNSET(moves) {{(u32)(moves), ((u64)(moves) >> 32)}}
#define TMHM(tmhm) ((u64)1 << (ITEM_##tmhm - ITEM_TM01_FOCUS_PUNCH))

// This table determines which TMs and HMs a species is capable of learning.
// Each entry is a 64-bit bit array spread across two 32-bit values, with
// each bit corresponding to a .
const u32 gTMHMLearnsets[][2] =
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
        if line.startswith(SCAN_DEFINE):
            continue
        if line.startswith(SCAN_COMMENT):
            continue
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

def parse_tmhm_learnsets(tmhm_learnsets):
    out_tmhm_learnsets = []
    tmhm_learnsets = tmhm_learnsets.strip()
    tmhm_learnsets = in_between(tmhm_learnsets, "= TMHM_LEARNSET(", "),")
    tmhm_learnsets = tmhm_learnsets.split("|")
    for tmhm_learnset in tmhm_learnsets:
        tmhm_learnset.strip()
        tmhm_learnset = in_between(tmhm_learnset, "TMHM(", ")")
        out_tmhm_learnsets.append(tmhm_learnset)
    return out_tmhm_learnsets

def to_json(fobj):
    out_json = {}
    data = fobj.read()
    sections_data = convert_sections(data.split('\n'))
    sections = re.split('\[|\]', sections_data)

    for i in range(1, len(sections), 2):
        name = sections[i]
        tmhm_learnsets = sections[i+1]
        species_name = name
        if tmhm_learnsets.strip() == SCAN_EMPTY:
            out_json[species_name] = []
            continue
        tmhm_learnset_json = parse_tmhm_learnsets(tmhm_learnsets)
        out_json[species_name] = tmhm_learnset_json
    return out_json

def format_tmhm_learnsets(tmhm_learnsets):
    JOIN = "\n\t{}| ".format(" " * (FILL_SPECIES_NAME_LEN + len("= TMHM_LEARNSE")))
    formatted_tmhm_learnsets = []
    for tmhm_learnset in tmhm_learnsets:
        tmhm_learnset = "TMHM({})".format(tmhm_learnset)
        formatted_tmhm_learnsets.append(tmhm_learnset)

    return "TMHM_LEARNSET({})".format(JOIN.join(
        formatted_tmhm_learnsets
    ))

def from_json(in_json):
    tmhm_learnsets = []

    ENTRY_TEMPLATE = "\t{}= {}"
    for species_name, species_tmhm_learnsets in in_json.items():
        species_name = "[{}]".format(species_name.upper())
        species_name += " " * (FILL_SPECIES_NAME_LEN - len(species_name))
        if species_tmhm_learnsets == []:
            species_tmhm_learnsets = "{(0), (0)}"
        else:
            species_tmhm_learnsets = format_tmhm_learnsets(species_tmhm_learnsets)
        tmhm_learnsets.append(ENTRY_TEMPLATE.format(species_name, species_tmhm_learnsets))

    return fix_tabs(TMHM_LEARNSETS_H_TEMPLATE.format(
        ',\n'.join(tmhm_learnsets)
    ))

def build_tmhm_learnsets(tmhm_learnset_json_fpath, tmhm_learnset_h_fpath):
    in_json = {}
    with open(tmhm_learnset_json_fpath, "r") as fobj:
        in_json = json.load(fobj)
    tmhm_learnset_h = from_json(in_json)
    with open(tmhm_learnset_h_fpath, "w") as fobj:
        fobj.write(tmhm_learnset_h)