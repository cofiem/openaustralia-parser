import argparse

from parliaments.au_qld.hansard import Hansard

parser = argparse.ArgumentParser(description='Process Queensland Hansard pdf files.')
parser.add_argument('input_file', help='Path to the input file.')
args = parser.parse_args()

hansard = Hansard()
hansard.run(args.input_file)
