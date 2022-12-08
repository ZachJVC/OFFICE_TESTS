
# -*- coding: utf-8 -*-
r"""
Main.py
    __  ___      _
   /  |/  /___ _(_)___
  / /|_/ / __ `/ / __ \
 / /  / / /_/ / / / / /
/_/  /_/\__,_/_/_/ /_/

@author: sportable
"""


# %% Import classes

import ConfigHandler
import DeviceManager
import ProductionTest
import TcpConnection
import UdpConnection


# %% RUN MAIN
if __name__ == "__main__":

    print('\n\n---------- SPORTABLE PRODUCTION TEST ----------\n\n')

    # Create config object
    config = ConfigHandler.configHandler()

    # Create connection objects
    udp = UdpConnection.udpConnection(
        UDP_IP=config.udpIP,
        UDP_PORT=config.udpPort)
    tcp = TcpConnection.tcpConnection(
        TCP_IP=config.tcpIP,
        TCP_PORT=config.tcpPort)

    # Create class to handle devices
    devices = DeviceManager.DeviceManager(
        udpConnection=udp, tcpConnection=tcp, config=config)

    # Set these devices as anchors, everything else will be a tag
    devices.makeAnchors(config.masterID)

    # %% Perform the production tests

    while True:

        # Create instance of production test class
        test = ProductionTest.ProductionTest(
            udpConnection=udp,
            tcpConnection=tcp,
            config=config,
            devices=devices)

        # Ensure that the DUTs are present - get user input to proceed, rescan
        # or abort
        test.userSpecifyIfProceed()

        # Enable bi-directional RSSI
        tcp.enableRssi(deviceType='anchor', devices=devices.anchors)
        tcp.enableRssi(deviceType='tag', devices=devices.tags)

        # Perform the range test
        rangeTestResults = test.rangeTest()

        # Perform the TX path test
        txTestResults = test.txTest()

        # Perform IMU test
        imuTestResults = test.imuTest()

        # Determine which devices passed / failed
        test.tagPassOrFail(
            rangeTestData=rangeTestResults,
            txTestData=txTestResults,
            imuTestData=imuTestResults)

        # Publish the raw data to individual excel files
        test.publishDataToExcel(
            rangeTestData=rangeTestResults,
            txTestData=txTestResults,
            imuTestData=imuTestResults)
