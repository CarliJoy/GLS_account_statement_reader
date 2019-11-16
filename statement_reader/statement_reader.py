import csv
import re
import subprocess
import tempfile
from logging import getLogger

from .bookings import Bookings
from .booking import Booking

logger = getLogger("statement_reader.reader")


def csv2bookings(filename):
    """
    Reads an GLS export (new version) and creates a bookings file
    """
    headers = list()
    bookings = Bookings()
    ignored_lines = list()
    ignore_rest: bool = False
    with open(filename, newline="", encoding='latin-1') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
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
                comment = result.get('Vorgang/Verwendungszweck').split("\n")
                booking.comment = "\n".join(comment[1:])
                booking.date = result.get('Buchungstag')
                booking.type = comment[0]
                multiply = -1 if result.get("HS") == "S" else 1
                booking.amount = float(result.get('Umsatz').replace(".", "").replace(",", ".")) * multiply
                booking.payee = result.get('Empfänger/Zahlungspflichtiger')
                bookings.append(booking, ignore_duplicates=False)
            elif len(row) > 0 and row[0] == "Buchungstag":
                # Read Headers
                for cell in row:
                    headers.append(cell)
                    if cell == "Umsatz":
                        headers.append("HS")
                        break
        if ignored_lines:
            logger.debug("Ignored lines: "+'\n'.join(ignored_lines))
    return bookings


def data2booking(data, year):
    booking = None
    bookings = Bookings()
    next_is_payee = False
    payee = None
    if data[-1].strip() != "":
        # Make sure the last entry is empty so also the last booking is added
        data.append("")
    for line in data:
        line = line.replace("\n", "")
        if not line:
            continue
        # Check for new entry
        if line[0] != " ":
            if booking:
                # Set payee just in the end, as we need the comment to be read complete before
                # print(f"Comment: {booking.comment}")
                booking.payee = payee
                bookings.append(booking, ignore_duplicates=False)
            booking = Booking()
            vals = re.split("[ ]{4,100}", line)
            # print(vals)
            booking.date = f"{vals[0]}{year}"
            booking.type = vals[1]
            booking.amount = float(vals[2][-1:] + vals[2][:-1].replace(".", "").replace(",", "."))
            booking.comment = ""
            next_is_payee = True
        elif next_is_payee:
            next_is_payee = False
            payee = line.strip()
            # print(f"Payee: {payee}")
        else:
            booking.comment = f"{booking.comment} {line}".strip()
    return bookings


def pdf2bookings(filepath):
    with tempfile.NamedTemporaryFile() as tmpfile:
        # First convert the pdf to text keeping the layout - all output is handeled in a temporary file that is deleted afters
        subprocess.run(['pdftotext', '-layout', filepath, tmpfile.name])
        # extract the year
        result = subprocess.run(
            f"cat {tmpfile.name} |  sed -n -e '/erstellt am [23][0-9][.][01][0-9].20[0-9][0-9]/ {{p;q}}' | sed 's/^.*am [23][0-9][.][01][0-9].\\(20[0-9][0-9]\\)/\\1/'",
            shell=True, stdout=subprocess.PIPE, encoding="UTF-8")
        year = result.stdout.replace("\n", "").strip()
        # Now just extract the actual lines containing a transfer by looking at every block that starts with the date
        # the first sed is used to remove all
        result = subprocess.run(
            f"cat {tmpfile.name} | sed 's/^[ ]*\\([0-3][0-9][.][0-1][0-9].[ ]*\\) /\\1    /' | sed -ne '/[0-3][0-9][.][0-1][0-9].[ ]\\{{1,4\\}}/,/^[_ \\t-]*\(SALDO NEU.*\)\{{0,1\}}$/ p' | sed '/^[_ \\t-]*$/ d'",
            shell=True, stdout=subprocess.PIPE, encoding="UTF-8")

        return data2booking(re.split("\n", result.stdout), year)


def txt2bookings(filepath, year):
    with open(filepath, "r", encoding="UTF-8") as fp:
        data = fp.readlines()
    return data2booking(data, year)
