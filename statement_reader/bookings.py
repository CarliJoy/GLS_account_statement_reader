from datetime import datetime
from .booking import Booking


class Bookings(list):
    def __init__(self):
        super().__init__()
        self.daterelation = dict()

    def html_filter_entry_without_category(self, filter: bool = True):
        result = "<table class='table_basic'><tr><th>Date</th><th>Category</th><th>Type</th><th>Amount</th><th>Payee</th><th>Comment</th></tr>"
        for i in self:
            if not i.category or not filter:
                result = f"{result}\n<tr>{i._tr_}</tr>"
        return f"{result}</table>"

    def _repr_html_(self):
        return self.html_filter_entry_without_category(False)

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
