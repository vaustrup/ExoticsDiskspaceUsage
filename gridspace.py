import argparse

from analysers.gridspaceanalyser import GridSpaceAnalyser


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--rse", default="CERN-PROD_PHYS-EXOTICS", choices=["CERN-PROD_PHYS-EXOTICS", "TOKYO-LCG2_PHYS-EXOTICS"], help="RSE to check")
    args = parser.parse_args()

    analyser = GridSpaceAnalyser(rse=args.rse)
    analyser.load_lookup_table()
    analyser.analyse_datasets()
    analyser.report()

if __name__ == "__main__":
    main()
 
