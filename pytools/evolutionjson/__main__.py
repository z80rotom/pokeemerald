from evolution import build_evolution

def main():
    argparser = ArgumentParser()
    argparser.add_argument('IN_FILE')
    argparser.add_argument('OUT_FILE')
    vargs = argparser.parse_args()
    build_evolution(vargs.IN_FILE, vargs.OUT_FILE)

if __name__ == "__main__":
    main()