import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:
    __version__ = "unknown"  # pragma: no cover
finally:
    del version, PackageNotFoundError

from .booking import Booking
from .bookings import Bookings
from .statement_reader import csv2bookings, files2booking, pdf2bookings, txt2bookings

__all__ = [
    "csv2bookings",
    "txt2bookings",
    "pdf2bookings",
    "Booking",
    "Bookings",
    "files2booking",
]
