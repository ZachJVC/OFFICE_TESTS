"""Implements assembly product production testing. Running the --boot option first is required.

Copyright (c) 2022, Sportable Technologies. All rights reserved.

"""

import src.datatypes as dt
import src.testUtils as tu
import src.prettyPrint as pretty
import src.sportableCommon as common

from src.versions import Versions, Version
from src.productionConfig import ProductionConfig
from src.firmwareVersion import QACivetFirmwareVersion, ReleaseCivetFirmwareVersion

TX_POWER_LEVEL_DEFAULT = 68
TX_POWER_LEVEL_MIN = 1
DAEMON_DELAY_EXT = 5
DUT_CONNECT_WAIT_TIME = 10
MASTER_CONNECT_WAIT_TIME = 10
MIN_MCUAPP_QA_FLASH_REPLY = "v128.3.4.8"

def asmTest(args,
            config: ProductionConfig,
            test: tu.TestUtilities,
            qaFirmware: QACivetFirmwareVersion,
            releaseFirmware: ReleaseCivetFirmwareVersion):
    dutVersions: Versions = None
    masterVersions: Versions = None

    try:
        if not args.skipConfigCheck and not args.quick:
            if (config.hardwareVariant.assemblyVariant ==
                dt.HardwareAssemblyVariant.AssemblyVariantNotProgrammed):
                raise ValueError(
                    'Production config has not specified an Assembly Variant. '
                    'This is required for the assembled product test.')
        Flash = True
        CheckVersion = True

        #----------------------------------------------------------------------
        # Get devices' serial numbers
        #----------------------------------------------------------------------

        if not config.masterDeviceSerialNumber:
            raise Exception(
                "No Master device serial number in the config file.")
        test.masterSerialNumber = config.masterDeviceSerialNumber
        serialNumbers = common.getSerialNumbers("CLI_NH_CIVET")
        for serialNumber in serialNumbers:
            if serialNumber != test.masterSerialNumber:
                test.serialNumber = serialNumber
                break
    
        #----------------------------------------------------------------------
        # Generate daemon.cfg
        #----------------------------------------------------------------------

        test.initDaemon(targetProduct="Civet", debug=args.debug)
        test.createDaemonConfig(dutType="CIVET",
                                masterType="CIVET",
                                dutBlocking=False)
        
        #----------------------------------------------------------------------
        # Start the Daemon
        #----------------------------------------------------------------------

        test.startDaemon()
    
        #----------------------------------------------------------------------
        # Get devices' id
        #----------------------------------------------------------------------

        test.findDevicesIds(deviceWaitTime=DUT_CONNECT_WAIT_TIME)
        print("TagID:",str(test.tagId))
        print("MasterID:",str(test.masterId))
        print()
        test.startTest()

        #----------------------------------------------------------------------
        # Check if issued by Sportable
        #----------------------------------------------------------------------
        
        if (not args.skipConfigCheck and
            not (str(test.serialNumber).upper() in config.issuedDeviceIds)):
            raise Exception(f'Warning! {str(test.serialNumber)} '
                            f'has not been issued by Sportable.')

        #----------------------------------------------------------------------
        # Reset the Master device
        #----------------------------------------------------------------------

        test.resetMasterDevice()
        common.waitWithLiveCounter(DAEMON_DELAY_EXT)
        print()
        test.resetDut()
        common.waitWithLiveCounter(DAEMON_DELAY_EXT)
        print()

        
        #----------------------------------------------------------------------
        # Get the Master and the Daemon versions
        #----------------------------------------------------------------------

        test.addRawToLog("\nMaster and Daemon Versions")     
        try:
            masterVersions = test.getMasterFwVersions()
        except:
            print()
            common.resetMasterPrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            masterVersions = test.getMasterFwVersions()    
        print()
        test.printVersions(masterVersions)
        test.logMasterVersions(masterVersions)

        #----------------------------------------------------------------------
        # Get firmware version before update
        #----------------------------------------------------------------------

        test.addRawToLog("\nVersions before update")
        try:
            dutVersions = test.getDutFwVersions()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            dutVersions = test.getDutFwVersions()
        print()
        test.printVersions(dutVersions)
        test.logVersions(dutVersions)

        if ((dutVersions.uwbMcuVersion == qaFirmware.uwbVersion) and
            (dutVersions.appMcuVersion == qaFirmware.appVersion) and
            (dutVersions.appMcuVersion.firmwareType == qaFirmware.appVersion.firmwareType)):
            print()
            pretty.printInfo("The MCUWB and MCUAPP QA version already uploaded")
            # Added for Adriens Report Generator
            Flash = False
            CheckVersion = False

            test.addRawToLog("\nVersions used for the QA")
            test.logQAVersions(dutVersions)
            test.addBooleanRecordToLog("AppMcu_QA_FW_Flash", True)
            test.addBooleanRecordToLog("UwbMcu_QA_FW_Flash", True)
            test.addBooleanRecordToLog("QA_Versions_Upload", True)

        #----------------------------------------------------------------------
        # Upload firmware images
        #----------------------------------------------------------------------
        
        if Flash and (not args.noFlash):
            test.addRawToLog("\nFirmware Upload")
            try:
                test.flashFirmware(fwImageVersion=qaFirmware,
                                   dutVersions=dutVersions,
                                   device="App")
            except:
                if dutVersions.appMcuVersion >= Version(MIN_MCUAPP_QA_FLASH_REPLY):
                    print()
                    common.resetDevicePrompt()
                    test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                       dutTimeout=DUT_CONNECT_WAIT_TIME)
                    test.flashFirmware(fwImageVersion=qaFirmware,
                                       dutVersions=dutVersions,
                                       device="App")
            common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
            print()
            try:
                test.flashFirmware(fwImageVersion=qaFirmware,
                                   dutVersions=dutVersions,
                                   device="Uwb")
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                   dutTimeout=DUT_CONNECT_WAIT_TIME)
                test.flashFirmware(fwImageVersion=qaFirmware,
                                   dutVersions=dutVersions,
                                   device="Uwb")
            common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)

        #----------------------------------------------------------------------
        # Check firmware version after update
        #----------------------------------------------------------------------
        
        if CheckVersion and (not args.noFlash):
            test.addRawToLog("\nVersions after update")
            try:
                dutVersions = test.getDutFwVersions()
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                   dutTimeout=DUT_CONNECT_WAIT_TIME)
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
        # Program Hardware Variant
        #----------------------------------------------------------------------

        test.addRawToLog("\nHardware Variant before programming")
        try:
            test.getHardwareVariant()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            test.getHardwareVariant()
        print()
        test.printHardwareVariant("AppMcu", test.hardwareVariantAppMcu)
        test.logHardwareVariant("Pre", "AppMcu", test.hardwareVariantAppMcu)

        if args.eraseHV:
            try:
                test.eraseHardwareVariant()
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                   dutTimeout=DUT_CONNECT_WAIT_TIME)
                test.eraseHardwareVariant()

        if ((not args.quick) and (not args.noVariant)):
            test.checkHardwareVariant(args=args, config=config)
            try:
                test.setHardwareVariant(hw_variant=config.hardwareVariant,
                                        setAssemblyVar=True)
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                   dutTimeout=DUT_CONNECT_WAIT_TIME)
                test.setHardwareVariant(hw_variant=config.hardwareVariant,
                                        setAssemblyVar=True)
            
            test.addRawToLog("\nHardware Variant after programming")
            try:
                test.getHardwareVariant()
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                   dutTimeout=DUT_CONNECT_WAIT_TIME)
                test.getHardwareVariant()
            print()
            test.printHardwareVariant("AppMcu", test.hardwareVariantAppMcu)
            test.logHardwareVariant("Post", "AppMcu", test.hardwareVariantAppMcu)

            if test.hardwareVariantAppMcu != config.hardwareVariant:
                test.addBooleanRecordToLog("Hardware_Product_Descriptor", False)
                raise Exception("Programming hardware variant to AppMcu failed.")
            else:
                test.addBooleanRecordToLog("Hardware_Product_Descriptor", True)
        
        #----------------------------------------------------------------------
        # Check power button
        #----------------------------------------------------------------------

        print()
        test.addRawToLog("\nPower button operation")
        lynxButton: bool = False
        if (config.hardwareVariant.assemblyVariant ==
            dt.HardwareAssemblyVariant.AssemblyVariantLynx or
            config.hardwareVariant.assemblyVariant ==
            dt.HardwareAssemblyVariant.AssemblyVariantLynxPlus or
            config.hardwareVariant.assemblyVariant ==
            dt.HardwareAssemblyVariant.AssemblyVariantLynxRetro):
            test.checkButton()
            lynxButton = True
        test.turnOffUwb()
        common.waitWithLiveCounter(DAEMON_DELAY_EXT)
        print()
        if test.checkOnline():
            raise Exception("Device not in standby state.")
        print()
        common.pressPowerButton(doublePress=lynxButton)
        if (config.hardwareVariant.assemblyVariant ==
            dt.HardwareAssemblyVariant.AssemblyVariantCivet):
            test.checkBuzzer()
        test.checkSession(throwException=True)

        #----------------------------------------------------------------------
        # Get Master device transmission power
        #----------------------------------------------------------------------

        test.addRawToLog("\nMaster Tx Power Levels")
        try:
            masterTxPower = dt.TxPower()
            masterTxPower = test.getMasterTxPower()
        except:
            print()
            common.resetMasterPrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            masterTxPower = test.getMasterTxPower()
        print()
        test.printTxPower(masterTxPower)
        test.addTxPowerToLog("Master", masterTxPower)

        #----------------------------------------------------------------------
        # Set transmission power to minimum value
        #----------------------------------------------------------------------

        test.addRawToLog("\nDUT Min Tx Power Levels")
        try:
            test.setDutTxPower(powerLevel=TX_POWER_LEVEL_MIN)
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            test.setDutTxPower(powerLevel=TX_POWER_LEVEL_MIN)       
        try:
            dutTxPower = dt.TxPower()
            dutTxPower = test.getDutTxPower()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            dutTxPower = test.getDutTxPower()
        print()
        test.printTxPower(dutTxPower)
        test.addTxPowerToLog("Minimum", dutTxPower)
        
        #----------------------------------------------------------------------
        # Check if still connected
        #----------------------------------------------------------------------

        test.addRawToLog("\nConnection check (USB connected)")
        try:
            retVal = test.checkOnline()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            retVal = test.checkOnline()
        test.addBooleanRecordToLog("DUT_Connected", bool(retVal))     
        print()
        pretty.printInfo("********************************")
        pretty.printInfo(f'DUT is online: {str(retVal)}')
        pretty.printInfo("********************************")

        #----------------------------------------------------------------------
        # Ensure the DUT is disconnected
        #----------------------------------------------------------------------

        print()
        common.disconnectDevicePrompt()
        common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
        print()

        #----------------------------------------------------------------------
        # Check if still connected
        #----------------------------------------------------------------------

        test.addRawToLog("\nConnection check (USB disconnected)")
        try:
            retVal = test.checkOnline()       
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            retVal = test.checkOnline() 
        test.addBooleanRecordToLog("DUT_Connected_Over_Air", bool(retVal))
        print()
        pretty.printInfo("********************************")
        pretty.printInfo(f'DUT is online: {str(retVal)}')
        pretty.printInfo("********************************")

        #----------------------------------------------------------------------
        # Check the Packet Success Rate
        #----------------------------------------------------------------------

        test.addRawToLog("\nPacket Success Rate check (USB disconnected)")
        try:
            retVal = test.getPSR()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            retVal = test.getPSR()
        test.addRecordToLog("PSR_Connection_Over_Air", str(retVal))
        print()
        pretty.printInfo("********************************")
        pretty.printInfo(f'PSR: {str(retVal)}')
        pretty.printInfo("********************************")

        #----------------------------------------------------------------------
        # Get in session current value in mA from Fuel Guage
        #----------------------------------------------------------------------

        test.addRawToLog("\nBattery state")
        try:
            current_mA = test.getCurrent()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            current_mA = test.getCurrent()
        print()
        test.printCurrent(current_mA)
        test.logCurrentConsumption("SlowSensor", "In_Session", current_mA)

        #----------------------------------------------------------------------
        # Rotate and ensure the DUT is connected
        #----------------------------------------------------------------------

        print()
        common.connectDevicePrompt()
        common.rotateDevicePrompt()
        common.waitWithLiveCounter(DUT_CONNECT_WAIT_TIME)
        print()

        #----------------------------------------------------------------------
        # Get charge current value in mA from Fuel Guage
        #----------------------------------------------------------------------

        try:
            current_mA = test.getCurrent()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            current_mA = test.getCurrent()
        print()
        test.printCurrent(current_mA)
        test.logCurrentConsumption("SlowSensor", "Charge", current_mA)

        #----------------------------------------------------------------------
        # Get standby current in mA state of charge in % and voltage in mV
        #----------------------------------------------------------------------

        test.turnOffUwb()
        common.waitWithLiveCounter(DAEMON_DELAY_EXT)
        print()
        if test.checkOnline():
            raise Exception('Device not in "Standby" state.')
        test.getStandbyCurrent()
        extendedBattery = dt.ExtendedBattery()
        try:
            extendedBattery = test.getExtendedBattery()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            extendedBattery = test.getExtendedBattery()
        print()
        test.printExtendedBattery(extendedBattery)
        test.logExtendedBattery(extendedBattery)
        
        #----------------------------------------------------------------------
        # Get Pressure from Extended Slow Sensor port
        #----------------------------------------------------------------------

        test.addRawToLog("\nPressure Sensor")
        try:
            pressureSensor = test.getPressure()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME)
            pressureSensor = test.getPressure()
        print()
        test.printPressure(pressureSensor.pressure, pressureSensor.temperature)
        test.logPressure(pressureSensor.pressure, pressureSensor.temperature)

        #----------------------------------------------------------------------
        # Turn on the DUT
        #----------------------------------------------------------------------

        test.turnOnUwb()
        common.waitWithLiveCounter(DAEMON_DELAY_EXT)
        print()
        if not test.checkOnline():
            raise Exception('Device not in "In session" state.')

        #----------------------------------------------------------------------
        # Set transmission power to default value
        #----------------------------------------------------------------------

        test.addRawToLog("\nDUT Default Tx Power Levels")
        try:
            test.setDutTxPower(powerLevel=TX_POWER_LEVEL_DEFAULT)
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            test.setDutTxPower(powerLevel=TX_POWER_LEVEL_DEFAULT)
        try:
            dutTxPower = test.getDutTxPower()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                               dutTimeout=DUT_CONNECT_WAIT_TIME)
            dutTxPower = test.getDutTxPower()
        print()
        test.printTxPower(dutTxPower)
        test.addTxPowerToLog("Default", dutTxPower)

        #----------------------------------------------------------------------
        # HMI tests
        #----------------------------------------------------------------------

        print()
        test.addRawToLog("\nHMI test")
        test.checkDisplay()
        test.checkRGBLED()
        test.checkWhiteLED()

        #----------------------------------------------------------------------
        # Live tests
        #----------------------------------------------------------------------

        # Add live test when ready
        # value = test.runLiveTest(dutSocketNumber=DUT_TCP_SOCKET,
        #                          testSocketNumber=TEST_TCP_SOCKET,
        #                          testName=dt.LiveTest.CURRENT_ONLINE)
        # print(value)

        #----------------------------------------------------------------------
        # Upload firmware images
        #----------------------------------------------------------------------
        
        if ((not args.noFlash) and (not args.noRelFlash)):
            test.addRawToLog("\nFirmware Upload")
            try:
                test.flashFirmware(fwImageVersion=releaseFirmware,
                                   dutVersions=dutVersions,
                                   device="App")
            except:
                if dutVersions.appMcuVersion >= Version(MIN_MCUAPP_QA_FLASH_REPLY):
                    print()
                    common.resetDevicePrompt()
                    test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                       dutTimeout=DUT_CONNECT_WAIT_TIME)
                    test.flashFirmware(fwImageVersion=releaseFirmware,
                                       dutVersions=dutVersions,
                                       device="App")
            common.waitWithLiveCounter(DAEMON_DELAY_EXT)
            print()
            try:
                test.flashFirmware(fwImageVersion=releaseFirmware,
                                   dutVersions=dutVersions,
                                   device="Uwb")
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                   dutTimeout=DUT_CONNECT_WAIT_TIME)
                test.flashFirmware(fwImageVersion=releaseFirmware,
                                   dutVersions=dutVersions,
                                   device="Uwb")
            common.waitWithLiveCounter(DAEMON_DELAY_EXT)
            CheckVersion = True

        #----------------------------------------------------------------------
        # Check firmware version after update
        #----------------------------------------------------------------------
        
        if CheckVersion:
            test.addRawToLog("\nRelease versions")
            try:
                dutVersions = test.getDutFwVersions()
            except:
                print()
                common.resetDevicePrompt()
                test.restartDaemon(masterTimeout=MASTER_CONNECT_WAIT_TIME,
                                   dutTimeout=DUT_CONNECT_WAIT_TIME)
                dutVersions = test.getDutFwVersions()
            print()
            test.printVersions(dutVersions)
            test.logRelVersions(dutVersions)

            if ((dutVersions.uwbMcuVersion == releaseFirmware.uwbVersion) and
                (dutVersions.appMcuVersion == releaseFirmware.appVersion) and
                (dutVersions.appMcuVersion.firmwareType == releaseFirmware.appVersion.firmwareType)):
                print()
                pretty.printInfo("The MCUWB and MCUAPP Release version successfully uploaded")
                # Uncomment when needed
                test.addBooleanRecordToLog("Release_Versions_Upload", True)
            else:
                print()
                pretty.printInfo("The MCUWB and MCUAPP Release version unsuccessfully uploaded")
                # Ucommend when needed
                test.addBooleanRecordToLog("Release_Versions_Upload", False)
        
        #----------------------------------------------------------------------
        # Turn off the DUT
        #----------------------------------------------------------------------

        test.turnOffUwb()

    except Exception as error:
        if (test and (not test.serialNumber)):
            # Get Serial Number manualy, log it and throw an excepton
            print()
            test.serialNumber = common.getSportableUniqueDeviceId(skipCheck=True)
            test.addSerialNumberToLog()
        if test:
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
