#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Production Test Configuration Parser

Author: Chris Paine

Copyright (c) 2021, Sportable Technologies. All rights reserved.

"""

import json
from typing import Optional
import src.datatypes as dt

class ProductionConfig:
    def __init__(self, filename):
        self._identifier: Optional[str] = None
        self._hardwareVariant: Optional[dt.HardwareVariant] = None
        self._commandLineArguments:Optional[list] = None
        self._issuedDeviceIds: Optional[list] = None
        self._masterDeviceSerialNumber: Optional[str] = None
        data: Optional[dict] = None
        with open(str(filename), "r") as f:
            try:
                data = json.load(f)
            except Exception as error:
                raise json.JSONDecodeError(
                    f"Parsing production config file "
                    f"'{str(filename)}' failed with error:\n\t{str(error)}")
        # Set Identifier
        self._identifier = data.get('identifier')
        # Set hardware Variant
        self._hardwareVariant = dt.HardwareVariant()
        temp = data.get('hardwareVariant', {})
        self._hardwareVariant.pcbType = temp.get('pcbType')
        self._hardwareVariant.pcbRevision = temp.get('pcbRevision')
        self._hardwareVariant.bomVariant = temp.get('bomVariant')
        self._hardwareVariant.bomRevision = temp.get('bomRevision')
        self._hardwareVariant.assemblyVariant = temp.get('assemblyVariant')
        # Get arguments list
        self._commandLineArguments = list()
        self._commandLineArguments = data.get('commandLineArguments')
        # Extract issued devices list
        self._issuedDeviceIds = list()
        self._issuedDeviceIds = data.get('issuedDeviceIds')
        # Set master serial number
        self._masterDeviceSerialNumber = data.get('masterDeviceSerialNumber')
    
    @property
    def identifier(self):
        return self._identifier
    
    @property
    def hardwareVariant(self):
        return self._hardwareVariant

    @property
    def commandLineArguments(self):
        return self._commandLineArguments

    @property
    def issuedDeviceIds(self):
        return self._issuedDeviceIds
    
    @property
    def masterDeviceSerialNumber(self):
        return self._masterDeviceSerialNumber

# For debug purpose only        
def main():
    config = ProductionConfig('assets/productionConfig.json')
    print(config.issuedDeviceIds)
    print(config.hardwareVariant)
    print(config.identifier)
    print(config.commandLineArguments)
    print(config.masterDeviceSerialNumber)