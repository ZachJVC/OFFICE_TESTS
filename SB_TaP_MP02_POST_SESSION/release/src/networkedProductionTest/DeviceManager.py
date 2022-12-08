#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
DeviceManager.py
    ____            _              __  ___
   / __ \___ _   __(_)_______     /  |/  /___ _____  ____ _____ ____  _____
  / / / / _ \ | / / / ___/ _ \   / /|_/ / __ `/ __ \/ __ `/ __ `/ _ \/ ___/
 / /_/ /  __/ |/ / / /__/  __/  / /  / / /_/ / / / / /_/ / /_/ /  __/ /
/_____/\___/|___/_/\___/\___/  /_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/
                                                        /____/

@author: sportable
"""


class deviceManager():
    """
    A class which gets the devices in the network
    and prepares list of anchors, tags, duts
    """

    # pylint: disable=too-many-instance-attributes
    # Ten is reasonable in this case.

    def __init__(self, **kwargs):
        self.udp = kwargs['udpConnection']
        self.tcp = kwargs['tcpConnection']
        self.config = kwargs['config']
        self.duts = []
        self.tags = []
        self.anchors = []
        self.getDevices()

    def getDevices(self):
        """ Creates lists of duts"""
        self.devices = self.udp.getDevices()
        self.numDevices = len(self.devices)
        self.master = self.config.masterID
        for device in self.devices:
            if device != self.config.masterID:
                self.duts.append(self.devices[device])
        self.numDuts = len(self.duts)

    def makeAnchors(self, deviceList):
        """ Creates lists of anchors and tags"""
        if isinstance(deviceList, list):
            self.anchors = deviceList
        elif isinstance(deviceList, str):
            self.anchors = [deviceList]
        for device in self.devices:
            if device not in self.anchors:
                self.tags.append(self.devices[device])
