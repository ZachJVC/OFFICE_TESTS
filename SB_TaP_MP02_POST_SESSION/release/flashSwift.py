#!/usr/bin/python3

"""Flash Swift device application
    Author: Tym
    Date: 12 Dec 2021
    Copyright (c) 2020-2022, Sportable Technologies. All rights reserved.
"""

import argparse
import src.dfu as dfu
import src.testUtils as tu
import src.swift as swift
import src.datatypes as dt
import src.tagDialog as dlg
import src.prettyPrint as pretty
import src.sportableCommon as common

from src.versions import Versions
from src.firmwareVersion import QASwiftFirmwareVersion, ReleaseSwiftFirmwareVersion

def uploadFirmware(swiftDev: tu.TestUtilities,
                   firmwareVersion: Versions):
    try:   
        swiftDev.flashFirmware(fwImageVersion=firmwareVersion, device="App")
    except:
        print()
        common.resetDevicePrompt()
        print()
        swiftDev.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
        swiftDev.flashFirmware(fwImageVersion=firmwareVersion, device="App")
    common.waitWithLiveCounter(TAG_CONNECT_WAIT_TIME)
    print()
    try:
        swiftDev.flashFirmware(fwImageVersion=firmwareVersion, device="Uwb")
    except:
        print()
        common.resetDevicePrompt()
        print()
        swiftDev.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
        swiftDev.flashFirmware(fwImageVersion=firmwareVersion, device="Uwb")
    common.waitWithLiveCounter(TAG_CONNECT_WAIT_TIME)
    print()

if __name__ == "__main__":
    DAEMON_DELAY = 5
    TAG_CONNECT_WAIT_TIME = 10
    TCP_SOCKET = 8694
    try:
        parser = argparse.ArgumentParser(
            description='Production testing Software (Sportable Technologies Ltd.)')

        parser.add_argument(
            '-i',
            '--internal',
            dest='intImage',
            action='store_true',
            default=False,
            help='Flash internal image.')
        
        parser.add_argument(
            '-d','--debug',
            dest='debug',
            action='store_true',
            default=False,
            help='Enable daemon debug (Does not run daemon internaly '
                 'to allow for running daemon in GDB)')

        args = parser.parse_args()
        swiftDev = tu.TestUtilities("Swift", dt.product.SWIFT)

        #----------------------------------------------------------------------
        # Initialise firmware images
        #----------------------------------------------------------------------

        qaFirmwareVersions = QASwiftFirmwareVersion()
        releaseFirmwareVersions = ReleaseSwiftFirmwareVersion()
        dlg.initPipes()

        #----------------------------------------------------------------------
        # Prepare devices for test
        #----------------------------------------------------------------------
 
        if dfu.isInDFUMode():
            dfu.leaveDFUMode()

        #----------------------------------------------------------------------
        # Find Swift Serial Number
        #----------------------------------------------------------------------

        serialNumber = str(swift.getProgrammedSwiftId()).upper()
        if not serialNumber:
            raise Exception("Cannot find the DUT's Serial Number." +
                            "\nPlease check if the DUT is connected.")
        swiftDev.serialNumber = serialNumber
        print("Device Serial Number:", swiftDev.serialNumber)

        #----------------------------------------------------------------------
        # Create daemon config file
        #----------------------------------------------------------------------

        swiftDev.initDaemon(targetProduct="Swift", debug=args.debug)
        swiftDev.createDaemonConfig(dutType="SWIFT",
                                    dutBlocking=False)
        swiftDev.startDaemon()
        
        #----------------------------------------------------------------------
        # Find Device Id
        #----------------------------------------------------------------------

        deviceId = swiftDev.findDeviceId(devType="Swift")
        if not deviceId:           
            raise Exception("Failed to find the Device Id.")
        swiftDev.tagId = deviceId["DeviceId"]
        print("Device Id:", swiftDev.tagId)

        #----------------------------------------------------------------------
        # Upload firmware images
        #----------------------------------------------------------------------
        
        if args.intImage:
            uploadFirmware(swiftDev=swiftDev,
                           firmwareVersion=qaFirmwareVersions)
        else:
            uploadFirmware(swiftDev=swiftDev,
                           firmwareVersion=releaseFirmwareVersions)

        #----------------------------------------------------------------------
        # Check firmware version after update
        #----------------------------------------------------------------------

        try:
            dutVersions = swiftDev.getDutFwVersions()
        except:
            print()
            common.resetDevicePrompt()
            swiftDev.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
            dutVersions = swiftDev.getDutFwVersions()
        print()
        swiftDev.printVersions(dutVersions)
        if args.intImage:
            if ((dutVersions.uwbMcuVersion == qaFirmwareVersions.uwbVersion) and
                (dutVersions.appMcuVersion == qaFirmwareVersions.appVersion) and
                (dutVersions.appMcuVersion.firmwareType == qaFirmwareVersions.appVersion.firmwareType)):
                print()
                pretty.printInfo("The MCUWB and MCUAPP QA version successfully uploaded")
            else:
                print()
                pretty.printInfo("The MCUWB and MCUAPP QA version unsuccessfully uploaded")
        else:
            if ((dutVersions.uwbMcuVersion == releaseFirmwareVersions.uwbVersion) and
                (dutVersions.appMcuVersion == releaseFirmwareVersions.appVersion) and
                (dutVersions.appMcuVersion.firmwareType == releaseFirmwareVersions.appVersion.firmwareType)):
                print()
                pretty.printInfo("The MCUWB and MCUAPP Release version successfully uploaded")
            else:
                print()
                pretty.printInfo("The MCUWB and MCUAPP Release version unsuccessfully uploaded")
    except Exception as error:
        pretty.printError("Error: " + str(error))
    finally:
        if swiftDev:
            swiftDev.copyDaemonLogFile()
            swiftDev.closeAllConnections()
            swiftDev.closeDaemon()
        print("Exiting script")