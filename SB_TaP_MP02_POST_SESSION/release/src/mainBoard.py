"""Implements main board production testing. Running the --boot option first is required.

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import os
import src.boot as boot
import src.datatypes as dt
import src.tagDialog as dlg
import src.prettyPrint as pretty
import src.testUtils as tu
import src.sportableCommon as common

from src.waitIndicator import WaitIndicator
from src.versions import Versions
from src.productionConfig import ProductionConfig
from src.firmwareVersion import QACivetFirmwareVersion, ReleaseCivetFirmwareVersion

MASTER_PROMPT_DELAY = 60
TAG_CONNECT_WAIT_TIME = 10
TAG_RESET_WAIT_TIME = 5
SESSION_RECORDING_DELAY = 20

def mbTest(args,
           config: ProductionConfig,
           test: tu.TestUtilities,
           qaFirmware: QACivetFirmwareVersion):
    try:
        waitIndicator = WaitIndicator()
        dutVersions = None

        #----------------------------------------------------------------------
        # Get serial number scan
        #----------------------------------------------------------------------

        print()
        test.serialNumber = common.getSportableUniqueDeviceId(config.issuedDeviceIds, args.skipConfigCheck)
        print()
        common.getBooleanInputFromOperator('Is the battery connected to the PCB?')
        print()

        #----------------------------------------------------------------------
        # Start the Test
        #----------------------------------------------------------------------

        test.startTest()
        print()

        #----------------------------------------------------------------------
        # Use JTAG to flash the app
        #----------------------------------------------------------------------

        if not args.noFlash:
            test.tagId = common.getTagIdFromJtag(test)
            boot.boot(test,
                      qaFirmware.appImagePathBankAHex,
                      qaFirmware.appImagePathBankBHex,
                      qaFirmware.mbrImagePath)
            print()
        else:
            test.tagId = common.autoFindTagId('./attachedTags.csv')

        #----------------------------------------------------------------------
        # Create daemon config file
        #----------------------------------------------------------------------

        test.initDaemon(targetProduct="Civet", debug=args.debug)
        test.createDaemonConfig(dutType="CIVET",
                                dutBlocking=False)
        test.createImuConfig(dutType="CIVET")
        test.createPsrConfig(dutType="CIVET")
        
        #----------------------------------------------------------------------
        # Start the Daemon
        #----------------------------------------------------------------------

        test.startDaemon()
        test.waitForTagConnection(timeout=TAG_CONNECT_WAIT_TIME)

        #----------------------------------------------------------------------
        # Use daemon to flash mcuwb
        #----------------------------------------------------------------------
        
        if not args.noFlash:
            test.useAeolusPy = True
            try:
                print()
                test.flashFirmware(fwImageVersion=qaFirmware,
                                   device="Uwb",
                                   useHardwareId=True)
            except Exception as error:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
                test.flashFirmware(fwImageVersion=qaFirmware,
                                   device="Uwb",
                                   useHardwareId=True)
            finally:
                waitIndicator.stop()
            common.waitWithLiveCounter(TAG_RESET_WAIT_TIME)
            print()

        #----------------------------------------------------------------------
        # Check firmware version after update
        #----------------------------------------------------------------------
        
        test.addRawToLog("\nVersions after update")
        try:
            dutVersions = test.getDutFwVersions()
        except:
            test.resetDut()
            common.waitWithLiveCounter(TAG_RESET_WAIT_TIME)
            dutVersions = test.getDutFwVersions()
        print()
        test.printVersions(dutVersions)
        test.logQAVersions(dutVersions)

        if ((dutVersions.uwbMcuVersion == qaFirmware.uwbVersion) and
            (dutVersions.appMcuVersion == qaFirmware.appVersion) and
            (dutVersions.appMcuVersion.firmwareType == qaFirmware.appVersion.firmwareType)):
            print()
            pretty.printInfo("The MCUWB and MCUAPP QA version successfully uploaded")
            # Uncomment when needed
            test.addBooleanRecordToLog("QA_Versions_Upload", True)
        else:
            print()
            pretty.printInfo("The MCUWB and MCUAPP QA version unsuccessfully uploaded")
            # Ucommend when needed
            test.addBooleanRecordToLog("QA_Versions_Upload", False)

        #----------------------------------------------------------------------
        # Program the device ID
        #----------------------------------------------------------------------
        
        if not args.quick:
            test.addRawToLog("\nDevice Id Programming")
            print()
            #common.ensureMasterOff("Civet", MASTER_PROMPT_DELAY)    Sometimes requires master off before, to uncomment if necessary
            test.setSerialNumber()
            print()
            common.getBooleanInputFromOperator('Power cycle the tag, then enter y to continue')
            test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
        
        #----------------------------------------------------------------------
        # Read the hardware variant from the device
        # If not programmed, program to what is specified in production config.
        # If it is programmed, check it matches the production config.
        # - exit if not matched (unless flag to ignore config mismatch is set). 
        # - skip programming if it is matched.
        #----------------------------------------------------------------------

        print()
        common.ensureMasterOn("Civet", MASTER_PROMPT_DELAY)
        test.addRawToLog("\nHardware Variant before programming")
        try:
            test.getHardwareVariant()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
            test.getHardwareVariant()
        print()
        test.printHardwareVariant("AppMcu", test.hardwareVariantAppMcu)
        test.logHardwareVariant("Pre", "AppMcu", test.hardwareVariantAppMcu)

        #----------------------------------------------------------------------
        # Erase Hardware Variant
        #----------------------------------------------------------------------

        if args.eraseHV:
            try:
                print()
                test.eraseHardwareVariant()
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
                test.eraseHardwareVariant()

        if ((not args.quick) and (not args.noVariant)):
            test.checkHardwareVariant(args=args, config=config)
            try:
                test.setHardwareVariant(hw_variant=config.hardwareVariant)
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
                test.setHardwareVariant(hw_variant=config.hardwareVariant)
            test.addRawToLog("\nHardware Variant after programming")
            try:
                print()
                test.getHardwareVariant()
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
                test.getHardwareVariant()
            print()
            test.printHardwareVariant("AppMcu", test.hardwareVariantAppMcu)
            test.logHardwareVariant("Post", "AppMcu", test.hardwareVariantAppMcu)

            if test.hardwareVariantAppMcu != config.hardwareVariant:
                test.addBooleanRecordToLog("Hardware_Variant_Programming", False)
                raise Exception("Programming hardware variant to AppMcu failed.")
            else :
                test.addBooleanRecordToLog("Hardware_Variant_Programming", True)

        #----------------------------------------------------------------------
        # HMI test
        #----------------------------------------------------------------------
        
        test.addRawToLog("\nHMI Implementation")
        print()
        test.checkRGBLED()
        test.checkWhiteLED()

        #----------------------------------------------------------------------
        # Current readings
        #----------------------------------------------------------------------

        test.addRawToLog("\nCurrent measurements")

        extendedBattery = dt.ExtendedBattery()
        try:
            extendedBattery = test.getExtendedBattery()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
            extendedBattery = test.getExtendedBattery()
        print()
        test.printExtendedBattery(extendedBattery)
        test.logExtendedBattery(extendedBattery)
        print()
        test.disableCharger()
        test.recordCurrent("IN_SESSION_CURRENT")
        test.stopSession()
        test.recordCurrent("STANDBY_CURRENT")
        test.enableCharger()
        test.recordCurrent("CHARGE_CURRENT")

        #----------------------------------------------------------------------
        # Offload metrics
        #----------------------------------------------------------------------

        test.retrieveData()
        test.parseDeviceContext()

        test.addRawToLog("\nMCU Implementation Testing: Clocks")
        try:
            rtcRatio = test.getRtcRatio()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
            rtcRatio = test.getRtcRatio()
        print()
        test.printRtcRatio(rtcRatio=rtcRatio)
        test.logRtcRatio(rtcRatio=rtcRatio)

        test.addRawToLog("\nPeripherals: IMU")
        try:
            imuData = test.getImuData()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
            imuData = test.getImuData()
        print()
        test.printImu(imuData=imuData)
        test.logImu(imuData=imuData)

        test.addRawToLog("\nUWB")
        try:
            avgPsr = test.getPsrData()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(dutTimeout=TAG_CONNECT_WAIT_TIME)
            avgPsr = test.getPsrData()
        print()
        test.printPsr(avgPsr)
        test.logPsr(avgPsr)
        print()
        test.appendErrorReports()
    except Exception as error:
        if 'test' in locals():
            test.addRecordToLog("ERROR", str(error))
        if __name__ == "__main__": # If standalone app
            pretty.printError("Error: "+str(error))
            exit()
        else:
            raise error
    finally:
        if test:
            test.finishTest()
            test.copyDaemonLogFile()
            test.closeAllConnections()
            if test.daemon:
                test.closeDaemon()
