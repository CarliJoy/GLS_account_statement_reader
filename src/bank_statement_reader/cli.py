#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import Bookings, files2booking


def main(args: List[str]):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Convert banking statements (PDF & CSV) "
        "to an analysed standard csv form.",
        epilog="""
        If no filename is given, the file will be saved to:
            basename_first_file_%date_string%.csv.
        %date_string% will be always replaced to 'YYYY-mm-dd_to_YYYY-mm-dd'
                                                 start date  to   end date
        """,
    )

    parser.add_argument(
        "input_files",
        metavar="statement.pdf",
        type=argparse.FileType("r"),
        nargs="+",
        help="files to open and convert",
    )

    parser.add_argument(
        "--out",
        metavar="out.csv",
        dest="output_file",
        type=argparse.FileType("w"),
        help="csv file to write the results to",
        default=None,
    )

    args = parser.parse_args(args)

    files = [Path(file_obj.name).absolute() for file_obj in args.input_files]

    outfile_name = files[0].with_name(f"{files[0].stem}_%date_string%.csv")

    if args.output_file is not None:
        outfile_name = Path(args.output_file.name).absolute()

    bookings: Bookings = files2booking(files)
    outfile_name = bookings.save(outfile_name)

    print(f"Successfully wrote {outfile_name}")


def run(args: Optional[List[str]] = None):
    """Entry point for console script"""
    main(args or sys.argv[1:])


if __name__ == "__main__":
    run()
