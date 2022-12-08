#!/usr/bin/env python3
"""Production test ball QA script.

Author: Tym Lek
Date: 12 Aug 2021

Copyright (c) 2021-2022, Sportable Technologies. All rights reserved.

"""

import os
from usb.core import USBError

import src.dfu as dfu
import src.datatypes as dt
import src.tagDialog as dlg
import src.testUtils as tu
import src.prettyPrint as pretty
import src.sportableCommon as common
import src.productionConfig as prodConf

import src.swift as swift
import src.civet as civet

from src.parser import Parser
from src.versions import Versions, Version
from src.firmwareVersion import QASwiftFirmwareVersion, ReleaseSwiftFirmwareVersion
from ballQAReportGenerator import ballReportGenerator

#------------------------------------------------------------------------------
# Class BallQA definition
#------------------------------------------------------------------------------

class BallQA(tu.TestUtilities):
    def __init__(self, test, targetProduct, sendMessage, sendErrorReport):
        super().__init__(test, targetProduct, sendMessage, sendErrorReport)
    
    #------------------------------------------------------------------------------
    # Print test header
    #------------------------------------------------------------------------------

    def printTestHeader(self, stage):
        print()
        print("*************************************************")
        print("                   " + str(stage) + " Test")
        print("*************************************************")
        print()

    #------------------------------------------------------------------------------
    # Ensure test stage
    #------------------------------------------------------------------------------
    
    def ensureTestStage(self):
        if self.test == dt.testStage.BOOT:
            parser.print_help()
            exit()
        if self.test == dt.testStage.BALL:
            self.printTestHeader(dt.testStage.BALL)
            if not common.ensureTestStage(dt.testStage.BALL):
                raise Exception("Wrong test")
        elif self.test == dt.testStage.BLADDER:
            self.printTestHeader(dt.testStage.BLADDER)
            if not common.ensureTestStage(dt.testStage.BLADDER):
                raise Exception("Wrong test")
        elif self.test == dt.testStage.VALVE:
            self.printTestHeader(dt.testStage.VALVE)
            if not common.ensureTestStage(dt.testStage.VALVE):
                raise Exception("Wrong test")

