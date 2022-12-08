#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
ConfigHandler.py
   ______            _____       __  __                ____
  / ____/___  ____  / __(_)___ _/ / / /___ _____  ____/ / /__  _____
 / /   / __ \/ __ \/ /_/ / __ `/ /_/ / __ `/ __ \/ __  / / _ \/ ___/
/ /___/ /_/ / / / / __/ / /_/ / __  / /_/ / / / / /_/ / /  __/ /
\____/\____/_/ /_/_/ /_/\__, /_/ /_/\__,_/_/ /_/\__,_/_/\___/_/
                       /____/

@author: sportable
"""
import sys
import json


class configHandler():  # pylint: disable=too-few-public-methods
    """
    A class which handles the config.json file and performs basic checks to
    ensure that there have been no user errors
    """

    def __init__(self):
        with open('config.json') as jsonFile:
            configData = json.load(jsonFile)

        self.masterID = configData['masterID']
        self.udpIP = configData['udpIP']
        self.udpPort = configData['udpPort']
        self.tcpIP = configData['tcpIP']
        self.tcpPort = configData['tcpPort']
        self.checkNetworkSettings()

    def checkNetworkSettings(self):
        """
        Checks that the network settings are formatted correctly and are meaningful
        Ensures there are no mistakes with port and IP address.
        """

        # Check IP addresses
        if not isinstance(self.udpIP, str):
            raise Exception('UDP IP address must be a string')
        elif not self.isIPAddressValid(self.udpIP):
            raise Exception('Invalid UDP IPV4 address')

        if not isinstance(self.tcpIP, str):
            raise Exception('TCP IP address must be a string')
        elif not self.isIPAddressValid(self.tcpIP):
            raise Exception('Invalid TCP IPV4 address')

         # Check ports
        if isinstance(self.udpPort, str):
            try:
                self.udpPort = int(self.udpPort)
            except BaseException:
                raise Exception('UDP port incorrectly formatted')
        elif not isinstance(self.udpPort, int):
            raise Exception('UDP port incorrectly formatted')

        if isinstance(self.tcpPort, str):
            try:
                self.tcpPort = int(self.tcpPort)
            except BaseException:
                raise Exception('TCP port incorrectly formatted')
        elif not isinstance(self.tcpPort, int):
            raise Exception('TCP port incorrectly formatted')

    @staticmethod
    def isIPAddressValid(ipAddress):
        """Checks for valid IPV4 address"""

        # Split the ip address into four numbers
        nums = ipAddress.split('.', 4)
        if len(nums) != 4:
            return False

        for i in nums:
            value = int(i)
            if (value < 0) or (value > 255):
                return False
        return True
