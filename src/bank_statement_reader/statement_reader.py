import csv
import re
import subprocess
import warnings
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import List, Tuple

from pdfminer.high_level import extract_text
from pdfminer.pdfdocument import PDFTextExtractionNotAllowedWarning

from .booking import Booking
from .bookings import Bookings
from .exceptions import ParsingError, UnableToExtractDate

logger = getLogger("bank_statement_reader.reader")

RE_BOOKING_LINE_START = re.compile("^[ \t]*[0-3][0-9][.][0-1][0-9].[ \t]+")

RE_BOOKING_LINE = re.compile(
    "^(?P<date1>[0-9]{2}[.][0-9]{2}[.])"
    "([ ]+(?P<date2>[0-9]{2}[.][0-9]{2}[.]))?"
    "[ ]*(?P<type>.+?)[ ]+"
    "(?P<amount>[0-9,.]+[ ]*[HS+-])$"
)
RE_SEPARATOR_LINE = re.compile("[ _\t-]*")
RE_CREATION_YEAR = re.compile(
    "erstellt[ ]+am[ ]+[0-3][0-9][.][01][0-9].(?P<year>20[0-9][0-9])"
)


def parse_amount_string(amount: str) -> float:
    """
    Parse strings like
     - '1.000,00-'
     - '1.000,00   S'
     - '23,23+'
     - '23,23     H'
    to the correct amount as float
    :param amount: The string of an amount
    :return:
    """
    # Replace H and S
    amount = amount.replace("H", "+").replace("S", "-")
    # Remove german thousand separator
    amount = amount.replace(".", "")
    # Replace german decimal separator with english
    amount = amount.replace(",", ".")
    # Put the sign at the correct place and trim
    amount = amount[-1] + amount[:-1].strip()
    return float(amount)


def csv2bookings(filename) -> Bookings:
    """
    Reads an GLS export (new version) and creates a bookings file
    """
    headers = list()
    bookings = Bookings()
    ignored_lines = list()
    ignore_rest: bool = False
    with open(filename, newline="", encoding="latin-1") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=";", quotechar='"')
        for row in spamreader:
            if ignore_rest:
                ignored_lines.append(";".join(row))
            elif len(headers) > 1:
                if len(row) != len(headers):
                    ignore_rest = True
                    ignored_lines.append(";".join(row))
                    continue
                result = dict()
                booking = Booking()
                for cell, header in zip(row, headers):
                    result[header] = cell

                # Comment has to be set first as it is used to determine Payee as well
                comment = result.get("Vorgang/Verwendungszweck").split("\n")
                booking.comment = "\n".join(comment[1:])
                booking.date = result.get("Buchungstag")
                booking.type = comment[0]
                multiply = -1 if result.get("HS") == "S" else 1
                booking.amount = (
                    float(result.get("Umsatz").replace(".", "").replace(",", "."))
                    * multiply
                )
                booking.payee = result.get("Empfänger/Zahlungspflichtiger")
                bookings.append(booking, ignore_duplicates=False)
            elif len(row) > 0 and row[0] == "Buchungstag":
                # Read Headers
                for cell in row:
                    headers.append(cell)
                    if cell == "Umsatz":
                        headers.append("HS")
                        break
        if ignored_lines:
            logger.debug("Ignored lines: " + "\n".join(ignored_lines))
    return bookings


def data2booking(data: List[str], year: str) -> Bookings:
    # Last line can not start with space and needs to be unique
    LAST_LINE = "%%%$$LAST$$%%%"

    booking = None
    bookings = Bookings()
    next_is_payee = False
    payee = None
    # Make sure the last entry is empty so also the last booking is added
    data.append(LAST_LINE)
    for line in data:
        line = line.replace("\n", "")
        if not line:
            continue
        # Check for new entry
        if line[0] != " ":
            if booking:
                # Set payee just in the end, as we need the comment to be
                # read complete before
                # print(f"Comment: {booking.comment}")
                booking.payee = payee
                bookings.append(booking, ignore_duplicates=False)
                if line == LAST_LINE:
                    break
            booking = Booking()
            # noqa: E501
            """
            Example for new file
            '02.01.    01.01. Überweisungsgutschr.                           1.000,00 H'
            Example for old file
            '01.04.   Dauer-Euro-Überweisung                                      1,00-'

            """

            matches = RE_BOOKING_LINE.fullmatch(line.strip())
            if matches is None:
                if "Anlage" in line:
                    # I kind of hate the GLS bank for creating reports
                    # that are so different and so hard to parse, could they
                    # not simply allow all time CSV downloads???
                    logger.info(
                        f"Ignoring line '{line}' as it seems to be only a summary"
                    )
                    continue
                else:
                    raise ParsingError(
                        f"Could not parse the line: \n"
                        f"  '{line}'\n"
                        f"It seem not to follow the format of a typical bank report"
                    )
            matches = matches.groupdict()
            date = matches["date1"]
            booking.date = f"{date}{year}"
            booking.type = matches["type"].strip()
            booking.amount = parse_amount_string(matches["amount"])
            booking.comment = ""
            next_is_payee = True
        elif next_is_payee:
            next_is_payee = False
            payee = line.strip()
            # print(f"Payee: {payee}")
        else:
            booking.comment = f"{booking.comment} {line}".strip()
    return bookings


