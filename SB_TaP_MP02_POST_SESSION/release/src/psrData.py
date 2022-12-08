""" Psr class definition

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import csv

from typing import Optional

class Psr:
    def __init__(self,
                 serialNumber: Optional[str] = None,
                 csvPsrFilePath: Optional[str] = None) -> None:

        if csvPsrFilePath and serialNumber:
            with open(csvPsrFilePath) as psrCsvFile:
                csvReader = csv.DictReader(psrCsvFile)
                for line in reversed(list(csvReader)):
                    if line.get(f'psrData/{serialNumber.upper()}PSR'):
                        self.parseCsvLine(serialNumber=serialNumber,
                                          csvLine=line)
                        break

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = val

    def parseCsvLine(self, serialNumber: str, csvLine: dict) -> None:
        self.value = csvLine.get(f'psrData/{serialNumber.upper()}PSR')
    
    def __str__(self) -> str:
        return str(f"PSR value: {self.value}")