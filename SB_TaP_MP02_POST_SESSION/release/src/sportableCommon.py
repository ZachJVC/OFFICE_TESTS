""" Implements common functions for the production test suite

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import os
import re
import time
import csv
import statistics
import signal
import src.nrfjtag as jtag
import src.datatypes as dt
import src.prettyPrint as pretty

from typing import List
from inspect import currentframe
from datetime import datetime, timedelta

sessionIds = "./sessionIds.csv"
players = "./playerNames.csv"
serverInfo = "./servers.config.json"
issuedDeviceIds = "./assets/issuedDeviceIds.csv"


def getLineNumber():
    cf = currentframe()
    return cf.f_back.f_lineno

def getBooleanInputFromOperator(prompt):
    promptMessage = pretty.formatPrompt(f"{prompt} [y/n]: ")
    userInput = input(promptMessage)

    if userInput == "y":
        return True
    elif userInput == "n":
        return False
    pretty.printError("Invalid input, please try again...")
    return getBooleanInputFromOperator(prompt)

def getConfirmInputFromOperator(prompt):
    promptMessage = pretty.formatPrompt(f"{prompt}: ")
    userInput = input(promptMessage)

    if userInput == "y":
        return True
    else:
        return False

def getFloatInputFromOperator(prompt):
    promptMessage = pretty.formatPrompt(prompt)
    userInput = input(promptMessage)
    try:
        value = float(userInput)
        return value
    except ValueError:
        pretty.printError("Invalid input, please try again...")
        return getFloatInputFromOperator(prompt)

def getIntInputFromOperator(prompt):
    promptMessage = pretty.formatPrompt(prompt)
    userInput = input(promptMessage)
    try:
        value = int(userInput)
        return value
    except ValueError:
        pretty.printError("Invalid input, please try again...")
        return getIntInputFromOperator(prompt)

def getStringInputFromOperator(prompt):
    promptMessage = pretty.formatPrompt(prompt)
    userInput = input(promptMessage)
    try:
        string = str(userInput)
        return string
    except ValueError:
        pretty.printError("Invalid input, please try again...")
        return getStringInputFromOperator(prompt)


def getTestLogFileName(test, date, time, serialNumber):
    testDirectory = getTestDirectory(test, date)
    return f"{testDirectory}{str(time)}-{str(serialNumber)}.log"

def getTestDirectory(test, date):
    return f"./@{str(test)}/{str(date)}/"

# Calls func every interval and returns False as soon as func returns True
# Returns True if func never returns True within timeout
# param func bool function (must be able to be called repeatedly - not suitable for use with operator input)
def timedOutWaitingFor(func, timeout=10, interval=0.2):
    steps = int(timeout / interval)
    for step in range(0,steps):
        if func() :
            return False
        time.sleep(interval)
    return True

def getTagIdFromJtag(test: 'TestUtilities'):
    try:
        ensureJtagConnectedToBoard(timeout=20)
        tagId = jtag.getSN()
        return tagId
    # This a special case when the JTAG fails to get the UUID which is required to make a test object
    except Exception as error:
        test.addRecordToLog("ERROR", str(error))
        test.logErrorReport(code=dt.ErrorCodes.ReadError,
                            description=dt.ReportDescriptions.getIdFromJtagError,
                            exception=error,
                            line=getLineNumber())
        raise error

def ensureJtagConnectedToPc(timeout):
    if not jtag.isJtagConnectedToPc():
        pretty.printWarning("Could not find JTAG debugger connected to PC")
        pretty.printPrompt("Waiting for JTAG debugger USB connection...")
        if timedOutWaitingFor(jtag.isJtagConnectedToPc, timeout, 0.2):
            raise TimeoutError(
                "Timed out waiting for JTAG debugger to connect to PC")

def ensureJtagConnectedToBoard(timeout):
    ensureJtagConnectedToPc(timeout)
    if not jtag.isJtagConnectedToBoard():
        pretty.printWarning("Could not find JTAG connection to board")
        pretty.printPrompt("Waiting for JTAG connection to board...")
        if timedOutWaitingFor(jtag.isJtagConnectedToBoard, timeout, 1):
            raise TimeoutError("Timed out waiting for JTAG connection to DUT")

def ensureJtagDisconnectedFromBoard(timeout):
    if not jtag.isJtagConnectedToPc():
        pretty.printWarning("Could not determine if JTAG is connected to board")
        while not getBooleanInputFromOperator("Ensure JTAG is disconnected and press [y] to continue"):
            time.sleep(0.1)
        return
    if jtag.isJtagConnectedToBoard():
        pretty.printPrompt("Please disconnect JTAG from board")
        print("Waiting for JTAG to disconnect...")
        while jtag.isJtagConnectedToBoard() :
            time.sleep(0.5)
        getBooleanInputFromOperator('Power cycle the tag, then press y to continue')

def autoFindTagId(attachedPath, timeOut=30):
    removed = True
    while removed:
        exitLoop = timeOut
        print('Auto-detecting tag ID ... ')
        while exitLoop != 0:
            with open(attachedPath, 'r') as f:
                i = -1
                for i, l in enumerate(f):
                    pass
                if i == 0:
                    fields = l.split(",")
                    return fields[0].strip()
            time.sleep(1)
            exitLoop -= 1

        if i > 0:
            removed = getBooleanInputFromOperator("More than one tags are attached, continue?")
        elif i < 0:
            removed = getBooleanInputFromOperator("No tag is attached, continue?")
        else:
            fields = l.split(",")
            return fields[0].strip()
    if not removed:
        raise Exception("Failed to find attached tag.")

def autoFindDeviceId(attachedPath, multiMode=False, timeout=30):
    endLoop = True
    devicesIds = []
    
    while endLoop:
        startTime = time.time()
        print('Auto-detecting Device ID ... ')
        while True:
            currentTime = time.time() - startTime
            if currentTime > timeout:
                # We've waited too long for the response
                break

            with open(attachedPath, 'r') as f:
                lines = f.readlines()
                
            if len(lines) == 1:
                fields = lines[0].split(',')
                return (fields[0]).strip()
            elif ((len(lines) > 1) and (multiMode == True)):
                for line in lines:
                    fields = line.split(',')
                    devicesIds.append(fields[0].strip())
                return devicesIds
            time.sleep(1)

        if ((len(lines) > 1) and (multiMode == False)):
            getBooleanInputFromOperator("More than one tags are attached.\n" +
                                        "Put DUT in OFF mode:\n"+
                                        "Slide switch to \"OFF\" position")
        elif len(lines) == 0:
            endLoop = getBooleanInputFromOperator("No tag is attached, continue? ...")
    
    raise Exception("Failed to find attached tag.")

def autoFindDevices(attachedPath="./attachedTags.csv", promptToRepeat=True, timeout=30, numOfDevices=2):
    endLoop = True
    devices = []
    
    while endLoop:
        startTime = time.time()
        print('Auto-detecting Device ID ... ')
        while True:
            currentTime = time.time() - startTime
            if currentTime > timeout:
                # We've waited too long for the response
                break

            with open(attachedPath, 'r') as f:
                lines = f.readlines()

            if len(lines) == numOfDevices:
                for line in lines:
                    fields = line.split(',')
                    devices.append({"Type":fields[1].strip(), "DeviceId":fields[0].strip()})
                return devices
            
            time.sleep(1)

        if len(lines) != numOfDevices:
            if promptToRepeat == False:
                break
            endLoop = getBooleanInputFromOperator("Please check if all devices are connected.\n"\
                "Press 'y' to continue or 'n' to terminate the test")
    
    raise Exception("Failed to find attached devices.")

def autoFindDevice(deviceType="Swift",
                   attachedPath="./attachedTags.csv",
                   promptToRepeat=False,
                   timeout=10) -> dict:
    endLoop = True
    device = {}

    while endLoop:
        startTime = time.time()
        print('Auto-detecting ' + str(deviceType) + ' Device ID ... ')
        while True:
            currentTime = time.time() - startTime
            if currentTime > timeout:
                # We've waited too long for the response
                break

            with open(attachedPath, 'r') as f:
                lines = f.readlines()

            if len(lines) > 0:
                for line in lines:
                    fields = line.split(',')
                    if fields[1].strip() == str(deviceType):
                        device = {"Type":fields[1].strip(), "DeviceId":fields[0].strip()}
                        return device
            
            time.sleep(0.5)

        if promptToRepeat == False:
            break
        endLoop = getBooleanInputFromOperator("Please check if the " + str(deviceType) + " device is connected.\n"\
            "Press 'y' to continue or 'n' to terminate the test")
    
    return None

def initLogDirectories():
    """Ensures required subdirectories exist and clears main board log.

    Parameters
    ----------
    tagId : str
        Target tag ID.

    """
    if not os.path.exists("./@MB"):
        os.mkdir("./@MB")
    if not os.path.exists("./@GNSS"):
        os.mkdir("./@GNSS")
    if not os.path.exists("./@ASSEMBLED"):
        os.mkdir("./@ASSEMBLED")

def clearTest():
    """Removes temporary files from the test directory.

    """
    # Clear new data
    if os.path.isfile(sessionIds):
        os.remove(sessionIds)
    if os.path.isfile(players):
        os.remove(players)
    if os.path.isfile(serverInfo):
        os.remove(serverInfo)
    return

def waitWithLiveCounter(waitTime):
    for seconds in range(waitTime, 0, -1):
        print(" ",str(seconds),"seconds remaining...   ", end="\r")
        time.sleep(1)


def scanImu():
    onlyfiles = [f for f in os.listdir("./@MB/") if os.path.isfile(os.path.join("./@MB/", f))]
    IMU_ST_AXL_X = []
    IMU_ST_AXL_Y = []
    IMU_ST_AXL_Z = []
    IMU_ST_GYR_X = []
    IMU_ST_GYR_Y = []
    IMU_ST_GYR_Z = []
    for f in onlyfiles:
        with open("./@MB/" + f, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row)> 0:
                    if row[0] == "IMU_ST_AXL_X":
                        IMU_ST_AXL_X.append(float(row[1]))
                    if row[0] == "IMU_ST_AXL_Y":
                        IMU_ST_AXL_Y.append(float(row[1]))
                    if row[0] == "IMU_ST_AXL_Z":
                        IMU_ST_AXL_Z.append(float(row[1]))
                    if row[0] == "IMU_ST_GYR_X":
                        IMU_ST_GYR_X.append(float(row[1]))
                    if row[0] == "IMU_ST_GYR_Y":
                        IMU_ST_GYR_Y.append(float(row[1]))
                    if row[0] == "IMU_ST_GYR_Z":
                        IMU_ST_GYR_Z.append(float(row[1]))
    print("IMU_ST_AXL_X", statistics.mean(IMU_ST_AXL_X), "+/-", statistics.stdev(IMU_ST_AXL_X))
    print("IMU_ST_AXL_Y", statistics.mean(IMU_ST_AXL_Y), "+/-", statistics.stdev(IMU_ST_AXL_Y))
    print("IMU_ST_AXL_Z", statistics.mean(IMU_ST_AXL_Z), "+/-", statistics.stdev(IMU_ST_AXL_Z))
    print("IMU_ST_GYR_X", statistics.mean(IMU_ST_GYR_X), "+/-", statistics.stdev(IMU_ST_GYR_X))
    print("IMU_ST_GYR_Y", statistics.mean(IMU_ST_GYR_Y), "+/-", statistics.stdev(IMU_ST_GYR_Y))
    print("IMU_ST_GYR_Z", statistics.mean(IMU_ST_GYR_Z), "+/-", statistics.stdev(IMU_ST_GYR_Z))

def powerCycleTag():
    prompt = "Please power cycle tag, then press y to continue"
    while not getBooleanInputFromOperator(prompt):
        time.sleep(0.5)

def getSportableUniqueDeviceId(issuedDeviceIds=[], skipCheck=False):
    numRetries=3
    uniqueDeviceId = None
    for i in range(0,numRetries):
        barcodeData = getStringInputFromOperator("Scan 2D barcode: ")
        barcodeRegex =re.search("S\/N:\s?([a-zA-Z0-9]{6}),?", barcodeData)
        kbRegex =re.search("^([a-zA-Z0-9]{6})$", barcodeData) #allow keyboard entry without barcode 'S/N:' prefix
        if barcodeRegex:
            uniqueDeviceId = barcodeRegex.group(1)
            break
        elif kbRegex:
            uniqueDeviceId = kbRegex.group(1)
            break
        print("Could not detect deviceID in barcode "+str(barcodeData)+", please try again")
    
    if uniqueDeviceId == None:
        raise Exception(
            f"Could not detect deviceID in barcode {str(barcodeData)}")
    
    if ((skipCheck == True) or (str(uniqueDeviceId).upper() in issuedDeviceIds)):
        return uniqueDeviceId
    
    raise Exception(
        f"Warning! {str(uniqueDeviceId)} has not been issued by Sportable.")

def getSerialNumber(product: str,
                    companyName: str = "Sportable") -> str or None:
    """Gets product's serial number using pyUSB library.
    
    param:
        product: string containing product name (e.g. CLI_NH_SWIFT)

    return:
        serial_number: string containing the retrieved serial number
        None: if device not found
    """
    try:
        import usb.core as usb
    except:
        print("\n'pyUSB' library not found.\n")
        return None
    devices = usb.find(find_all=True, manufacturer=str(companyName))
    for dev in devices:
        if dev.product == product:
            return str(dev.serial_number[0:6])
    return None

def getSerialNumbers(product: str,
                     companyName: str = "Sportable"
) -> List[str] or None:
    """Gets product's serial number using pyUSB library.
    
    param:
        product: string containing product name (e.g. CLI_NH_SWIFT)

    return:
        serial_numbers: list of strings containing the retrieved serial numbers
        None: if device not found
    """
    try:
        import usb.core as usb
    except:
        print("\n'pyUSB' library not found.\n")
        return None
    serial_numbers = list()
    devices = usb.find(find_all=True, manufacturer=str(companyName))
    for dev in devices:
        if dev.product == product:
            serial_numbers.append(str(dev.serial_number[0:6]))
    if serial_numbers:
        return serial_numbers
    else:
        return None

def isIssuedDeviceId(uniqueDeviceId):
    with open(issuedDeviceIds, 'r') as logFile:
        reader = csv.DictReader(logFile)
        for row in reader:
            if row["deviceId"].upper() == uniqueDeviceId.upper():
                return True
    print(uniqueDeviceId, "is not included in issuedDeviceIds.csv, please ensure that the id has been issued by Sportable")
    return False

def getManufacturingNumber():
    batchNumber = getStringInputFromOperator("Enter batch number: ")
    unitNumber = getStringInputFromOperator("Enter unit number: ")
    manufacturingNumber = (str(batchNumber)+str(unitNumber))
    return manufacturingNumber

def timeoutHandler(signum, frame):
    raise TimeoutError("Timeout!")

def getBooleanInputFromOperatorWithTimeout(prompt, timeout):
    signal.signal(signal.SIGALRM, timeoutHandler)
    try:
        signal.alarm(timeout)
        bool = getBooleanInputFromOperator(prompt)
        return bool
    except Exception as error:
        raise TimeoutError(f"Timed out while waiting for: {str(prompt)}")
    finally:
        signal.alarm(0)

def ensureMasterOn(product, timeout):
    timeoutDuration = timedelta(seconds=timeout)
    timeoutStart = datetime.now()
    masterOn = getBooleanInputFromOperatorWithTimeout(
        f"Is {str(product)} master device on?", timeout)
    while not masterOn:
        masterOn = getBooleanInputFromOperatorWithTimeout(
            f"Turn {str(product)} master device on", timeout)
        now = datetime.now()
        if (now-timeoutStart) > timeoutDuration:
            raise TimeoutError("Timed out while waiting for master device")

def ensureMasterOff(product, timeout):
    timeoutDuration = timedelta(seconds=timeout)
    timeoutStart = datetime.now()
    masterOff = getBooleanInputFromOperatorWithTimeout(
        f"Is {str(product)} master device off?", timeout)
    while not masterOff:
        masterOff = getBooleanInputFromOperatorWithTimeout(
            f"Turn {str(product)} master device off", timeout)
        now = datetime.now()
        if (now-timeoutStart) > timeoutDuration:
            raise TimeoutError("Timed out while waiting for master device off")

def ensureDutOn(timeout: float = 60):
    timeoutDuration = timedelta(seconds=timeout)
    timeoutStart = datetime.now()
    dutOn = getBooleanInputFromOperatorWithTimeout(
        f"Is the DUT on?", timeout)
    while not dutOn:
        dutOn = getBooleanInputFromOperatorWithTimeout(
            f"Turn the DUT on", timeout)
        now = datetime.now()
        if (now-timeoutStart) > timeoutDuration:
            raise TimeoutError("Timed out while waiting for the DUT")

def ensureDeviceConn(product, timeout):
    timeoutDuration = timedelta(seconds=timeout)
    timeoutStart = datetime.now()
    deviceConn = getBooleanInputFromOperatorWithTimeout(
        f"Is {str(product)} device connected to the USB?", timeout)
    while not deviceConn:
        deviceConn = getBooleanInputFromOperatorWithTimeout(
            f"Connect {str(product)} device to the USB", timeout)
        now = datetime.now()
        if (now-timeoutStart) > timeoutDuration:
            raise TimeoutError(
                f"Timed out while waiting for {str(product)} "
                f"device connect to the USB")

def ensureDeviceDisconn(product, timeout):
    timeoutDuration = timedelta(seconds=timeout)
    timeoutStart = datetime.now()
    deviceDisconn = getBooleanInputFromOperatorWithTimeout(
        f"Is {str(product)} device disconnected from the USB", timeout)
    while not deviceDisconn:
        deviceDisconn = getBooleanInputFromOperatorWithTimeout(
            f"Disconnect {str(product)} device from the USB", timeout)
        now = datetime.now()
        if (now-timeoutStart) > timeoutDuration:
            raise TimeoutError(f"Timed out while waiting for {str(product)} "
                               f"device disconnect from the USB")

def ensureTestStage(stage):
    return getBooleanInputFromOperator(
        f"Please confirm that you are testing a {str(stage)}")

def disconnectDevicePrompt():
    while not getConfirmInputFromOperator(
        "Please disconnect the Device Under Test, then press 'y' to continue"):
        time.sleep(0.5)
    return True

def disconnectSwiftKey():
    while not getConfirmInputFromOperator(
        "Please unplug the USB cable from the SWIFT Key, then press 'y' to continue"):
        time.sleep(0.5)
    return True

def connectSwiftKey():
    while not getConfirmInputFromOperator(
        "Please connect the computer USB cable to the SWIFT Key, then press 'y' to continue"):
        time.sleep(0.5)
    return True

def connectDevicePrompt():
    while not getConfirmInputFromOperator(
        "Please connect the Device Under Test, then press 'y' to continue"):
        time.sleep(0.5)
    return True

def rotateDevicePrompt(location: str = "B"):
    while not getConfirmInputFromOperator(
        f"Please rotate the DUT and place it in the location {location}, "
        f"then press 'y' to continue"):
        time.sleep(0.5)
    return True

def resetDevicePrompt():
    while not getConfirmInputFromOperator(
        "Please reset the Device Under Test, then press 'y' to continue"):
        time.sleep(0.5)
    return True

def hardResetDevicePrompt():
    while not getConfirmInputFromOperator(
        "Please HARD reset the Device Under Test, then press 'y' to continue"):
        time.sleep(0.5)
    return True

def resetMasterPrompt():
    while not getConfirmInputFromOperator(
        "Please reset the Master device, then press 'y' to continue"):
        time.sleep(0.5)
    return True

def pressPowerButton(doublePress: bool = False):
    while not getConfirmInputFromOperator(
        f"Please{' double' if doublePress else ''} press the power button, "
        "then press 'y' to continue"):
        time.sleep(0.5)
    return True

def testMenu():
    print()
    print("*************************************************")
    print("                   Production Test")
    print("*************************************************")
    print()
    print("1) Valve")
    print("2) Bladder")
    print("3) Ball")
    print()
    input = getIntInputFromOperator("Please enter your choice: ")
    if input == 1:
        return dt.testStage.VALVE
    elif input == 2:
        return dt.testStage.BLADDER
    elif input == 3:
        return dt.testStage.BALL
    else:
        raise ValueError("Invalid input.")

def kickMenu():
    print()
    print("*************************************************")
    print("                   Test Type")
    print("*************************************************")
    print()
    print("1) Pre-kick")
    print("2) Post-kick")
    print()
    input = getIntInputFromOperator("Please enter your choice: ")
    if input == 1:
        return dt.testType.PRE_KICK
    elif input == 2:
        return dt.testType.POST_KICK
    else:
        raise ValueError("Invalid input.")