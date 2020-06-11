import battlemovesjson.battlemoves as battlemoves
import evolutionjson.evolution as evolution
import learnsetsjson.learnsets as learnsets
import tmhm_learnsets_json.tmhm_learnsets as tmhm_learnsets

BATTLE_MOVES_JSON_FPATH = "battlemovesjson/battle_moves.json"
BATTLE_MOVES_H_FPATH = "../src/data/battle_moves.h"
EVOLUTION_JSON_FPATH = "evolutionjson/evolution.json"
EVOLUTION_H_FPATH = "../src/data/pokemon/evolution.h"
LEARNSETS_JSON_FPATH = "learnsetsjson/level_up_learnsets.json"
LEARNSETS_H_FPATH = "../src/data/pokemon/level_up_learnsets.h"
LEARNSET_POINTERS_H_FPATH = "../src/data/pokemon/level_up_learnset_pointers.h"
TMHM_LEARNSETS_JSON_FPATH = "tmhm_learnsets_json/tmhm_learnsets.json"
TMHM_LEARNSETS_H_FPATH = "../src/data/pokemon/tmhm_learnsets.h"

def main():
    battlemoves.build_battlemoves(BATTLE_MOVES_JSON_FPATH, BATTLE_MOVES_H_FPATH)
    learnsets.build_learnsets(LEARNSETS_JSON_FPATH, LEARNSETS_H_FPATH, 
                              LEARNSET_POINTERS_H_FPATH)
    evolution.build_evolution(EVOLUTION_JSON_FPATH, EVOLUTION_H_FPATH)
    tmhm_learnsets.build_tmhm_learnsets(TMHM_LEARNSETS_JSON_FPATH,
                                        TMHM_LEARNSETS_H_FPATH)

if __name__ == "__main__":
    main()