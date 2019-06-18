#!/usr/bin/env python3
import argparse
import logging
from statement_reader import pdf2bookings, txt2bookings, csv2bookings
from statement_reader.bookings import Bookings

parser = argparse.ArgumentParser(description='Convert banking statements (PDF & CSV) to analysed standard csv form.')

parser.add_argument('input_files', metavar='filenames_in', type=argparse.FileType('r'), nargs='+',
                    help='files to open and convert')

parser.add_argument('output_file', metavar='filename_out', type=argparse.FileType('w'), help='output file')

args = parser.parse_args()

bookings = Bookings()

for file_obj in args.input_files:
    filename = file_obj.name
    if filename.endswith('.pdf'):
        bookings = bookings + pdf2bookings(filename)
    elif filename.endswith('.csv'):
        bookings = bookings + csv2bookings(filename)
    else:
        logging.warning(f'Ignoring "{filename}": Only csv and pdf files are supported')

bookings.save(args.output_file.name)
