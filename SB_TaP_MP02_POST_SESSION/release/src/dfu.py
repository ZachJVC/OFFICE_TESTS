"""Module with DFU functions
    Date: 5 Nov 2019
    Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.
"""

import os
import src.prettyPrint as pretty
# import required functions rather than the module to avoid import loops
# import loops seems to have caused problems on certain machines
from src.sportableCommon import getBooleanInputFromOperatorWithTimeout
from src.sportableCommon import getBooleanInputFromOperator
from src.sportableCommon import timedOutWaitingFor

dfuseToolDirectory = "../external/dfuse-tool"
dfuModeTimeout = 60
def ensureDFUMode():
    if not isInDFUMode():
        promptDFUMode()
        waitForDFUMode(dfuModeTimeout)

def askForDFUMode():
    if not isInDFUMode():
        printDFUModePrompt()
        waitForDFUMode(dfuModeTimeout, False)

def promptDFUMode():
    getBooleanInputFromOperatorWithTimeout("Put DUT in DFU mode:\n"+
                                        "Slide switch to \"OFF/Boot\" position\n"+
                                        "Hold reset button for 3 seconds\n"+
                                        "Return slide switch to \"ON\" position", dfuModeTimeout)

def promptStandbyMode():
    getBooleanInputFromOperator("Put DUT in Standby mode:\n"+
                                        "Slide switch to \"OFF/Boot\" position\n"+
                                        "Return slide switch to \"ON\" position")

def waitForDFUMode(timeout: float,
                   printWarning: bool = True):
    if not isInDFUMode():
        if printWarning:
            pretty.printWarning("Could not find DFU device")
            pretty.printPrompt("Put DUT in DFU mode...")
        if timedOutWaitingFor(isInDFUMode, timeout, 0.2):
            raise Exception("Timed out while waiting for DFU mode")

def isInDFUMode():
    command = os.system("lsusb | grep -q \"STMicroelectronics STM Device in DFU Mode\"")
    exitCode = os.WEXITSTATUS(command)
    if exitCode == 0:
        return True
    return False

def flashImage(imagePath, address):
    command = os.system(f"sudo STM32_Programmer_CLI -c port=usb1 -w {imagePath} {hex(address)}")
    exitCode = os.WEXITSTATUS(command)
    if exitCode == 0:
        return True
    else:
        return False

def legacyFlashImage(imagePath):
    command = os.system("sudo dfu-util -a 0 -D "+imagePath)
    exitCode = os.WEXITSTATUS(command)
    if exitCode != 0:
        pretty.printError("Failed to flash image "+imagePath)
        raise Exception("Failed to flash DFU image")

def leaveDFUMode():
    command = os.system("sudo STM32_Programmer_CLI -c port=usb1 -g")
    exitCode = os.WEXITSTATUS(command)
    if exitCode != 0:
        pretty.printError("Failed to leave DFU mode")

def legacyLeaveDFUMode():
    command = os.system("sudo "+dfuseToolDirectory+"/dfuse-tool.py --leave")
    exitCode = os.WEXITSTATUS(command)
    if exitCode != 0:
        pretty.printError("Failed to leave DFU mode")

def printDFUModePrompt():
    pretty.printPrompt("Put DUT in DFU mode:\n"+
                       "Slide switch to \"OFF/Boot\" position\n"+
                       "Hold reset button for 3 seconds\n"+
                       "Return slide switch to \"ON\" position")