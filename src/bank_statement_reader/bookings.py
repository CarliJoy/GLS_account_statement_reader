import logging
import re
from datetime import date
from os import PathLike
from pathlib import Path
from textwrap import indent
from typing import Dict, Optional

from .booking import Booking

logger = logging.getLogger("bank_statement_reader.bookings")
logger_dupes = logging.getLogger("bank_statement_reader.duplicates")


class Bookings(list):
    STRICT_COMPARING: bool = True

    def __init__(self):
        super().__init__()
        self.daterelation: Dict[date, list] = dict()

    def html_filter_entry_without_category(self, filter: bool = True):
        result = (
            "<table class='table_basic'>"
            "<tr><th>Date</th><th>Category</th><th>Type</th>"
            "<th>Amount</th><th>Payee</th><th>Comment</th></tr>"
        )
        for i in self:
            if not i.category or not filter:
                result = f"{result}\n<tr>{i._tr_}</tr>"
        return f"{result}</table>"

    def _repr_html_(self):
        return self.html_filter_entry_without_category(False)

    def __repr__(self):
        result = " [\n"
        for itm in self:
            result += "  " + repr(itm) + "\n"
        return result + "]"

    def __iter__(self):
        """ Always sort"""
        for itm in sorted(super().__iter__()):
            yield itm

    def __add__(self, other: "Bookings"):
        result = Bookings()
        # for key in sorted(self.daterelation.keys() + other.daterelation.keys()):
        for itm in self:
            result.append(itm, ignore_duplicates=True)
        for itm in other:
            result.append(itm, ignore_duplicates=True)
        return result

    def __iadd__(self, other):
        """ allow same handling for += like for add"""
        return self.__add__(other)

    @property
    def start_date(self):
        return list(sorted(self.daterelation.keys()))[0]

    @property
    def end_date(self):
        return list(sorted(self.daterelation.keys()))[-1]

    @property
    def sum(self):
        return sum([itm for itm in self])

    def test_logger(self):
        logger.info("Info")
        logger.warning("Warning")
        logger.debug("Debug")

    def save(
        self,
        filename: Optional[PathLike] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Path:
        """
        save bookings

        if start or end date are given the export will be limited to dates between
        if no filename is given, the file will be saved to
            "bookings_exported_%date_string%.csv"
        %date_string% will be always replaced to YYYY-mm-dd_to_YYYY-mm-dd
            (start to end date)

        :param filename: Filename to save result to
        :param start_date: limit export to start date
        :param end_date:  limit export until end date
        :return: filepath of saved filed
        """

        if not isinstance(filename, Path):
            filename = Path(filename)
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date
        if filename is None:
            filename = Path(".").absolute() / "bookings_exported_%date_string%.csv"
        if "%date_string%" in filename.name:
            filename = filename.parent / str(filename.name).replace(
                "%date_string%", f"{start_date:%Y-%m-%d}_to_{end_date:%Y-%m-%d}"
            )
        with open(filename, "w", newline="\n", encoding="utf-8") as fp:
            fp.write("Date;Category;Type;Amount;Payee;Comment\n")
            for i in self:
                i: Booking
                if i.date > end_date:
                    break
                if i.date >= start_date:
                    fp.write(f"{i}\n")
        logger.info(f"Saved bookings to '{filename.absolute()}'")
        return filename.absolute()

    def append(self, booking: Booking, ignore_duplicates: bool = True):
        self.daterelation.setdefault(booking.date, [])
        if ignore_duplicates:
            for old_booking in self.daterelation[booking.date]:
                old_booking: Booking
                if (
                    old_booking.payee == booking.payee
                    and old_booking.amount == booking.amount
                ):
                    if not self.STRICT_COMPARING:
                        logger_dupes.warning(
                            f"Ignoring:\n"
                            f"{indent(str(booking), ' ' * 6)}\n  "
                            f"as possible duplicate of\n"
                            f"{indent(str(old_booking), ' ' * 6)}"
                        )
                        return
                    else:
                        old_comment = re.sub(
                            "[\n _-]+", "_", old_booking.comment
                        ).lower()
                        new_comment = re.sub("[\n _-]+", "_", booking.comment).lower()
                        if old_comment == new_comment:
                            logger_dupes.warning(
                                f"Ignoring:\n{indent(str(booking), ' '*6)}\n  "
                                f"as duplicate of\n{indent(str(old_booking), ' '*6)}"
                            )
                            return
        self.daterelation[booking.date].append(booking)
        super().append(booking)

    def _sum_by_attrib(self, attrib: str) -> Dict[str, float]:
        result = {}
        for i in self:
            i: Booking
            if not hasattr(i, attrib):
                raise ValueError(
                    f"Tried to sum by attrib {attrib} but {type(i)} "
                    f"does not have this attribute!"
                )
            key = getattr(i, attrib)
            if key not in result:
                result[key] = 0
            result[key] = result[key] + i.amount
        return result

    def sum_by_payee(self) -> Dict[str, float]:
        return self._sum_by_attrib("payee")

    def sum_by_category(self) -> Dict[str, float]:
        return self._sum_by_attrib("category")
