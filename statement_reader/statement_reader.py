import csv
import re
import subprocess
import tempfile
from datetime import datetime
from .booking import Booking


class Bookings(list):
    def __init__(self):
        super().__init__()
        self.daterelation = dict()

    def _repr_html_(self):
        result = "<table class='table_basic'><tr><th>Date</th><th>Category</th><th>Type</th><th>Amount</th><th>Payee</th><th>Comment</th></tr>"
        for i in self:
            if not i.category:
                result = f"{result}\n<tr>{i._tr_}</tr>"
        return f"{result}</table>"

    def __add__(self, other: 'Bookings'):
        result = Bookings()
        # for key in sorted(self.daterelation.keys() + other.daterelation.keys()):
        for itm in self:
            result.append(itm)
        for itm in other:
            result.append(itm)
        return result

    def save(self, filename):
        with open(filename, "w", newline="\n", encoding="utf-8") as fp:
            fp.write("Date;Category;Type;Amount;Payee;Comment\n")
            for i in self:
                fp.write(f"{i}\n")

    def append(self, booking: Booking):
        booking_date = datetime.strptime(booking.date, "%d.%m.%Y").date()
        if not booking_date in self.daterelation:
            self.daterelation[booking_date] = list()
        self.daterelation[booking_date].append(booking)
        super().append(booking)


def csv2bookings(filename):
    """
    Reads an GLS export and creates a bookings file
    """
    headers = list()
    bookings = Bookings()
    with open(filename, newline="", encoding='latin-1') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        line = 0
        for row in spamreader:
            line = line + 1
            if line == 1:
                for cell in row:
                    headers.append(cell)
            else:
                result = dict()
                booking = Booking()
                for cell, header in zip(row, headers):
                    result[header] = cell

                # Comment has to be set first as it is used to determine Payee as well
                booking.comment = ""
                for i in range(1, 14):
                    tmp = result.get(f"VWZ{i}")
                    if tmp:
                        booking.comment = f"{booking.comment} {tmp}"
                booking.date = result.get('Buchungstag')
                booking.type = result.get('Buchungstext')
                booking.amount = float(result.get('Betrag').replace(".", "").replace(",", "."))
                booking.payee = result.get('Auftraggeber/Empfänger')
                bookings.append(booking)
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
                # Set payee just in the end, as we need the comment to be read completly before
                # print(f"Comment: {booking.comment}")
                booking.payee = payee
                bookings.append(booking)
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
