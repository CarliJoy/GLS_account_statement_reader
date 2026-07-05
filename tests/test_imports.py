import bank_statement_reader
from bank_statement_reader.bookings import Bookings


def test_package_importable():
    assert bank_statement_reader is not None


def test_bookings_empty():
    b = Bookings()
    assert len(b) == 0
