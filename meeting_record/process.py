import argparse

import textract

from meeting_record.raw.au_qld.process import Process as AuQldProcess

parser = argparse.ArgumentParser(description='Process government meeting record files.')
parser.add_argument('meeting_record_type', help='The type of meeting record.')
parser.add_argument('input_file', help='Path to the input file.')
args = parser.parse_args()

# item = textract.process(args.input_file)

meeting_types = {
    'au_qld': AuQldProcess()
}

if args.meeting_record_type in meeting_types:
    meeting_types[args.meeting_record_type].run(args.input_file)
else:
    raise Exception(f"Unrecognised meeting type '{args.meeting_record_type}'.")
