import re


class BookingBase:
    type_convert = {'SEPA-Basislastschrift': "Lastschrift",
                    'SEPA-Kartenlastschrift': "EC-Kartenzahlung",
                    "Lastschrift": "Lastschrift",
                    'Rücklastschr. mang. Deckung': "Rücklastschrift",
                    'Auszahlung girocard': "Bargeldabhebung",
                    'Kartenzahlung girocard': "EC-Kartenzahlung",
                    'Kartenzahlung Maestro': "EC-Kartenzahlung",
                    'Dauer-Euro-Überweisung': "Überweisung",
                    'Kontoführung': "Kontogebühren",
                    'Überweisungs-Gutschrift': "Überweisung",
                    'Kartenzahlung': "EC-Kartenzahlung",
                    'Kartenzahlung Debitkarte': "EC-Kartenzahlung",
                    'Lohn-,Gehalt-,Renten-Gutsch': "Gehalt",
                    'Auszahlung': "Bargeldabhebung",
                    'Bargeldauszahlg. Debitkarte': "Bargeldabhebung",
                    'Internet-Euro-Überweisung': "Überweisung",
                    'Kartengenerierte Lastschr.': "EC-Kartenzahlung",
                    'Kontogebühren': "Kontogebühren",
                    'Gebühren allgemein': "Kontogebühren",
                    'Zinsen/Kontoführung': "Kontogebühren",
                    'GLS BankCard Gebühr': "Kontogebühren"}

    def __init__(self):
        self._type = None
        self.date: str = None
        self.amount: float = None
        self._wrong_type = None
        self.comment = ""

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str):
        """
        Set the type of transaction - can be done only once and has to be a valid type!
        """
        value = re.sub("Wertstellung: [0-9]{2}.[0-9]{2}.", "", value).strip()
        type_convert = self.__class__.type_convert
        if value in type_convert and self._type is None:
            self._type = type_convert.get(value)
        elif value not in type_convert:
            self._wrong_type = value
            print(f"Unkown booking type '{value}'")
        else:
            if value != self._type:
                print(f"Reset type from '{self._type}' ({self._wrong_type}) to '{value}'")
                self._type = value

    @property
    def payee(self) -> str:
        if not self._payee.strip() and self.type == "Kontogebühren":
            return "GLS Bank"
        else:
            return self._payee

    def _set_payee(self, value: str):

        beginnings = ["TAZ", "POCO", "REWE", "Denns", "DEBEKA", "Allianz", "IKK", "OBI ", "DB ", "Rossmann",
                      "Thalia", "Combi ", "AKTIV UND IRMA", "KFW", ]

        contains = {"SATURN": "Saturn", "FRISCHEMARKT": "EDEKA", "EDEKA": "EDEKA", "LIDL": "LIDL" }

        paypals = {"spotify": "Spotify", "MUDJEANS": "Mudjeans", "TAZ": "TAZ"}

        if self._wrong_type is not None:
            print("Assuming the invalid booking type is payee")
            self.comment = f"{value} {self.comment}".strip()
            value = self._wrong_type
            self._type = "Überweisung"

        for beginn in beginnings:
            if value.lower().strip().startswith(beginn.lower()):
                self._payee = beginn.strip()
                return

        for key, val in contains.items():
            if key.lower() in value.lower():
                self._payee = val
                return

        if value.startswith("PayPal"):
            # Set Booking Type correctly
            self._type = "PayPal"
            self._payee = None
            for key, val in paypals.items():
                if key.lower() in self.comment.lower():
                    self._payee = val
                    break
            if self._payee is None:
                self._payee = "PayPal"
        elif value.upper().startswith("DM FIL"):
            self._payee = "DM"
        elif "ingenico" in value.lower() and "ross" in self.comment.lower():
            self._payee = "Rossmann"
        else:
            self._payee = value

    @payee.setter
    def payee(self, value: str):
        self._set_payee(value)

    def _get_category(self) -> str:
        insurances = ["IKK", "Allianz", "DEBEKA"]
        newspaper = ["TAZ", "Stiftung Warentest", ]
        grocery = ["Combi", "EDEKA", "AKTIV UND IRMA", "Combi", "REWE", "Denns", "Superbiomarkt", "LIDL"]
        anschaffung_sonstig = ["PayPal", "AMAZON", "Pollin", "Saturn", "Reichelt"]
        if self.type == "Bargeldabhebung":
            return "Cash Withdrawal"
        elif self.type == "Kontogebühren":
            return "Financial expenses > Bank charges"
        elif "GLS Beitrag" in self.comment:
            self.type = "Kontogebühren"
            return "Financial expenses > Bank charges"
        elif self.type == "Gehalt":
            return "Einnahmen > Gehalt"
        elif self.payee in insurances:
            return "Insurance"
        elif self.payee in grocery:
            return "Nahrung > Grocery"
        elif self.payee in anschaffung_sonstig:
            return "Anschaffungen > Sonstiges"
        elif self.payee == "KFW":
            return "Loan"
        elif self.payee == "DB":
            return "Transport > Train"
        elif self.payee == "Spotify":
            return "Leisures > Music"
        elif self.payee == "Mudjeans":
            return "Care > Clothing"
        elif self.payee == "DM" or self.payee == "Rossmann":
            return "Care > Careproducts"
        elif "APOTHEKE" in self.payee.upper():
            return "Health > Chemist"
        elif self.payee in newspaper:
            return "Education > Newspaper"
        elif self.payee == "Thalia":
            return "Education > Books"
        elif "miete" in self.comment.lower():
            return "Miete"
        else:
            return ""

    @property
    def category(self) -> str:
        return self._get_category()

    def __str__(self):
        return f'{self.date};{self.category};{self.type};{self.amount:.2f};{self.payee};"{self.comment}"'

    @property
    def _tr_(self):
        comment = self.comment.replace("\n", " ")
        return f"<td>{self.date}</td><td>{self.category}</td><td>{self.type}</td><td class='number_cell'>{self.amount:.2f}</td><td>{self.payee}</td><td class='comment_cell'>{comment}</td>"
