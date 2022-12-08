"""
Test script for pressure sensor sub-assembly.

Author: Sportable
Date: 20 June 2022

Copyright (c) 2022, Sportable Technologies. All rights reserved.
"""
import re
import src.prettyPrint as pretty
import src.testUtils as tu
import src.sportableCommon as common

from src.datatypes import OperatorInputError

def pressureTest(args,
                 test: tu.TestUtilities):
    LIVE_COUNTER_DELAY = 5
    SLOW_SENOR_READING_DELAY = 10

    try:
        #----------------------------------------------------------------------
        # Get device serial number
        #----------------------------------------------------------------------

        print()
        common.waitWithLiveCounter(LIVE_COUNTER_DELAY)
        print()
        test.serialNumber = common.getSerialNumber("CLI_NH_CIVET")
        print(f"DUT S/N: {test.serialNumber}")
    
        #----------------------------------------------------------------------
        # Generate daemon.cfg
        #----------------------------------------------------------------------

        test.initDaemon(targetProduct="Civet", debug=args.debug)
        test.createDaemonConfig(dutType="CIVET",
                                dutBlocking=False)

        #----------------------------------------------------------------------
        # Start the Daemon
        #----------------------------------------------------------------------

        test.startDaemon()

        #----------------------------------------------------------------------
        # Start the Test
        #----------------------------------------------------------------------

        print()
        test.startTest()
        # Scan sub assembly ID and check it starts with S-B
        print()
        subAssemblyId = common.getStringInputFromOperator("Scan sub assembly ID: ")
        subAssRegex = re.search("S-B", subAssemblyId)
        if  not subAssRegex:
            raise OperatorInputError(f"Invalid Sub Assembly ID: {subAssemblyId}")
        test.addRawToLog(f"subAssNumber,{subAssemblyId}")

        #----------------------------------------------------------------------
        # Get Pressure from Extended Slow Sensor port
        #----------------------------------------------------------------------

        test.addRawToLog("\nPressure Sensor\n")
        try:
            print()
            pretty.printInfo("Waiting for the slow sensor data")
            common.waitWithLiveCounter(SLOW_SENOR_READING_DELAY)
            test.stopSession()
            pressureSensor = test.getPressure()
        except:
            print()
            common.resetDevicePrompt()
            test.restartDaemon()
            print()
            pretty.printInfo("Waiting for the slow sensor data")
            common.waitWithLiveCounter(SLOW_SENOR_READING_DELAY)
            test.stopSession()
            pressureSensor = test.getPressure()
        print()
        test.printPressure(pressureSensor.pressure, pressureSensor.temperature)
        test.logPressure(pressureSensor.pressure, pressureSensor.temperature)

        #----------------------------------------------------------------------
        # End of test
        #----------------------------------------------------------------------

    except Exception as error:
        if test != None:
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
            test.closeDaemon()
