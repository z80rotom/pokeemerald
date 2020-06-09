from argparse import ArgumentParser
import json

SCAN_DEFINE = "#define"
SCAN_ARRAY_LINE_START = "static const u16 "
SCAN_ARRAY_LINE_END = "[] = {"
SCAN_MOVE_START = "LEVEL_UP_MOVE("
SCAN_MOVE_END = "),"
SCAN_MOVES_END = "LEVEL_UP_END"
SCAN_ARRAY_END = "};"

LEVEL_UP_LEARNSETS_TEMPLATE = """#define LEVEL_UP_MOVE(lvl, move) ((lvl << 9) | move)

{}"""

POINTERS_TEMPLATE = """const u16 *const gLevelUpLearnsets[NUM_SPECIES] =
{{
{}
}};"""

def fix_tabs(in_str):
    return in_str.replace('\t', '    ')

def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].capitalize() + ''.join(x.title() for x in components[1:])

def get_between(in_str, start_str, end_str):
    return in_str[
        in_str.index(start_str) + len(start_str) :
        in_str.index(end_str)
    ]

def to_json(fobj):
    data = fobj.read()

    level_up_learnsets = {}
    current_species_name = None
    current_learnset = None
    in_learnset = False

    for line in data.split('\n'):
        line = line.strip()
        if line.startswith(SCAN_DEFINE):
            # We don't want to worry about defines in this file
            continue
        if line.startswith(SCAN_ARRAY_LINE_START) and \
           line.endswith(SCAN_ARRAY_LINE_END):
           species_name = line
           # Remove the C Syntax for the array construction
           species_name = species_name.replace(SCAN_ARRAY_LINE_START, '')
           species_name = species_name.replace(SCAN_ARRAY_LINE_END, '')
           # Remove the leading s for hungarian naming
           species_name = species_name[1:]
           species_name = species_name.replace('LevelUpLearnset', '')
           species_name = species_name.lower()
           current_species_name = species_name
           current_learnset = []
           in_learnset = True
           continue
        
        if not in_learnset:
            continue

        if line.startswith(SCAN_MOVES_END):
            level_up_learnsets[current_species_name] = current_learnset
            in_learnset = False
            continue
        
        if line.startswith(SCAN_MOVE_START):
            move_data = get_between(line, SCAN_MOVE_START, SCAN_MOVE_END)
            move_data = move_data.strip()
            level, move_name = move_data.split(', ')
            level = int(level)
            move_name = move_name.replace("MOVE_", '')
            move_name = move_name.lower()
            level_up_move = {
                "level" : level,
                "name" : move_name
            }
            current_learnset.append(level_up_move)
    return level_up_learnsets

def build_entry(species_name, level_up_learnset):
    lines = []

    species_name = to_camel_case(species_name)
    array_name = "s{}LevelUpLearnset".format(species_name)
    declare_array = "{}{}{}".format(SCAN_ARRAY_LINE_START, array_name, SCAN_ARRAY_LINE_END)
    lines.append(declare_array)
    for move in level_up_learnset:
        level = move["level"]
        name = move["name"]
        name = "MOVE_{}".format(name.upper())
        line = "\t{}{}, {}{}".format(SCAN_MOVE_START, level, name, SCAN_MOVE_END)
        lines.append(line)
    lines.append('\t{}'.format(SCAN_MOVES_END))
    lines.append(SCAN_ARRAY_END)

    return '\n'.join(lines)

def from_json(in_json):
    entries = []
    for species_name, level_up_learnset in in_json.items():
        entry = build_entry(species_name, level_up_learnset)
        entries.append(entry)
    return fix_tabs(LEVEL_UP_LEARNSETS_TEMPLATE.format(
        '\n\n'.join(entries)
    ))

def build_pointer_entry(species_name, array_name):
    array_name = "s{}LevelUpLearnset".format(to_camel_case(array_name))
    species_name = "SPECIES_{}".format(species_name.upper())
    return '\t[{}] = {},'.format(species_name, array_name)

def build_pointers(in_json):
    pointers = []
    
    pointers.append(build_pointer_entry("none", list(in_json.keys())[0]))
    for species_name in in_json:
        pointer = build_pointer_entry(species_name, species_name)
        pointers.append(pointer)

    return fix_tabs(POINTERS_TEMPLATE.format(
        '\n'.join(pointers)
    ))

def main():
    argparser = ArgumentParser()
    argparser.add_argument('IN_FILE')
    argparser.add_argument('OUT_FILE')
    argparser.add_argument('PTR_FILE')
    vargs = argparser.parse_args()

    in_json = {}
    with open(vargs.IN_FILE, "r") as fobj:
        in_json = json.load(fobj)
    
    level_up_learnsets_h = from_json(in_json)
    with open(vargs.OUT_FILE, "w") as fobj:
        fobj.write(level_up_learnsets_h)

    level_up_learnset_pointers_h = build_pointers(in_json)
    with open(vargs.PTR_FILE, "w") as fobj:
        fobj.write(level_up_learnset_pointers_h)

    # out_json = {}
    # with open(vargs.IN_FILE, "r") as fobj:
    #     out_json = to_json(fobj)
    # with open(vargs.OUT_FILE, "w") as fobj:
    #     json.dump(out_json, fobj, indent=4)

if __name__ == "__main__":
    main()