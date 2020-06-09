import learnsetsjson.learnsets as learnsets

LEARNSETS_JSON_FPATH = "learnsetsjson/level_up_learnsets.json"
LEARNSETS_H_FPATH = "../src/data/pokemon/level_up_learnsets.h"
LEARNSET_POINTERS_H_FPATH = "../src/data/pokemon/level_up_learnset_pointers.h"

def main():
    learnsets.build_learnsets(LEARNSETS_JSON_FPATH, LEARNSETS_H_FPATH, 
                              LEARNSET_POINTERS_H_FPATH)

if __name__ == "__main__":
    main()