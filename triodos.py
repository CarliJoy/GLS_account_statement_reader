from IPython.core.display import display
import os
from statement_reader import csv2bookings, pdf2bookings, txt2bookings

bookings = None
os.chdir("/home/daten/Eigene/Privat/Finanzen/Triodos/")

for fn in sorted(list(os.listdir("."))):
    if fn.endswith(".pdf"):
        print(fn)
        if bookings is None:
            bookings = pdf2bookings(fn)
        else:
            bookings += pdf2bookings(fn)