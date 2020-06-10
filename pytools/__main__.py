import learnsetsjson.learnsets as learnsets
import evolutionjson.evolution as evolution

EVOLUTION_JSON_FPATH = "evolutionjson/evolution.json"
EVOLUTION_H_FPATH = "../src/data/pokemon/evolution.h"
LEARNSETS_JSON_FPATH = "learnsetsjson/level_up_learnsets.json"
LEARNSETS_H_FPATH = "../src/data/pokemon/level_up_learnsets.h"
LEARNSET_POINTERS_H_FPATH = "../src/data/pokemon/level_up_learnset_pointers.h"

def main():
    learnsets.build_learnsets(LEARNSETS_JSON_FPATH, LEARNSETS_H_FPATH, 
                              LEARNSET_POINTERS_H_FPATH)
    evolution.build_evolution(EVOLUTION_JSON_FPATH, EVOLUTION_H_FPATH)

if __name__ == "__main__":
    main()