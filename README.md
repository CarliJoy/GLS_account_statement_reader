# Description
This script allows to read PDF bank statements from the [GLS Bank](https://www.gls.de/).
Even so, the banks online manager supports exporting of CSV files, this works only for the past three month whereas PDF
account statements are kept for at least two years.

So if, you forced to automatically analyse past bank transactions, this script will help you.

The tool also supports reading the CSV files (which include more information), so you can analyse them.

I also tested it with Banking records from the [Triodos Bank](https://www.triodos.de/)
and it works well. They both using the same banking system, so maybe also other
"Volksbank" or "Raiffeisenbank" work as well. Write me an issue

I tested it with the following Banking records so far:
* GLS 2014-2020
* Triodos 2020

# Dependencies
* `python >= 3.6`
* `pdftotext`(part of [poppler-utils](https://poppler.freedesktop.org/))
* `jupyter-notebook` [Optional]


# Installation


## Variant One
 Install using `pip install bank-statement-reader`

Advantage:
 * Easy to install

Disadvantage:
 * some features like the `booking/personal.py` file depend on modifying the package
   the package source before installing, which won't work using this
   method

## Variant Two
Clone the repro locally, create and activate a new virtual environment
and run `pip install -e .` within the project folder.

# Usage

After installation, you have a new command `statement2csv` available.
```
usage: statement2csv [-h] [--out out.csv] statement.pdf [statement.pdf ...]

Convert banking statements (PDF & CSV) to an analysed standard csv form.

positional arguments:
  statement.pdf  files to open and convert

optional arguments:
  -h, --help     show this help message and exit
  --out out.csv  csv file to write the results to

        If no filename is given, the file will be saved to
            basename_first_file_%date_string%.csv.
        %date_string% will be always replaced to 'YYYY-mm-dd_to_YYYY-mm-dd'
                                                 start date  to   end date
```

Another way to use the project is to use  `jupyter-notebook` for fast analysing data.
See `example.ipynb` for an idea how to use it.

# Data Protection Note
As bank statement data is highly sensitive, only very general rules for categorizing were pushed to this git.

Use `src/bank_statement_reader/bookings/personal.py` for customizations of categories and payees.
You only to create this file with a content like the following, and it will be used automatically.

```python
from bank_statement_reader.booking.booking_base import BookingBase

class Booking(BookingBase):
    def _set_payee(self, value: str):
        """your custom functions here"""
        super()._set_payee(value)

    def _get_category(self):
        """your custom stuff here"""
        return super()._get_category()
```
