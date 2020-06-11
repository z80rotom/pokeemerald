from argparse import ArgumentParser
import json
from pokedextext import to_json, build_pokedex_text

def main():
    argparser = ArgumentParser()
    argparser.add_argument('IN_FILE')
    argparser.add_argument('OUT_FILE')
    vargs = argparser.parse_args()

    build_pokedex_text(vargs.IN_FILE, vargs.OUT_FILE)
    # out_json = {}
    # with open(vargs.IN_FILE, "r") as fobj:
    #     out_json = to_json(fobj)
    # with open(vargs.OUT_FILE, "w") as fobj:
    #     json.dump(out_json, fobj, indent=4)

if __name__ == "__main__":
    main()