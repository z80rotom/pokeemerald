import re
import json

SCAN_EMPTY = "= (0),"
SCAN_DEFINE = "#define"
SCAN_COMMENT = "//"
SCAN_TUTOR_MOVES = "const u16 gTutorMoves[TUTOR_MOVE_COUNT] ="
SCAN_EVOS = "static const u32 sTutorLearnsets[] ="
SCAN_ARRAY_START = "{"
SCAN_ARRAY_END = "};"
TUTOR_LEARNSETS_H_TEMPLATE = """const u16 gTutorMoves[TUTOR_MOVE_COUNT] =
{{
{}
}};

#define TUTOR(move) (1u << (TUTOR_##move))

static const u32 sTutorLearnsets[] =
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

def parse_tutor_learnsets(tutor_learnsets):
    out_tutor_learnsets = []
    tutor_learnsets = tutor_learnsets.strip()
    tutor_learnsets = in_between(tutor_learnsets, "= (", "),")
    tutor_learnsets = tutor_learnsets.split("|")
    for tutor_learnset in tutor_learnsets:
        tutor_learnset.strip()
        tutor_learnset = in_between(tutor_learnset, "TUTOR(", ")")
        out_tutor_learnsets.append(tutor_learnset)
    return out_tutor_learnsets

def parse_tutor_moves(lines):
    moves = []
    in_moves = False
    in_array = False
    for line in lines:
        line = line.strip()
        if line.startswith(SCAN_DEFINE):
            continue
        if line.startswith(SCAN_COMMENT):
            continue
        if line.startswith(SCAN_TUTOR_MOVES):
            in_moves = True
            continue

        # Need to double check we're not in array so we don't mistake 
        # an evolution entry as an outer array scan token
        if in_moves and not in_array and line.startswith(SCAN_ARRAY_START):
            in_array = True
            continue

        if not in_array:
            continue

        if line.startswith(SCAN_ARRAY_END):
            in_array = False
            in_moves = False
            break
        # We don't care about the left side
        # because it should always be TUTOR_##RIGHT_SIDE
        move_name = line.split("=")[1]
        move_name = move_name.strip()
        move_name = move_name.replace(',', '')
        moves.append(move_name)
    return moves

def to_json(fobj):
    out_json = {}
    data = fobj.read()
    lines = data.split('\n')

    out_json["tutor_moves"] = parse_tutor_moves(lines)
    out_tutor_learnsets = {}
    sections_data = convert_sections(lines)
    sections = re.split('\[|\]', sections_data)

    for i in range(1, len(sections), 2):
        name = sections[i]
        tutor_learnsets = sections[i+1]
        species_name = name
        if tutor_learnsets.strip() == SCAN_EMPTY:
            out_json[species_name] = []
            continue
        tutor_learnset_json = parse_tutor_learnsets(tutor_learnsets)
        out_tutor_learnsets[species_name] = tutor_learnset_json
    out_json["tutor_learnsets"] = out_tutor_learnsets
    return out_json

def format_tutor_learnsets(tutor_learnsets):
    JOIN = "\n\t{}| ".format(" " * (FILL_SPECIES_NAME_LEN + len("=")))
    formatted_tutor_learnsets = []
    for tutor_learnset in tutor_learnsets:
        tutor_learnset = "TUTOR({})".format(tutor_learnset)
        formatted_tutor_learnsets.append(tutor_learnset)

    return "({})".format(JOIN.join(
        formatted_tutor_learnsets
    ))

def format_tutor_moves(tutor_moves):
    out_tutor_moves = []
    for tutor_move in tutor_moves:
        out_tutor_moves.append("\t[TUTOR_{0}] = {0}".format(tutor_move))
    return ",\n".join(
        out_tutor_moves
    )

def from_json(in_json):
    ENTRY_TEMPLATE = "\t{}= {}"
    in_tutor_moves = in_json["tutor_moves"]
    tutor_moves = format_tutor_moves(in_tutor_moves)

    in_tutor_learnsets = in_json["tutor_learnsets"]
    tutor_learnsets = []
    for species_name, species_tutor_learnsets in in_tutor_learnsets.items():
        species_name = "[{}]".format(species_name.upper())
        species_name += " " * (FILL_SPECIES_NAME_LEN - len(species_name))
        if species_tutor_learnsets == []:
            species_tutor_learnsets = "{(0), (0)}"
        else:
            species_tutor_learnsets = format_tutor_learnsets(species_tutor_learnsets)
        tutor_learnsets.append(ENTRY_TEMPLATE.format(species_name, species_tutor_learnsets))

    return fix_tabs(TUTOR_LEARNSETS_H_TEMPLATE.format(
        tutor_moves,
        ',\n\n'.join(tutor_learnsets)
    ))

def build_tutor_learnsets(tutor_learnset_json_fpath, tutor_learnset_h_fpath):
    in_json = {}
    with open(tutor_learnset_json_fpath, "r") as fobj:
        in_json = json.load(fobj)
    tutor_learnset_h = from_json(in_json)
    with open(tutor_learnset_h_fpath, "w") as fobj:
        fobj.write(tutor_learnset_h)