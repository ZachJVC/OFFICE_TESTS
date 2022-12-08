""" Imu class definition

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import csv

from typing import Optional
from src.datatypes import Gyro, Accel, Magnet

class Imu:
    def __init__(self,
                 serialNumber: Optional[str] = None,
                 csvImuFilePath: Optional[str] = None) -> None:
        self._gyro: Optional[Gyro] = None
        self._accel: Optional[Accel] = None
        self._magnet: Optional[Magnet] = None

        if csvImuFilePath and serialNumber:
            with open(csvImuFilePath) as imuCsvFile:
                csvReader = csv.DictReader(imuCsvFile)
                for line in reversed(list(csvReader)):
                    if line.get(f'IMU/{serialNumber.upper()}IMU time'):
                        self.parseCsvLine(serialNumber=serialNumber,
                                        csvLine=line)
                        break
    
    @property
    def gyro(self) -> Gyro:
        return self._gyro
    
    @gyro.setter
    def gyro(self, gyro: Gyro) -> None:
        self._gyro = gyro
    
    @property
    def accel(self) -> Accel:
        return self._accel
    
    @accel.setter
    def accel(self, accel: Accel) -> None:
        self._accel = accel
    
    @property
    def magnet(self) -> Magnet:
        return self._magnet
    
    @magnet.setter
    def magnet(self, magnet: Magnet) -> None:
        self._magnet = magnet

    def parseCsvLine(self, serialNumber: str, csvLine: dict) -> None:
        self.gyro = Gyro(X=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Gyro X')),
                         Y=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Gyro Y')),
                         Z=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Gyro Z')))
        self.accel = Accel(X=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Accel X')),
                           Y=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Accel Y')),
                           Z=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Accel Z')))
        self.magnet = Magnet(X=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Magnet X')),
                             Y=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Magnet Y')),
                             Z=float(csvLine.get(f'IMU/{serialNumber.upper()}IMU Magnet Z')))
    
    def __str__(self) -> str:
        return str(f"IMU Gyro X: {self.gyro.X}\n"
                   f"IMU Gyro Y: {self.gyro.Y}\n"
                   f"IMU Gyro Z: {self.gyro.Z}\n"
                   f"IMU Accel X: {self.accel.X}\n"
                   f"IMU Accel Y: {self.accel.Y}\n"
                   f"IMU Accel Z: {self.accel.Z}\n"
                   f"IMU Magnet X: {self.magnet.X}\n"
                   f"IMU Magnet Y: {self.magnet.Y}\n"
                   f"IMU Magnet Z: {self.magnet.Z}")