def get_pdf_text_with_layout(filepath: PathLike, force_poppler: bool = False) -> str:
    """
    Extract the layout like text from the PDF, either using pdfminer.six (python only)
    or pdftotext from poppler.

    We first try the PDF only variant but it is not working as stable as pdftotext
    and Carli* is not willing to spend time into fine tuning it for ever changing
    reports only to reduce external dependencies

    :param filepath:
    :param force_poppler:
    :return:
    """
    if not force_poppler:
        with warnings.catch_warnings():
            # Ignore warning that text extraction is not allowed by the PDF
            warnings.filterwarnings(
                "ignore", category=PDFTextExtractionNotAllowedWarning
            )
            text = extract_text(filepath)
        if len(text.splitlines()) > 10:
            return text
    logger.debug("Using poppler to extract text.")
    result = subprocess.run(
        ["pdftotext", "-layout", filepath, "-"],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
    )
    return result.stdout.decode("UTF-8")


def pdf2data_and_year(text: str, filepath: PathLike) -> Tuple[List[str], str]:
    """
    Parse PDF and extract all booking strings and the booking year
    :param text: the text to analyse for bookings
    :param filepath: Only for sane error reporting
    :return: List of bookings, year of the bookings
    """
    # Extract the creation date to get the correct year for the entries
    try:
        match = next(RE_CREATION_YEAR.finditer(text))
    except StopIteration:
        raise UnableToExtractDate(f"Could not extract creation date from '{filepath}'.")
    else:
        year = match.groupdict()["year"]

    # Now extract all booking values
    lines: List[str] = text.splitlines()
    # booking values
    data: List[str] = []

    beginning_found = False
    for line in lines:
        do_append = False
        # Every booking should start with a data
        if RE_BOOKING_LINE_START.match(line) is not None:
            beginning_found = True
            do_append = True
            line = line.strip()
        # followed by indented lines
        elif beginning_found and len(line) > 0 and line[0] == " ":
            if RE_SEPARATOR_LINE.fullmatch(line) is None:
                do_append = True
            else:
                # but if this indented lines only consists of separator characters
                # it is probably the end of booking section
                beginning_found = False
        else:
            beginning_found = False
            do_append = False

        if do_append:
            # Only strip the right as the front is used to determine th
            data.append(line.rstrip())
    return data, year


def pdf2bookings(filepath: PathLike) -> Bookings:
    logger.debug(f"Reading {filepath}")
    try:
        text = get_pdf_text_with_layout(filepath)
        return data2booking(*pdf2data_and_year(text, filepath))
    except UnableToExtractDate:
        # Try again but force the use of poppler
        text = get_pdf_text_with_layout(filepath, True)
        return data2booking(*pdf2data_and_year(text, filepath))


def txt2bookings(filepath, year) -> Bookings:
    with open(filepath, "r", encoding="UTF-8") as fp:
        data = fp.readlines()
    return data2booking(data, year)


def files2booking(files: List[Path]) -> Bookings:
    bookings = Bookings()

    for filename in files:
        if filename.suffix.lower() == ".pdf":
            bookings = bookings + pdf2bookings(filename)
        elif filename.suffix.lower() == ".csv":
            bookings = bookings + csv2bookings(filename)
        else:
            logger.warning(
                f'Ignoring "{filename}": Only csv and pdf files are supported'
            )

    return bookings