if __name__ == "__main__":
    try:
        TX_POWER_LEVEL_DEFAULT = 68
        TX_POWER_LEVEL_MIN = 1
        CURRENT_mA_MAX = 450
        DAEMON_DELAY = 5
        OLD_COMMANDS_MCUAPP = "v0.1.3.18"
        MIN_MCUAPP_FOR_HW03 = "v0.2.2.7"
        HW_VERSION_03 = 3
        MASTER_CONNECT_WAIT_TIME = 10
        DUT_CONNECT_WAIT_TIME = 10
        CheckVersion = True
        Flash: bool = True
        TestPass: bool = True
        serialNumber: str = None
        parser = Parser()
        ballQA: BallQA = None
        dutVersions: Versions = None
        masterVersions: Versions = None

        #----------------------------------------------------------------------
        # Initialise production config file
        #----------------------------------------------------------------------
        
        config = prodConf.ProductionConfig('./assets/productionConfig.json')

        args = parser.parse_args_list(config.commandLineArguments)
        
        if not args.skipConfigCheck:
            tu.TestUtilities.ensureHardwareVariant(config)

        #----------------------------------------------------------------------
        # Initialise arguments
        #----------------------------------------------------------------------

        if args.ensureStage:
            ballQA = BallQA(test=args.stage,
                            targetProduct=dt.product.SWIFT,
                            sendMessage=True,
                            sendErrorReport=True)
            ballQA.ensureTestStage()
        elif args.showMenu:
            args.stage = common.testMenu()
            ballQA = BallQA(test=args.stage,
                            targetProduct=dt.product.SWIFT,
                            sendMessage=True,
                            sendErrorReport=True)
        else:
            ballQA = BallQA(test=args.stage,
                            targetProduct=dt.product.SWIFT,
                            sendMessage=True,
                            sendErrorReport=True)
        
        if args.kickMenu:
            testType = common.kickMenu()
        
        brg = ballReportGenerator(ballQA.test)

        #----------------------------------------------------------------------
        # Initialise firmware images
        #----------------------------------------------------------------------
        
        dlg.initPipes()
        qaFirmwareVersions = QASwiftFirmwareVersion()
        releaseFirmwareVersions = ReleaseSwiftFirmwareVersion()
        
        #----------------------------------------------------------------------
        # Prepare devices for test
        #----------------------------------------------------------------------
 
        if dfu.isInDFUMode():
            dfu.leaveDFUMode()

        #----------------------------------------------------------------------
        # Find Master's and DUT's Serial Number
        #----------------------------------------------------------------------

        try:
            # Try using pyUSB library
            serialNumber = common.getSerialNumber("CLI_NH_SWIFT")
            if not serialNumber:
                raise USBError()
        except Exception:
            # Try using lsusb command
            serialNumber = swift.getProgrammedSwiftId()
            if not serialNumber:
                pretty.printError("The device under test is not detected on the USB"
                                  "\nPlease enter the serial number.")
                raise Exception("Cannot find the DUT's Serial Number." +
                                "\nPlease check if the DUT is connected.")

        try:
            masterSerialNumber = common.getSerialNumber("CLI_NH_CIVET")
            if not masterSerialNumber:
                raise USBError()
        except Exception:
            # Try using lsusb command
            masterSerialNumber = civet.getProgrammedCivetId()
        if not masterSerialNumber:
            raise Exception("Cannot find the Master's device Serial Number." +
                            "\nPlease check if the Master device is connected.")
        
        print()

        if args.confirmSerialNumber:
            if not common.getBooleanInputFromOperator(
                f'Is the S/N: {serialNumber} correct?'):
                raise Exception("Make sure only one ball is connected.")        

        ballQA.serialNumber=serialNumber
        ballQA.masterSerialNumber=masterSerialNumber

        #----------------------------------------------------------------------
        # Create daemon config file
        #----------------------------------------------------------------------

        ballQA.initDaemon(targetProduct="Swift", debug=args.debug)
        ballQA.createDaemonConfig(dutType="SWIFT",
                                  masterType="CIVET",
                                  dutBlocking=False)
        ballQA.createImuConfig(dutType="SWIFT")
        ballQA.createPsrConfig(dutType="SWIFT")
        
        #----------------------------------------------------------------------
        # Start the Daemon
        #----------------------------------------------------------------------

        ballQA.startDaemon()

        #----------------------------------------------------------------------
        # Find Devices' Ids
        #----------------------------------------------------------------------

        ballQA.findDevicesIds(deviceWaitTime=DUT_CONNECT_WAIT_TIME)
        if not ballQA.tagId:
            print()
            pretty.printError("Failed to find the DUT device.")
            raise Exception("Failed to find the DUT device.")
        if not ballQA.masterId:
            print()
            pretty.printError("Failed to find the Master device.")
            raise Exception("Failed to find the Master device.")
        print("Master Id:", ballQA.masterId)
        print("DUT Id:", ballQA.tagId)
        print()


        #----------------------------------------------------------------------
        # Start test
        #----------------------------------------------------------------------

        ballQA.startTest()
        if args.kickMenu:
            if testType == dt.testType.PRE_KICK:
                ballQA.addRecordToLog("SUB_STEP","Pre-kick")
                args.noRelFlash = True
            else:
                ballQA.addRecordToLog("SUB_STEP","Post-kick")
                args.noRelFlash = False


        #----------------------------------------------------------------------
        # Reset the Master device
        #----------------------------------------------------------------------

        ballQA.resetMasterDevice()
        common.waitWithLiveCounter(DAEMON_DELAY)
        print()
        ballQA.resetDut()
        common.waitWithLiveCounter(DAEMON_DELAY)
        print()

        #----------------------------------------------------------------------
        # Check if issued by Sportable
        #----------------------------------------------------------------------
        
        if (not args.skipConfigCheck and not (str(ballQA.serialNumber).upper() in config.issuedDeviceIds)):
            raise Exception(f"Warning! {str(ballQA.serialNumber)} has not been issued by Sportable.")

        #----------------------------------------------------------------------
        # Get the Master and the Daemon versions
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nMaster and Daemon Versions")     
        try:
            masterVersions = ballQA.getMasterFwVersions()
        except:
            print()
            common.resetMasterPrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            masterVersions = ballQA.getMasterFwVersions()    
        print()
        ballQA.printVersions(masterVersions)
        ballQA.logMasterVersions(masterVersions)

        #----------------------------------------------------------------------
        # Get firmware version before update
        #----------------------------------------------------------------------
        """
        ballQA.addRawToLog("\nVersions before update")
        try:
            dutVersions = ballQA.getDutFwVersions()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                    dutTimeout=DUT_CONNECT_WAIT_TIME)
            dutVersions = ballQA.getDutFwVersions()
        print()
        ballQA.printVersions(dutVersions)
        ballQA.logVersions(dutVersions)

        # UwbMcu checked here, and not before flashing UWB,
        # because we do not have a way to differentiate between QA and Release versions for UwbMcu
        if ((dutVersions.uwbMcuVersion == qaFirmwareVersions.uwbVersion) and
            (dutVersions.appMcuVersion == qaFirmwareVersions.appVersion) and
            (dutVersions.appMcuVersion.firmwareType == qaFirmwareVersions.appVersion.firmwareType)):
            print()
            pretty.printInfo("The MCUWB and MCUAPP QA version already uploaded")
            Flash = False
            CheckVersion = False

            ballQA.addRawToLog("\nVersions used for the QA")
            ballQA.logQAVersions(dutVersions)
            ballQA.addBooleanRecordToLog("DFU_MODE_QA", True)
            ballQA.addBooleanRecordToLog("QA_Versions_Upload", True)

	"""
        #----------------------------------------------------------------------
        # Upload firmware images
        #----------------------------------------------------------------------
        
        if ((not args.noFlash) and Flash):
            ballQA.addRawToLog("\nInternal image upload")
            print()
            try:
                ballQA.flashFirmware(fwImageVersion=qaFirmwareVersions,
                                     dutVersions=dutVersions,
                                     device="App")
            except:
                print()
                common.resetDevicePrompt()
                print()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                ballQA.flashFirmware(fwImageVersion=qaFirmwareVersions,
                                     dutVersions=dutVersions,
                                     device="App")
            common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
            print()
            
            try:
                ballQA.flashFirmware(fwImageVersion=qaFirmwareVersions,
                                     device="Uwb")
            except:
                print()
                common.resetDevicePrompt()
                print()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                ballQA.flashFirmware(fwImageVersion=qaFirmwareVersions,
                                     device="Uwb")
            common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
            print()

        #----------------------------------------------------------------------
        # Check firmware version after update
        #----------------------------------------------------------------------
        
        if CheckVersion:
            ballQA.addRawToLog("\nVersions after update")
            try:
                dutVersions = ballQA.getDutFwVersions()
            except:
                print()
                common.resetDevicePrompt()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                dutVersions = ballQA.getDutFwVersions()
            print()
            ballQA.printVersions(dutVersions)
            ballQA.logQAVersions(dutVersions)

            if ((dutVersions.uwbMcuVersion == qaFirmwareVersions.uwbVersion) and
                (dutVersions.appMcuVersion == qaFirmwareVersions.appVersion) and
                (dutVersions.appMcuVersion.firmwareType == qaFirmwareVersions.appVersion.firmwareType)):
                print()
                pretty.printInfo("The MCUWB and MCUAPP QA version successfully uploaded")
                # Uncomment when needed
                ballQA.addBooleanRecordToLog("QA_Versions_Upload", True)
            else:
                print()
                pretty.printInfo("The MCUWB and MCUAPP QA version unsuccessfully uploaded")
                # Ucommend when needed
                ballQA.addBooleanRecordToLog("QA_Versions_Upload", False)
                TestPass = False

        #----------------------------------------------------------------------
        # Retrieve Hardware Variant
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nHardware Variant before programming")
        try:
            ballQA.getHardwareVariant()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            ballQA.getHardwareVariant()

        print()
        ballQA.printHardwareVariant("AppMcu", ballQA.hardwareVariantAppMcu)
        ballQA.logHardwareVariant("Pre", "AppMcu", ballQA.hardwareVariantAppMcu)

        #----------------------------------------------------------------------
        # Program Hardware Variant
        #----------------------------------------------------------------------

        if not args.noVariant:
            ballQA.checkHardwareVariant(args=args, config=config)
            try:
                ballQA.setHardwareVariant(hw_variant=config.hardwareVariant)
            except:
                print()
                common.resetDevicePrompt()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                ballQA.setHardwareVariant(hw_variant=config.hardwareVariant)

        #----------------------------------------------------------------------
        # Retrieve Hardware Variant
        #----------------------------------------------------------------------

        if not args.noVariant:
            ballQA.addRawToLog("\nHardware Variant after programming")
            try:
                print()
                ballQA.getHardwareVariant()
            except:
                print()
                common.resetDevicePrompt()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                ballQA.getHardwareVariant()

            print()
            ballQA.printHardwareVariant("AppMcu", ballQA.hardwareVariantAppMcu)
            ballQA.logHardwareVariant("Post", "AppMcu", ballQA.hardwareVariantAppMcu)

            if ((ballQA.hardwareVariantAppMcu != config.hardwareVariant) and
                (not args.skipConfigCheck)):
                ballQA.addBooleanRecordToLog("Hardware_Variant_Programming", False)
                TestPass = False
                raise Exception("Programming hardware variant to AppMcu failed.")
            else:
                ballQA.addBooleanRecordToLog("Hardware_Variant_Programming", True)

        #----------------------------------------------------------------------
        # Download metrics from the flash memory
        #----------------------------------------------------------------------

        print()
        pretty.printInfo("Retrieving data ...")

        try:
            ballQA.stopSession()
            ballQA.retrieveData()
        except:
            print()
            common.resetDevicePrompt()
            print()
            pretty.printInfo("Retrieving data ...")
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            ballQA.stopSession()
            ballQA.retrieveData()

        #----------------------------------------------------------------------
        # Log collected metrics
        #----------------------------------------------------------------------

        ballQA.parseDeviceContext()

        ballQA.addRawToLog("\nBattery Fuel Gauge")
        extendedBattery = dt.ExtendedBattery()
        try:
            extendedBattery = ballQA.getExtendedBattery()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            extendedBattery = ballQA.getExtendedBattery()
        print()
        ballQA.printExtendedBattery(extendedBattery)
        ballQA.logExtendedBattery(extendedBattery)

        ballQA.addRawToLog("\nMCU Implementation Testing: Clocks")
        try:
            rtcRatio = ballQA.getRtcRatio()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            rtcRatio = ballQA.getRtcRatio()
        print()
        ballQA.printRtcRatio(rtcRatio=rtcRatio)
        ballQA.logRtcRatio(rtcRatio=rtcRatio)

        ballQA.addRawToLog("\nPeripherals: IMU")
        try:
            imuData = ballQA.getImuData()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            imuData = ballQA.getImuData()
        print()
        ballQA.printImu(imuData=imuData)
        ballQA.logImu(imuData=imuData)

        ballQA.addRawToLog("\nUWB")
        try:
            avgPsr = ballQA.getPsrData()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            avgPsr = ballQA.getPsrData()
        print()
        ballQA.printPsr(avgPsr)
        ballQA.logPsr(avgPsr)
        ballQA.startSession()

        #----------------------------------------------------------------------
        # Get Master device transmission power
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nMaster Tx Power Levels")
        try:
            masterTxPower = dt.TxPower()
            masterTxPower = ballQA.getMasterTxPower()
        except:
            print()
            common.resetMasterPrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            masterTxPower = ballQA.getMasterTxPower()
        print()
        ballQA.printTxPower(masterTxPower)
        ballQA.addTxPowerToLog("Master", masterTxPower)

        #----------------------------------------------------------------------
        # Set transmission power to minimum value
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nDUT Min Tx Power Levels")
        try:
            ballQA.setDutTxPower(powerLevel=TX_POWER_LEVEL_MIN)
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            ballQA.setDutTxPower(powerLevel=TX_POWER_LEVEL_MIN)       
        try:
            dutTxPower: dt.TxPower() = None
            minTxPower = dt.TxPower(txAvgPower=TX_POWER_LEVEL_MIN,
                                    txChirpPower=TX_POWER_LEVEL_MIN,
                                    txDataPower=TX_POWER_LEVEL_MIN)
            dutTxPower = ballQA.getDutTxPower()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            dutTxPower = ballQA.getDutTxPower()
        print()
        ballQA.printTxPower(dutTxPower)
        ballQA.addTxPowerToLog("Minimum", dutTxPower)
        if dutTxPower != minTxPower:
            TestPass = False
        
        #----------------------------------------------------------------------
        # Check if still connected
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nConnection check (USB connected)")
        try:
            retVal = ballQA.checkOnline()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            retVal = ballQA.checkOnline()
        ballQA.addBooleanRecordToLog("DUT_Connected", bool(retVal))
        if not retVal:
            TestPass = False       
        print()
        pretty.printInfo("********************************")
        pretty.printInfo(f'DUT is online: {str(retVal)}')
        pretty.printInfo("********************************")

        #----------------------------------------------------------------------
        # Ensure the DUT is disconnected
        #----------------------------------------------------------------------

        print()
        common.disconnectSwiftKey()
        common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
        print()

        #----------------------------------------------------------------------
        # Check if still connected
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nConnection check (USB disconnected)")
        try:
            retVal = ballQA.checkOnline()       
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            retVal = ballQA.checkOnline() 
        ballQA.addBooleanRecordToLog("DUT_Connected_Over_Air", bool(retVal))
        if not retVal:
            TestPass = False
        print()
        pretty.printInfo("********************************")
        pretty.printInfo(f'DUT is online: {str(retVal)}')
        pretty.printInfo("********************************")

        #----------------------------------------------------------------------
        # Check the Packet Success Rate
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nPacket Success Rate check (USB disconnected)")
        try:
            retVal = ballQA.getPSR()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            retVal = ballQA.getPSR()
        ballQA.addRecordToLog("PSR_Connection_Over_Air", str(retVal))
        print()
        pretty.printInfo("********************************")
        pretty.printInfo(f'PSR: {str(retVal)}')
        pretty.printInfo("********************************")

        #----------------------------------------------------------------------
        # Get current value in mA from Fuel Guage
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nCurrent consumption")
        try:
            current_mA = ballQA.getCurrent()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            current_mA = ballQA.getCurrent()
        print()
        ballQA.printCurrent(current_mA)
        ballQA.logCurrentConsumption("SlowSensor", "Online", current_mA)
        if ((current_mA == None) or (current_mA >= CURRENT_mA_MAX)):
            TestPass = False

        #----------------------------------------------------------------------
        # Ensure the DUT is connected
        #----------------------------------------------------------------------

        print()
        common.connectSwiftKey()

        #----------------------------------------------------------------------
        # Set transmission power to default value
        #----------------------------------------------------------------------

        ballQA.addRawToLog("\nDUT Default Tx Power Levels")
        try:
            ballQA.setDutTxPower(powerLevel=TX_POWER_LEVEL_DEFAULT)
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            ballQA.setDutTxPower(powerLevel=TX_POWER_LEVEL_DEFAULT)
        try:
            dutTxPower = ballQA.getDutTxPower()
        except:
            print()
            common.resetDevicePrompt()
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                 dutTimeout=DUT_CONNECT_WAIT_TIME)
            dutTxPower = ballQA.getDutTxPower()
        print()
        ballQA.printTxPower(dutTxPower)
        ballQA.addTxPowerToLog("Default", dutTxPower)
        defaultTxPower = dt.TxPower(txAvgPower=TX_POWER_LEVEL_DEFAULT,
                                    txChirpPower=TX_POWER_LEVEL_DEFAULT,
                                    txDataPower=TX_POWER_LEVEL_DEFAULT)
        if dutTxPower != defaultTxPower:
            TestPass = False
        
        #----------------------------------------------------------------------
        # Upload release MCUAPP and MCUWB image
        #----------------------------------------------------------------------
        
        if ((dutVersions.hwVersion >= HW_VERSION_03) and
            (releaseFirmwareVersions.appVersionString < MIN_MCUAPP_FOR_HW03)):
            print()
            pretty.printWarning(f"The version: "
                                f"{releaseFirmwareVersions.appVersion} does "
                                f"not work with HW: {str(dutVersions.hwVersion)}")
            args.noFlash = True       
        # UwbMcu checked here, and not before flashing UWB,
        # because we do not have a way to differentiate between QA and Release versions for UwbMcu images
        if (((dutVersions.appMcuVersion != releaseFirmwareVersions.appVersion) or
            (dutVersions.uwbMcuVersion != releaseFirmwareVersions.uwbVersion) or
            (dutVersions.appMcuVersion.firmwareType != releaseFirmwareVersions.appVersion.firmwareType)) and
            (not args.noFlash) and (not args.noRelFlash)):
            ballQA.addRawToLog("\nFinal image upload")
            print()
            try:
                ballQA.flashFirmware(fwImageVersion=releaseFirmwareVersions,
                                     dutVersions=dutVersions,
                                     device="App")              
            except:
                print()
                common.resetDevicePrompt()
                print()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                ballQA.flashFirmware(fwImageVersion=releaseFirmwareVersions,
                                     dutVersions=dutVersions,
                                     device="App")
            common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
            print()
            
            try:
                ballQA.flashFirmware(fwImageVersion=releaseFirmwareVersions,
                                     device="Uwb")
            except:
                print()
                common.resetDevicePrompt()
                print()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                ballQA.flashFirmware(fwImageVersion=releaseFirmwareVersions,
                                     device="Uwb")
            common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
            print()
        
            #----------------------------------------------------------------------
            # Check firmware version after update
            #----------------------------------------------------------------------
            
            ballQA.addRawToLog("\nRelease Versions")         
            try:
                dutVersions = ballQA.getDutFwVersions()
            except:
                print()
                common.resetDevicePrompt()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                     dutTimeout=DUT_CONNECT_WAIT_TIME)
                dutVersions = ballQA.getDutFwVersions()
            print()
            ballQA.printVersions(dutVersions)
            ballQA.logRelVersions(dutVersions)
            if ((dutVersions.uwbMcuVersion == releaseFirmwareVersions.uwbVersion) and
                (dutVersions.appMcuVersion == releaseFirmwareVersions.appVersion) and
                (dutVersions.appMcuVersion.firmwareType == releaseFirmwareVersions.appVersion.firmwareType)):
                print()
                pretty.printInfo("The MCUWB and MCUAPP Release version successfully uploaded")
                # Uncomment when needed
                ballQA.addBooleanRecordToLog("Release_Versions_Upload", True)
            else:
                print()
                pretty.printInfo("The MCUWB and MCUAPP Release version unsuccessfully uploaded")
                # Uncomment when needed
                ballQA.addBooleanRecordToLog("Release_Versions_Upload", False)
                TestPass = False

        if dutVersions.appMcuVersion > Version(OLD_COMMANDS_MCUAPP):
        #----------------------------------------------------------------------
        # Ensure the DUT is disconnected
        #----------------------------------------------------------------------

            print()
            common.disconnectDevicePrompt()

        #----------------------------------------------------------------------
        # Turn off the DUT
        #----------------------------------------------------------------------
            
            try:
                ballQA.turnOff()
            except:
                print()
                common.resetDevicePrompt()
                ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
                ballQA.turnOff()

            common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
        else:
        #----------------------------------------------------------------------
        # Turn off the DUT
        #----------------------------------------------------------------------

            print()
            common.getBooleanInputFromOperator(
                "Please use the key to turn the Device Under Test off?")

        #----------------------------------------------------------------------
        # Check if DUT off
        #----------------------------------------------------------------------
        
        ballQA.addRawToLog("\nDUT off status")
        try:
            retVal = ballQA.checkOnline()         
        except:
            ballQA.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            retVal = ballQA.checkOnline() 
        dutOff = True
        if retVal:
            dutOff = False
        ballQA.addBooleanRecordToLog("DUT_Off", bool(dutOff))
        TestPass = dutOff
        print()
        pretty.printInfo("********************************")
        pretty.printInfo(f'DUT is off: {str(dutOff)}')
        pretty.printInfo("********************************")

        #----------------------------------------------------------------------
        # Finish the test
        #----------------------------------------------------------------------

        if args.passFail:
            print()
            if TestPass:
                pretty.printSuccess("Device Under Test: Pass")
            else:
                pretty.printError("Device Under Test: Fail")
        
        print()
        ballQA.appendErrorReports()
    except Exception as error:
        if ((not serialNumber) and ballQA):
            # Get Serial Number manualy, log it and throw an excepton
            print()
            ballQA.serialNumber = common.getSportableUniqueDeviceId(skipCheck=True)
            ballQA.addSerialNumberToLog()
        pretty.printError("Error: " + str(error))
        if ballQA:
            ballQA.addRecordToLog("ERROR", str(error))
        print("Exiting Test")
    finally:
        if ballQA:
            ballQA.finishTest()
            ballQA.copyDaemonLogFile()
            ballQA.closeAllConnections()
            if ballQA.daemon:
                ballQA.closeDaemon()

        testOutcome = brg.writeReports()
        
        if testOutcome == "pass":
            pretty.printSuccess("\n\n********************************")
            pretty.printSuccess(
                "TEST OUTCOME: " + ballQA.serialNumber + " PASSED THE TEST")
            pretty.printSuccess("********************************\n\n")
        elif testOutcome == "fail":
            pretty.printFailure("\n\n********************************")
            pretty.printFailure(
                "TEST OUTCOME: " + ballQA.serialNumber + " FAILED THE TEST")
            pretty.printError("********************************\n\n")

        else :
            pretty.printError("Test outcome couldn't be determined for " +
                              ballQA.serialNumber)

        try :
            brg.createSummarySheet()

            if args.masterSummary:
                brg.createMasterSummarySheet()
        except:
            print("Error generating the report sheet")
        
        try :
            if args.masterSummary:
                brg.backupProductionFolder("quiet", "multiStage")
            else :
                brg.backupProductionFolder("quiet", "singleStage")
        except :
            print("Error uploading the logs to the shared drive")
        common.clearTest()

    exit()
