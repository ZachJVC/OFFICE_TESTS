"""Handles communication with nrfjprog.

Author: Christos Bontozoglou
Date: 22 Aug 2019

Copyright (c) 2019, Sportable Technologies. All rights reserved.

"""

import os
import shlex
import subprocess

nrfj = "/opt/SEGGER/nrfjprog/nrfjprog"

def nrfExists():
    """Checks if NRF JTAG tool is installed

    Returns
    -------
    boolean
        True if application is installed, otherwise false.

    """
    if not os.path.isfile(nrfj):
        raise Exception('NRF JTAG application is not found under:' + nrfj)
        return False
    return True

def isJtagConnectedToPc():
    jtagSerialNumber = subprocess.check_output(nrfj+" -i 2>/dev/null", shell=True);
    if jtagSerialNumber == "" :
        return False
    else:
        return True

def isJtagConnectedToBoard():
    command = os.system(nrfj+" --memrd 0x0 >/dev/null 2>&1")
    exitCode = os.WEXITSTATUS(command)
    #serialNumber = subprocess.check_output(nrfj + " --memrd 0x100000A4 ",shell = True, stderr=subprocess.STDOUT).strip()
    #if "ERROR:" in serialNumber:
    if not exitCode == 0:
        return False
    else:
        return True

def getSN():
    if not nrfExists(): return
    SN0 = subprocess.check_output(nrfj + " --memrd 0x100000A4 | awk '{print $2}'",shell = True).strip()
    SN1 = subprocess.check_output(nrfj + " --memrd 0x100000A8 | awk '{print $2}'",shell = True).strip()
    print("NRF MCU ID: " + (SN1.decode("utf-8")  + SN0.decode("utf-8") ).lower())
    return (SN1.decode("utf-8")  + SN0.decode("utf-8") ).lower()

def erase():
    if not nrfExists(): return
    ers = subprocess.check_output(nrfj + " -f nrf52 --eraseall",shell = True)
    return ("Applying system reset." in ers.decode("utf-8"))

def program(hexPath):
    if not nrfExists(): return
    fls = subprocess.check_output(nrfj + " -f nrf52 --program " + hexPath + " --sectorerase", shell = True)
    return ("Programming device." in fls.decode("utf-8"))

def run():
    if not nrfExists(): return
    rns = subprocess.check_output(nrfj + " -f nrf52 --run", shell = True)
    return ("Run." in rns.decode("utf-8"))
