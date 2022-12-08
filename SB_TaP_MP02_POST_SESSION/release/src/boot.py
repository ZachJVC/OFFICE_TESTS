"""Initialises directory and tests first MCUAPP flashing and booting.

This is part of the main board test and writes in the main board log. It is
separated because of jtag vs usb reset issues.

Author: Christos Bontozoglou
Date: 22 Aug 2019

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import src.dfu as dfu
import src.tagDialog as dlg
import src.nrfjtag as jtag
import src.datatypes as dt
import src.sportableCommon as common


def boot(test,
         appBankAImagePath: str,
         appBankBImagePath: str = '',
         mbrImagePath: str = '',
         verType: str = "QA"):
    """Performs the boot test.
    Major steps: (a) connects to jtag, (b) Erases MCUAP, (c) flashes master
    boot record and main firmware, (d) initialises test folder and waits for
    first connection with the tag.

    Parameters
    ----------
    prctType : enum
        Product type under test.
    imgPath : type
        Firmware image to flash.

    Returns
    -------
    str
        Tag ID.

    """
    if test.targetProduct == dt.product.CIVET:
        bootCivet(test, mbrImagePath, appBankAImagePath, appBankBImagePath)
    elif test.targetProduct == dt.product.SWIFT:
        bootSwiftWithMbr(test, mbrImagePath, appBankAImagePath, verType)

def legacyBootSwift(test, imgPath):
    dfu.ensureDFUMode()
    print("Preparing to boot Swift tag")
    dfu.flashImage("images/bootloader.dfu")
    dfu.flashImage("images/mcuwb.dfu")
    common.powerCycleTag()
    common.waitWithLiveCounter(30)
    #TODO prompt is MCUAPP led flashing?
    flashComplete = common.getBooleanInputFromOperator("Is the MCUAPP LED blinking?")
    if not flashComplete:
        raise Exception("Failed to flash MCUWB!")
    dfu.ensureDFUMode()
    dfu.flashImage("images/swift-a.dfu")
    common.powerCycleTag()
    #dfu.leaveDFUMode()

def bootSwift(test, appImagePath, uwbImagePath, verType):
    dfu.ensureDFUMode()
    print("Preparing to boot Swift tag")
    if dfu.flashImage(appImagePath, 0x8000000):
        test.addBooleanRecordToLog(f"AppMcu_{verType}_FW_Upload", True)
    else:
        test.addBooleanRecordToLog(f"AppMcu_{verType}_FW_Upload", False)
        raise Exception(f"Failed to upload AppMcu_{verType}_FW image")
    if dfu.flashImage(uwbImagePath, 0x801E000):
        test.addBooleanRecordToLog(f"UwbMcu_{verType}_FW_Upload", True)
    else:
        test.addBooleanRecordToLog(f"UwbMcu_{verType}_FW_Upload", False)
        raise Exception(f"Failed to upload UwbMcu_{verType}_FW image")
    dfu.leaveDFUMode()

def bootSwiftWithMbr(test, mbrImagePath, appBankABImagePath, verType):
    dfu.ensureDFUMode()
    print("Preparing to boot Swift tag")
    if dfu.flashImage(mbrImagePath, 0x8000000):
        test.addBooleanRecordToLog(f"MBR_Upload", True)
    else:
        test.addBooleanRecordToLog(f"MBR_Upload", False)
        raise Exception(f"Failed to upload MBR")
    if dfu.flashImage(appBankABImagePath, 0x8006800):
        test.addBooleanRecordToLog(f"AppMcu_{verType}_FW_Upload", True)
    else:
        test.addBooleanRecordToLog(f"AppMcu_{verType}_FW_Upload", False)
        raise Exception(f"Failed to upload AppMcu_{verType}_FW image")
    dfu.leaveDFUMode()

def bootSwiftApp(test, appImagePath):
    dfu.ensureDFUMode()
    print("Preparing to boot Swift tag")
    dfu.flashImage(appImagePath, 0x8000000)
    dfu.leaveDFUMode()

def bootCivet(test, mbrImagePath, appBankAImagePath, appBankBImagePath):
    print("Preparing to boot Civet tag")
    common.initLogDirectories()
    common.ensureJtagConnectedToBoard(timeout=20)
    test.addRawToLog("\nMCU Flashing & Identification\n")
    print("Flashing MCUAPP ...")
    flsStatus  = jtag.program(mbrImagePath) and jtag.program(appBankAImagePath) and jtag.program(appBankBImagePath)
    print("Flash Complete")
    test.addBooleanRecordToLog("JTAG_FLASH", flsStatus)
    dlg.initPipes()
    jtag.run()
    common.ensureJtagDisconnectedFromBoard(timeout=20)
