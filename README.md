# Description
This script allows to read PDF bank statements from the [GLS Bank](https://www.gls.de/). 
Even so the banks online manager supports exporting of CSV files, this works only for the past three month whereas PDF
account statements are kept for at least two years.

So if you forced to automatically analyse past bank transactions this script will help you.

The tool also supports reading the CSV files (which include more information), so you can analyse 

# Dependencies
 * `sed` (included in the most Linux distributions)
 * `python 3`
 * `jupyter-notebook`
 * `pdftotext`(part of [poppler-utils](https://poppler.freedesktop.org/))

# Usage
The script is intended to be used with the `jupyter-notebook` for fast analysing data.
See `example.ipynb` for an idea how to use it.

# Data Protection Note
As bank statement data is highly sensitive, only very general rules for categorizing were pushed to this git.

Use `statement_reader/bookings/personal.py` for customizations of categories and payees.
You only to create this file with a content like the following and it will be used automatically.

```python
from .booking_base import BookingBase

class Booking(BookingBase):
    def _set_payee(self, value: str):
        """your custom functions here"""
        super()._set_payee(value)
        
    def _get_category(self):
        """your custom stuff here"""
        return super()._get_category()

``` 
