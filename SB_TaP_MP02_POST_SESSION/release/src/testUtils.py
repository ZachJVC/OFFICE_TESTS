""" Implements test utilities for the production test suite

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import os
import csv
import glob
import time
import shutil
import statistics
import src.datatypes as dt
import src.dfu as dfu
import src.boot as boot
import src.tagDialog as dlg
import src.daemonSocket as ds
import src.prettyPrint as pretty
import src.sportableCommon as sc

from typing import Optional
from datetime import datetime, timedelta
from usb.core import USBError
from src.daemon import Daemon
from src.parser import Parser
from src.imuData import Imu
from src.psrData import Psr
from src.waitIndicator import WaitIndicator
from src.buildVersion import BuildVersion
from src.versions import Version, Versions
from src.firmwareVersion import FirmwareVersion
from src.productionConfig import ProductionConfig

class TestUtilities:
    CONNECTIONS_DELAY = 0.2     # Delay in seconds
    RESTART_WAIT_TIME = 5       # Delay in seconds

    def __init__(self,
                 test: str = "BOOT",
                 targetProduct: str = "Civet",
                 sendMessage: bool = False,
                 sendErrorReport: bool = False):
        self.sessionId = 1
        self.test: str = test
        self.useAeolusPy: bool = False
        self.targetProduct: str = targetProduct
        self._sendMessage: bool = sendMessage
        self._sendErrorReport: bool = sendErrorReport
        self._tagId: str = "0"
        self._masterId: Optional[str] = None
        self._serialNumber: Optional[str] = None
        self._masterSerialNumber: Optional[str] = None
        self._hardwareVariantAppMcu: dt.HardwareVariant = dt.HardwareVariant()
        self._hardwareVariantUwbMcu: dt.HardwareVariant = dt.HardwareVariant()
        self._daemon: Optional[Daemon] = None
        self._dutConnection: Optional[ds.ControlClient] = None
        self._masterConnection: Optional[ds.ControlClient] = None
        self._firmwareFlashConnection: Optional[ds.FirmwareFlashClient] = None
        self._errorReportConnection: Optional[ds.ErrorReportClient] = None
        self._networkMetricsConnection: Optional[ds.NetworkMetricsClient] = None
        self._liveTestConnection: Optional[ds.LiveTestClient] = None
        self._rangingConnection: Optional[ds.RangingClient] = None
        self._slowSensorConnection: Optional[ds.SlowSensorClient] = None
        self._extendedSlowSensorConnection: Optional[
            ds.ExtendedSlowSensorClient] = None
        self._start_time: datetime = datetime.now()
        self._end_time: Optional[datetime] = None
        self._test_duration: Optional[timedelta] = None
        self._date_string: str = self._start_time.strftime("%Y_%m_%d")
        self._start_time_string: str = self._start_time.strftime("%H_%M_%S")
        self._end_time_string: Optional[str] = None
        self._buildVersion: BuildVersion = BuildVersion()
        if not os.path.exists(sc.getTestDirectory(test, self._date_string)):
            os.makedirs(sc.getTestDirectory(test, self._date_string), exist_ok=True)

    @property
    def tagId(self):
        return self._tagId

    @property
    def masterId(self):
        return self._masterId

    @property
    def serialNumber(self):
        return self._serialNumber

    @property
    def masterSerialNumber(self):
        return self._masterSerialNumber

    @property
    def hardwareVariantAppMcu(self):
        return self._hardwareVariantAppMcu

    @property
    def hardwareVariantUwbMcu(self):
        return self._hardwareVariantUwbMcu
    
    @property
    def daemon(self):
        return self._daemon
    
    @property
    def sendMessage(self):
        return self._sendMessage
    
    @property
    def sendErrorReport(self):
        return self._sendErrorReport

    @tagId.setter
    def tagId(self, tagId):
        if tagId != None:
            self._tagId = str(tagId)

    @masterId.setter
    def masterId(self, masterId):
        if masterId != None:
            self._masterId = str(masterId)

    @serialNumber.setter
    def serialNumber(self, serialNumber):
        if serialNumber != None:
            self._serialNumber = str(serialNumber)

    @masterSerialNumber.setter
    def masterSerialNumber(self, masterSerialNumber):
        if masterSerialNumber != None:
            self._masterSerialNumber = str(masterSerialNumber)

    @hardwareVariantAppMcu.setter
    def hardwareVariantAppMcu(self, hardwareVar):
        self._hardwareVariantAppMcu = hardwareVar

    @hardwareVariantUwbMcu.setter
    def hardwareVariantUwbMcu(self, hardwareVar):
        self._hardwareVariantUwbMcu = hardwareVar
    
    @daemon.setter
    def daemon(self, daemon: Daemon):
        self._daemon = daemon
    
    @sendMessage.setter
    def sendMessage(self, sendMessage: bool):
        self._sendMessage = sendMessage
    
    @sendErrorReport.setter
    def sendErrorReport(self, sendErrorReport: bool):
        self._sendErrorReport = sendErrorReport

    def setTagId(self, tagId):
        self.tagId = tagId

    def getTagId(self):
        return self.tagId
    
    def createAllConnections(self):
        self._dutConnection = ds.ControlClient()
        self._masterConnection = ds.ControlClient(tcpPort=8695)
        self._firmwareFlashConnection = ds.FirmwareFlashClient(timeout=180)
        self._errorReportConnection = ds.ErrorReportClient()
        self._networkMetricsConnection = ds.NetworkMetricsClient()
        self._liveTestConnection = ds.LiveTestClient()
    
    def closeAllConnections(self):
        self._dutConnection.closeConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._masterConnection.closeConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._firmwareFlashConnection.closeConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._errorReportConnection.closeConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._networkMetricsConnection.closeConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._liveTestConnection.closeConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
    
    def openAllConnections(self):
        self._dutConnection.openConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._masterConnection.openConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._firmwareFlashConnection.openConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._errorReportConnection.openConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._networkMetricsConnection.openConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._liveTestConnection.openConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
    
    def restartAllConnections(self):
        self._dutConnection.restartConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._masterConnection.restartConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._firmwareFlashConnection.restartConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._errorReportConnection.restartConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._networkMetricsConnection.restartConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
        self._liveTestConnection.restartConnection()
        time.sleep(TestUtilities.CONNECTIONS_DELAY)
    
    def initDaemon(self,
                   targetProduct: Optional[str] = None,
                   debug: Optional[bool] = None):
        if self._daemon is None:
            self._daemon = Daemon(targetProduct, debug=debug)

    def createDaemonConfig(self,
                           dutType: str,
                           masterType: Optional[str] = None,
                           dutBlocking: bool = False,
                           masterBlocking: bool = False):
        if self.daemon is None:
            raise AttributeError ("Daemon not defined")
        self.daemon.createDaemonConfig(
            dutType=dutType,
            dutSerialNumber=self.serialNumber,
            masterType=masterType,
            masterSerialNumber=self.masterSerialNumber,
            dutBlocking=dutBlocking,
            masterBlocking=masterBlocking)
    
    def startDaemon(self):
        if self.daemon is None:
            raise AttributeError("Daemon not defined")
        self.daemon.startDaemon()
        self.createAllConnections()
    
    def restartDaemon(self,
                      masterTimeout: float = None,
                      dutTimeout: float = None):
        if self.daemon is None:
            raise AttributeError("Daemon not defined")
        self.closeAllConnections()
        self.daemon.restartDaemon()
        print()
        self.waitForDevice(masterTimeout=masterTimeout,
                           dutTimeout=dutTimeout)
        self.restartAllConnections()
    
    def closeDaemon(self):
        if self.daemon is None:
            return
        self.daemon.closeDaemon()
        self.daemon = None
    
    def copyDaemonLogFile(self):
        if self.daemon is None:
            raise AttributeError("Daemon not defined")
        self.daemon.copyLogFile(self.serialNumber)

    def clearLog(self):
        logName = self.getTestLogFileName()
        open(logName, 'w').close()

    def addTagIdToLog(self):
        self.addRecordToLog("PRODUCT_ID", str(self.tagId))

    def addSerialNumberToLog(self):
        self.addRecordToLog("SERIAL_NUMBER", str(self.serialNumber))

    def addHardwareVariantAppMcuToLog(self):
        self.addRecordToLog("AppMcu pcbType",
                            str(self.hardwareVariantAppMcu.pcbType))
        self.addRecordToLog("AppMcu pcbRevision",
                            str(self.hardwareVariantAppMcu.pcbRevision))
        self.addRecordToLog("AppMcu bomVariant",
                            str(self.hardwareVariantAppMcu.bomVariant))
        self.addRecordToLog("AppMcu bomRevision",
                            str(self.hardwareVariantAppMcu.bomRevision))
        self.addRecordToLog("AppMcu assemblyVariant",
                            str(self.hardwareVariantAppMcu.assemblyVariant))
    
    def addHardwareVariantUwbMcuToLog(self):
        self.addRecordToLog("UwbMcu pcbType",
                            str(self.hardwareVariantUwbMcu.pcbType))
        self.addRecordToLog("UwbMcu pcbRevision",
                            str(self.hardwareVariantUwbMcu.pcbRevision))
        self.addRecordToLog("UwbMcu bomVariant",
                            str(self.hardwareVariantUwbMcu.bomVariant))
        self.addRecordToLog("UwbMcu bomRevision",
                            str(self.hardwareVariantUwbMcu.bomRevision))
        self.addRecordToLog("UwbMcu assemblyVariant",
                            str(self.hardwareVariantUwbMcu.assemblyVariant))

    def recordCurrent(self, recordLabel):
        current = sc.getFloatInputFromOperator(
            "Enter device "+recordLabel+" current (mA): ")
        #Todo: Do validation on input, if fails, call self recursively
        roundedCurrent = round(current, 2)
        self.addRecordToLog(recordLabel, roundedCurrent)

    def recordBooleanFromOperator(self,
                                  recordLabel: str,
                                  prompt: str):
        recordValue = sc.getBooleanInputFromOperator(prompt)
        self.addBooleanRecordToLog(recordLabel, recordValue)

    def checkBootTestComplete(self):
        if not os.path.exists("./@MB"):
            errorMessage = pretty.formatError("You must run the main board test on this device before assembled product test")
            raise Exception(errorMessage)
        if not [f for f in os.listdir("@MB") if (self.tagId in f)]:
            pretty.printError("Could not find main board test log for tag "+self.tagId)
            errorMessage = pretty.formatError("You must run the main board test on this device before assembled product test")
            raise Exception(errorMessage)

    def addRawToLog(self, sline: str):
        testLog = self.getTestLogFileName()
        with open(testLog, "a+") as logfile:
            logfile.write(sline + '\n')
        if self._sendMessage and self._daemon:
            self.logUserMessage(info=sline.replace('\n',''))

    def addBooleanRecordToLog(self,
                              recordLabel: str,
                              recordValue: bool):
        if recordValue is True:
            self.addRecordToLog(recordLabel, "Pass")
        elif recordValue is False:
            self.addRecordToLog(recordLabel, "Fail")
        else:
            raise ValueError("addBooleanRecordToLog requires a boolean value")

    def addRecordToLog(self,
                       recordLabel: str,
                       recordValue: Optional[str]):
        self.addRawToLog(f"{recordLabel},{str(recordValue)}")
    
    def exceptionTypeToErrorCode(self, excType):
        switcher = {
            Exception: dt.ErrorCodes.InternalError,
            TimeoutError: dt.ErrorCodes.TimeoutError,
            ValueError: dt.ErrorCodes.InvalidDataError,
            USBError: dt.ErrorCodes.ResourceError,
            ImportError: dt.ErrorCodes.ReadError,
            dt.TcpServerError: dt.ErrorCodes.ConnectionError,
            dt.RangingServerError: dt.ErrorCodes.ConnectionError,
            dt.NetworkMetricsServerError: dt.ErrorCodes.ConnectionError,
            dt.SlowSensorServerError: dt.ErrorCodes.ConnectionError,
            dt.ExtendedSlowSensorServerError: dt.ErrorCodes.ConnectionError,
            dt.FlashingImageError: dt.ErrorCodes.WriteError,
            dt.LiveTestChannelError: dt.ErrorCodes.ConnectionError
        }
        return switcher.get(excType, dt.ErrorCodes.InternalError)
    
    def exceptionToReturnCode(self,
                              exception: Exception) -> dt.ReturnCode:
        returnCode = dt.ReturnCode()
        returnCode.line = exception.__traceback__.tb_lineno
        returnCode.code = self.exceptionTypeToErrorCode(type(exception))
        returnCode.layer = dt.ErrorLayer.eNoLayerModule
        return returnCode
    
    def logErrorReport(self,
                       code: dt.ErrorCodes,
                       description: dt.ReportDescriptions,
                       exception: Exception,
                       instanceNum: int = 0,
                       line: int = 0,
                       module: dt.ErrorModule = dt.ErrorModule.productionTestModule,
                       version: Optional[int] = None):
        if not self._sendErrorReport or not self._daemon:
            return
        if not version:
            version = self._buildVersion.uint32Version
        returnCode = self.exceptionToReturnCode(exception=exception)
        try:
            self._errorReportConnection.reportError(deviceId="DM0N00",
                                                    code=code,
                                                    instanceNum=instanceNum,
                                                    line=line,
                                                    description=description,
                                                    module=module,
                                                    version=version,
                                                    returnCode=returnCode)
        except Exception as error:
            raise Exception(
                f'Logging error report failed.\n{str(error)}') from error

    def logUserMessage(self, info: str):
        try:
            self._errorReportConnection.sendUserMessage(deviceId="DM0N00",
                                                        info=info)
        except Exception as error:
            raise Exception(
                f'Logging user message failed.\n{str(error)}') from error

    def enableCharger(self):
        print("Enabling Charger")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.CHARGER, data = 1)

    def disableCharger(self):
        print("Disabling Charger")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.CHARGER, data = 0)

    def configureSession(self):
        print('Downloading configuration ...')
        dlg.cmdSafeSend(tagId=self.tagId, cmd = "sessions", data = 1)

    def startSession(self):
        print("Starting test session ...")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.START, data = 1)
        #Todo: Replace sleep with wait for ready message from tag
        time.sleep(3)

    def stopSession(self):
        print("Stopping test session ...")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.STOP, data = 1)
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.DEVCTX, data = 0)
        time.sleep(2)
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.SESCTX, data = 0)
        time.sleep(2)
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.SESCFG, data = 0)
        time.sleep(2)
        print("Session ended")

    def waitForSessionRecording(self, waitTime):
        print("Recording session segment, please wait...")
        sc.waitWithLiveCounter(waitTime)
        print("Completed recording session segment")

    def retrieveData(self):
        waitIndicator = WaitIndicator()
        try:
            waitIndicator.start("Retrieving data")
            dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.SESCTX)
            dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.OFFLOAD)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.memoryError,
                                exception=error,
                                line=sc.getLineNumber())
            raise MemoryError(
                f'Retrieving data failed.\n{str(error)}')
        finally:
            waitIndicator.stop()

    def processData(self):
        self.mockGpsRecord()
        self.checkLogsExist()
        if(self.test == dt.testStage.SWIFT or
           self.test == dt.testStage.BALL or
           self.test == dt.testStage.BLADDER or
           self.test == dt.testStage.VALVE):
            #TODO Max this less bodgey
            longTagId = self.getSensorLogFilename("Sgm")[4:20]
            print(longTagId)
            command = f"./aProduction {longTagId} . {self.getTestLogFileName()} MB"
        else:
            command = f"./aProduction {self.tagId} . {self.getTestLogFileName()} {self.test}"
        print("Processing data...")
        exitInfo = os.system(command)
        exitCode = os.WEXITSTATUS(exitInfo)
        if exitCode != 0:
            raise ImportError("Failed to process data!")

    def appendErrorReports(self):
        print("Appending Error Reports...")
        with open(self.getSensorLogFilename("Error"), 'r') as errorLog:
            with open(self.getTestLogFileName(), 'a+') as testReport:
                testReport.write("\nError Reports: \n")
                testReport.write(errorLog.read())
                testReport.write("\n ------- \n\n")

    def startTest(self, serialNumber=None, masterSerialNumber=None):
        print("STARTING",str(self.test),"BOARD TEST FOR",str(self.targetProduct),str(self.tagId))
        if serialNumber:
            self.serialNumber=serialNumber
            if masterSerialNumber:
                self.masterSerialNumber = masterSerialNumber
        self.clearLog()
        self.addRecordToLog("DATE", str(self._date_string))
        self.addRecordToLog("START_TIME", str(self._start_time_string))
        self.addRecordToLog("PRODUCT", str(self.targetProduct))
        self.addRecordToLog("TEST_STEP", str(self.test))
        self.addSerialNumberToLog()
        self.addTagIdToLog()

    def addDeviceIdToLog(self, deviceId):
        self.addRecordToLog("DEVICE_ID",str(deviceId)+"\n")

    def finishTest(self):
        self._end_time = datetime.now()
        self._end_time_string = self._end_time.strftime("%H_%M_%S")
        self._test_duration = (self._end_time - self._start_time)
        self.addRecordToLog("END_TIME", self._end_time_string)
        self.addRecordToLog("TEST_DURATION", self._test_duration)
        self.addRecordToLog("TEST_STATUS", "COMPLETE")
        time.sleep(1)
        print("Test log saved to",self.getTestLogFileName())
        pretty.printComplete("\n\n*********************************************")
        pretty.printComplete(f"COMPLETED {str(self.test)} BOARD TEST FOR "
                             f"{str(self.targetProduct)} {str(self.tagId)}")
        pretty.printComplete("*********************************************\n\n")

    def formatTag(self):
        print("Formatting tag...")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.FORMAT, data=255)
        #self.resetTag()

    def flashTag(self):
        print("Preparing MCUWB ...")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.FLASH, data = 1)
    
    def shutdownDevice(self):
        print("Shutting down the device ...")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.SHUTDOWN, data = 1)

    def shutdownUwb(self):
        print("Shutting down the UWB ...")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.STOP, data = 1)

    def resetTag(self):
        print("Reseting tag...")
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.RESET)

    def waitForTagConnection(self, timeout=60, log=True, attachedTags=False):
        print(f"Waiting for DUT {str(self.tagId)} to reconnect to USB...")
        if attachedTags:
            usbStatus = dlg.waitConnectionUsingAttachedTags(self.tagId, timeout)
        else:
            usbStatus = dlg.waitConnection(self.tagId, timeout)
        
        if log:
            self.addBooleanRecordToLog("USB_CONNECT",usbStatus)
        
        if not usbStatus:
            raise USBError(f"Tag {str(self.tagId)} not connected over USB")
    
    def waitForMasterConnection(self, timeout=60, log=True, attachedTags=False):
        print(f"Waiting for Master device {str(self.masterId)} to reconnect to USB...")
        if attachedTags:
            usbStatus = dlg.waitConnectionUsingAttachedTags(self.masterId, timeout)
        else:
            usbStatus = dlg.waitConnection(self.masterId, timeout)
        
        if log:
            self.addBooleanRecordToLog("USB_CONNECT",usbStatus)
        
        if not usbStatus:
            raise USBError(f"Master {str(self.masterId)} not connected over USB")
    
    def waitForDevice(self,
                      masterTimeout: float = None,
                      dutTimeout: float = None,
                      log: bool = False):
        if masterTimeout:
            self.waitForMasterConnection(timeout=masterTimeout,
                                         log=log,
                                         attachedTags=True)
        if dutTimeout:
            self.waitForTagConnection(timeout=dutTimeout,
                                      log=log,
                                      attachedTags=True)

    def powerCycleTagAndWaitForConnection(self):
        sc.powerCycleTag()
        Daemon.ensureStopped()
        Daemon.ensureRunning()
        self.waitForTagConnection()

    def getSensorLogFilename(self, sensor: str):
        log = glob.glob(f"./{str(self.sessionId)}/{str(self.tagId)}*{str(sensor)}.csv")
        if len(log) == 0:
            errorMessage = pretty.formatError(f"Could not find {str(sensor)} log")
            raise FileNotFoundError(errorMessage)
        elif len(log) != 1:
            errorMessage = pretty.formatError(f"Found conflicting {str(sensor)} logs")
            raise Exception(errorMessage)
        elif len(log) == 1:
            return log[0]

    def getTestLogFileName(self):
         return sc.getTestLogFileName(test=self.test,
                                      date=self._date_string,
                                      time=self._start_time_string,
                                      serialNumber=self.serialNumber)

    def getDaemonLog(self, logDirectory):
        log = glob.glob(f"./{logDirectory}/{self.tagId}*.csv")
        if len(log) == 0:
            errorMessage = pretty.formatError(f"Could not find {logDirectory} log")
            raise FileNotFoundError(errorMessage)
        elif len(log) != 1:
            errorMessage = pretty.formatError(f"Found conflicting {logDirectory} logs")
            raise Exception(errorMessage)
        elif len(log) == 1:
            return log[0]

    def parseCommunicationDianosticLog(self):
        self.addRawToLog("\nCommunication Diagnostics")
        log = self.getDaemonLog("diag")
        with open(log, 'r') as logFile:
            next(logFile) # Skip the time stamp line in the file
            reader = csv.DictReader(logFile)
            for row in reader:
                self.addRecordToLog(f"{row['Peripheral']}_INIT_STATUS",row['Inited'])
                self.addRecordToLog(f"{row['Peripheral']}_STREAM_STATUS",row['Stream'])
                self.addRecordToLog(f"{row['Peripheral']}_ERRORS",row['No of Errors'])

    def parseDeviceContext(self):
        self.addRawToLog("\nDevice Context")
        log = self.getDaemonLog("deviceContext")
        with open(log, 'r') as logFile:
            reader = csv.DictReader(logFile)
            for row in reader:
                self.addRecordToLog(row['name'],row['value'])

    def readDeviceID(self):
        self.retrieveData()
        log = self.getDaemonLog("deviceContext")
        with open(log, 'r') as logFile:
            reader = csv.DictReader(logFile)
            for row in reader:
                if row['name'] == "deviceID":
                    return row['value']
        return

    def addFuelGaugeResults(self):
        self.addRawToLog("\nBattery Fuel Gauge")
        percentageCharged, chargeCurrent, maxCurrent, minCurrent = self.parseCurrent()
        self.addRecordToLog("FuelGauge_Average_Charge_State[%]", str(int(percentageCharged)))
        self.addRecordToLog("FuelGauge_Average_Current[mA]", str(int(chargeCurrent)))
        self.addRecordToLog("FuelGauge_Average_Maximum_Current[mA]", str(int(maxCurrent)))
        self.addRecordToLog("FuelGauge_Average_Minimum_Current[mA]", str(int(minCurrent)))
        self.addRawToLog("\n")


    def mockGpsRecord(self):
        dummyGPS = "UTC Time [usecs],Latitude [deg],Longitude [deg],Heading [deg],speed [cm/s],hMSL [mm],hAcc[mm],MCU Time [usecs],CNO[0],CNO[1],CNO[2],CNO[3],HDOP\n" \
        "0,0,0,0,0,0,0,1548779642823965,0,0,0,0,99.9899978637695\n" \
        "1548779652300197,51.5253989021308,-0.0836703009777793,0,0,34722,9333118,1548779642923965,0,0,0,0,99.9899978637695\n" \
        "1548779652400197,51.5253989021308,-0.0836703009777793,0,0,34722,9333118,1548779643023965,0,0,0,0,99.9899978637695\n" \
        "1548779652500197,51.5253989021308,-0.0836703009777793,0,0,34722,9333118,1548779643123965,0,0,0,0,99.9899978637695\n" \
        "1548779652600197,51.5253989021308,-0.0836703009777793,0,0,34722,9333118,1548779643223965,0,0,0,0,99.9899978637695\n" \
        "1548779652700197,51.5253989021308,-0.0836703009777793,0,0,34722,9333120,1548779643323965,0,0,0,0,99.9899978637695\n" \
        "1548779652800197,51.5253989021308,-0.0836703009777793,0,0,34722,9333120,1548779643423965,0,0,0,0,99.9899978637695"
        # Include fake gps data, since gnss board is not connected ...
        gpsLogFilename = self.getSensorLogFilename("Gps")
        gpsFile = open(gpsLogFilename, 'w')
        gpsFile.write(dummyGPS)
        gpsFile.close()

    def mockUwbRecord(self):
        dummyUwb = "MCU Time [usecs],Range[mm],tqf,tqf2,source\n" \
        "1579089958668771,0,0,0,0\n" \
        "1579089958718771,0,0,0,0\n"
        uwbLogFilename = self.getSensorLogFilename("Uwb")
        uwbFile = open(uwbLogFilename, 'w')
        uwbFile.write(dummyUwb)
        uwbFile.close()

    def parseCurrent(self):
        percentageCharged = []
        chargeCurrent = []
        slowSensorLogFilename = self.getSensorLogFilename("Slow")
        with open(slowSensorLogFilename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[1] == "battery":
                    percentageCharged.append(float(row[2]))
                    chargeCurrent.append(float(row[3]))
        return (statistics.mean(percentageCharged),
                statistics.mean(chargeCurrent),
                max(chargeCurrent),
                min(chargeCurrent))

    def setSerialNumber(self):
        print("Programming Serial Number:", str(self.serialNumber))
        try:
            dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.SETID, stringData=self.serialNumber)
            self.addBooleanRecordToLog("DEVICE_ID_PROGRAMMED", True)
            self.addRecordToLog("PROGRAMMED_DEVICE_ID", str(self.serialNumber))
        except Exception as error:
            self.addBooleanRecordToLog("DEVICE_ID_PROGRAMMED", False)
            raise error

    def legacySetSerialNumber(self):
        print("Programming Serial Number:", str(self.serialNumber))
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.SETID, stringData=self.serialNumber)
        self.addRecordToLog("PROGRAMMED_DEVICE_ID", str(self.serialNumber))

    def setTemporarySerialNumber(self, number=1):
        serialNumber = "TEMP{:02d}".format(number)
        print("Programming Temporary Serial Number:", str(serialNumber))
        dlg.cmdSafeSend(tagId=self.tagId, cmd = dt.cmd.SETID, stringData=serialNumber)
    
    def checkDisplay(self):
        displaySerialNumber = sc.getBooleanInputFromOperator(
            f"Does screen display {str(self.serialNumber)}?")
        if displaySerialNumber:
            self.addRecordToLog("DISPLAY_S/N","Pass")
        else:
            self.addRecordToLog("DISPLAY_S/N","Fail")
    def checkRGBLED(self):
        ledFlashing = sc.getBooleanInputFromOperator("Is the RGB LED illuminated?")
        self.addBooleanRecordToLog("RGB_LED", ledFlashing)

    def checkWhiteLED(self):
        ledFlashing = sc.getBooleanInputFromOperator("Is the White LED flashing?")
        self.addBooleanRecordToLog("WHITE_LED", ledFlashing)

    def checkBuzzer(self):
        buzzerSounded = sc.getBooleanInputFromOperator("Did buzzer sound?")
        if buzzerSounded:
            self.addRecordToLog("BUZZER_SOUND","Pass")
        else:
            self.addRecordToLog("BUZZER_SOUND","Fail")
    
    def checkSession(self, throwException: bool = False):
        if sc.getBooleanInputFromOperator("Are the DW1000 LEDs flashing?"):
            self.addRecordToLog("BUTTON_START_SESSION","Pass")
        else:
            self.addRecordToLog("BUTTON_START_SESSION","Fail")
            if throwException:
                raise Exception('Button strart session failure.')

    def checkButton(self, throwException: bool = False):
        if sc.getBooleanInputFromOperator("Is light emitted from the centre of push button?"):
            self.addRecordToLog("BUTTON_LIGHT","Pass")
        else:
            self.addRecordToLog("BUTTON_LIGHT","Fail")
            if throwException:
                raise Exception('Button light failure.')

    def addVersionNumbers(self,
                          versions: Versions):
        self.addRecordToLog("MCUWB_FW_VERSION", str(versions.uwbMcuVersion))
        self.addRecordToLog("MCUAPP_FW_VERSION", str(versions.appMcuVersion))
        if not versions.hwVersion:
            self.addRecordToLog("HW_VERSION", str(versions.hwVersion))

    def checkLogExists(self, log):
        if os.path.getsize(self.getSensorLogFilename(log)) == 0:
            raise Exception(f"Could not offload {log} logs")

    def checkLogsExist(self):
        self.checkLogExists("Uwb")
        self.checkLogExists("Imu")
        self.checkLogExists("Sgm")
        # Slow sensor commented due to changes in the offload feature
        # self.checkLogExists("Slow")
        self.checkLogExists("Gps")
    
    def resetMasterDevice(self):
        print()
        pretty.printInfo("Resetting the Master device ...")
        try:
            self._masterConnection.resetDevice(deviceId=self.masterSerialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.resetMasterDeviceError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Reset Master device failed.\n{str(error)}') from error
    
    def resetDut(self):
        print()
        pretty.printInfo("Resetting the DUT ...")
        try:
            self._dutConnection.resetDevice(deviceId=self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.resetDutError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Reset DUT device failed.\n{str(error)}') from error
    
    def getMasterFwVersions(self) -> Versions:
        print()
        pretty.printInfo("Checking Master Device Version ...")
        try:
            masterVersions: Versions = None
            masterVersions = self._masterConnection.getVersions(
                deviceId=self.masterSerialNumber)
            masterVersions.daemonVersion = self._masterConnection.getDaemonVersion()
            return masterVersions
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.getMasterFirmwareVersionError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(f'Checking Master FW versions '
                            f'failed.\n{str(error)}') from error

    def getDutFwVersions(self) -> Versions:
        print()
        pretty.printInfo("Checking Versions ...")
        try:
            return self._dutConnection.getVersions(deviceId=self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.getDutFirmwareVersionError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Checking DUT FW versions failed.\n{str(error)}') from error
    
    def getHardwareVariant(self):
        print()
        pretty.printInfo("Getting Hardware Variant ...")
        try:
            self.hardwareVariantAppMcu = self._dutConnection.getHardwareVariant(
                deviceId=self.serialNumber, device="AppMcu")
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.getHardwareVariantError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Getting hardware variant failed.\n{str(error)}') from error
    
    def getPsrData(self) -> int:
        print()
        pretty.printInfo("Exporting PSR data ...")
        try:
            self._dutConnection.exportPsrData()
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.exportPsrDataError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Exporting PSR data failed.\n{str(error)}') from error
        print()
        sc.waitWithLiveCounter(TestUtilities.RESTART_WAIT_TIME)
        print()
        shutil.move("./psrData.csv", f"./{str(self.sessionId)}/{str(self.tagId)}Uwb.csv")
        print()
        pretty.printInfo("Processing PSR data ...")
        try:
            return Psr(self.serialNumber, self.getSensorLogFilename('Uwb'))
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.processPsrDataError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Processing Psr data failed.\n{str(error)}') from error

    def createPsrConfig(self,
                        dutType: str,
                        psrConfigTemplatePath: str = "./PSR.cfg.templ",
                        psrConfigPath: str = "./PSR.cfg") -> None:
        """Creates PSR.cfg with designated serial number
        
        Params:
            psrConfigTemplatePath: string containing path to the PSR
                                   config template file
            psrConfigPath: string containing path to the PSR
                                  config file
            dutType: string containing the DUT device type

        Returns:
            None
        """
        self.createConfigFile(dutType=dutType,
                              configTemplatePath=psrConfigTemplatePath,
                              configPath=psrConfigPath)
    
    def getImuData(self) -> Imu:
        print()
        pretty.printInfo("Exporting IMU data ...")
        try:
            self._dutConnection.exportImuData()
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.exportImuDataError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Exporting IMU data failed.\n{str(error)}') from error
        print()
        sc.waitWithLiveCounter(TestUtilities.RESTART_WAIT_TIME)
        print()
        shutil.move("./IMU.csv", f"./{str(self.sessionId)}/{str(self.tagId)}Imu.csv")
        print()
        pretty.printInfo("Processing IMU data ...")
        try:
            return Imu(self.serialNumber, self.getSensorLogFilename('Imu'))
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.processImuDataError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Processing IMU data failed.\n{str(error)}') from error
    
    def createImuConfig(self,
                        dutType: str,
                        imuConfigTemplatePath: str = "./IMU.cfg.templ",
                        imuConfigPath: str = "./IMU.cfg") -> None:
        """Creates IMU.cfg with designated serial number
        
        Params:
            imuConfigTemplatePath: string containing path to the IMU
                                   config template file
            imuConfigPath: string containing path to the IMU
                                  config file
            dutType: string containing the DUT device type

        Returns:
            None
        """
        self.createConfigFile(dutType=dutType,
                              configTemplatePath=imuConfigTemplatePath,
                              configPath=imuConfigPath)
    
    def createConfigFile(self,
                         dutType: str,
                         configTemplatePath: str,
                         configPath: str) -> None:
        """Creates config file with designated serial number
        
        Params:
            configTemplatePath: string containing path to the
                                config template file
            configPath: string containing path to the
                        config file
            dutType: string containing the DUT device type

        Returns:
            None
        """
        dutString = dutType + "_" + self.serialNumber

        with open(str(configTemplatePath), "r") as template:
            with open(str(configPath), "w") as file:
                for line in template:
                    line = str(line).replace("$(DUT)", str(dutString))
                    line = str(line).replace("$(accelScale)", str(dt.Accel.scale))
                    line = str(line).replace("$(gyroScale)", str(dt.Gyro.scale))
                    if dutType == "SWIFT":
                        line = str(line).replace("$(magnetScale)", str(dt.Magnet.scaleSwift))
                    elif dutType == "CIVET":
                        line = str(line).replace("$(magnetScale)", str(dt.Magnet.scaleCivet))
                    file.write(line)
    
    def eraseHardwareVariant(self):
        print()
        pretty.printInfo("Erasing Hardware Variant ...")
        try:
            self._dutConnection.eraseHardwareVariant(deviceId=self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.eraseHardwareVariantError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Erasing hardware variant failed.\n{str(error)}') from error
    
    def setHardwareVariant(self,
                           hw_variant: dt.HardwareVariant,
                           setAssemblyVar: bool = False):
        print()
        pretty.printInfo("Programming Hardware Variant ...")
        try:
            self._dutConnection.setHardwareVariant(
                deviceId=self.serialNumber,
                hw_variant=hw_variant,
                device="AppMcu",
                setAssemblyVar=setAssemblyVar)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.WriteError,
                                description=dt.ReportDescriptions.setHardwareVariantError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(f'Programming hardware variant '
                            f'failed.\n{str(error)}') from error
        self.resetDut()
        sc.waitWithLiveCounter(TestUtilities.RESTART_WAIT_TIME)
    
    def getMasterTxPower(self) -> dt.TxPower:
        txPower = dt.TxPower()
        print()
        pretty.printInfo("Getting Master Device Tx Power Levels ...")
        try:
            txPower = self._masterConnection.getTxPower(self.masterSerialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.getMasterTxPowerError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Retrieving Master Tx power failed.\n{str(error)}') from error
        return txPower
    
    def getDutTxPower(self) -> dt.TxPower:
        txPower = dt.TxPower()
        print()
        pretty.printInfo("Getting DUT Device Tx Power Levels ...")
        try:
            txPower = self._dutConnection.getTxPower(self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.getDutTxPowerError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Retrieving DUT Tx power failed.\n{str(error)}') from error
        return txPower

    def setDutTxPower(self, powerLevel: int):
        print()
        pretty.printInfo(f'Setting DUT Tx power to {str(powerLevel)} ...')
        try:
            self._dutConnection.setTxPower(self.serialNumber, powerLevel)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.WriteError,
                                description=dt.ReportDescriptions.setDutTxPowerError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Setting DUT Tx power failed.\n{str(error)}') from error
    
    def bypassLNA(self):
        print()
        pretty.printInfo(f'Bypassing LNA ...')
        try:
            self._dutConnection.bypassLNA(self.serialNumber)
        except Exception as error:
            raise Exception(
                f'Bypassing LNA failed.\n{str(error)}') from error

    def restoreLNA(self):
        print()
        pretty.printInfo(f'Restoring LNA ...')
        try:
            self._dutConnection.restoreLNA(self.serialNumber)
        except Exception as error:
            raise Exception(
                f'Restoring LNA failed.\n{str(error)}') from error
    
    def findDeviceId(self, devType: str) -> dict:
        print()
        pretty.printInfo("Finding Device Id ...")
        try:
            deviceId = sc.autoFindDevice(deviceType=devType)
        except Exception as error:
            raise Exception(
                f"Finding Device Id failed.\n{str(error)}") from error
        return deviceId
    
    def getRtcRatio(self) -> float:
        print()
        pretty.printInfo("Retrieving RTC Ratio ...")
        try:
            rtcRatio = self._dutConnection.getRtcRatio(deviceId=self.serialNumber)
            return rtcRatio
        except Exception as error:
            raise Exception(
                f"Retrieving RTC Ration failed.\n{str(error)}") from error

    def findDevicesIds(self, deviceWaitTime: float):
        print()
        pretty.printInfo("Finding Devices Ids ...")
        try:
            self.waitForTagConnection(timeout=deviceWaitTime,
                                      log=False,
                                      attachedTags=True)
            self.tagId = self._dutConnection.getHardwareID(deviceId=self.serialNumber)
            self.masterId = self._masterConnection.getHardwareID(deviceId=self.masterSerialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.hardwareIdError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Finding Devices Ids failed.\n{str(error)}') from error

    def flashFirmware(self,
                      fwImageVersion: FirmwareVersion,
                      dutVersions: Optional[Versions] = None,
                      device: str = "Uwb",
                      useHardwareId: bool = False):

        OTWUpdate = False

        if (self.targetProduct == dt.product.SWIFT):
            if device == "App":
                if not dutVersions:
                    dfuMode = True
                else:
                    if (fwImageVersion.isSwiftUSBFwUpdateSupported(dutVersions.appMcuVersion)):
                        dfuMode = False
                    else:
                        dfuMode = True
                
                if (fwImageVersion.isSwiftUSBFwUpdateSupported(fwImageVersion.appVersion)):
                    bootMbr = True
                else:
                    bootMbr = False
                
                if dfuMode:
                    try:
                        dfu.askForDFUMode()
                    except Exception as error:
                        self.addBooleanRecordToLog("DFU_MODE_QA", False)
                        raise Exception(
                            f'Flashing {device} image failed.\n{str(error)}') from error
                    self.addBooleanRecordToLog("DFU_MODE_QA", True)
                    if bootMbr:
                        boot.bootSwiftWithMbr(self,
                                            mbrImagePath=fwImageVersion.mbrImagePath,
                                            appBankABImagePath=fwImageVersion.appImagePathBankA,
                                            verType=fwImageVersion.versionType)
                    else:
                        boot.bootSwift(self,
                                    appImagePath=fwImageVersion.appImagePathBankA,
                                    uwbImagePath=fwImageVersion.uwbImagePath,
                                    verType=fwImageVersion.versionType)
                else:
                    OTWUpdate = True
            else:
                OTWUpdate = True
                print()
                dfu.promptStandbyMode()
        
        elif (self.targetProduct == dt.product.CIVET):
            if (not dutVersions and (device == "App")):
                boot.bootCivet(self,
                               mbrImagePath=fwImageVersion.mbrImagePath,
                               appBankAImagePath=fwImageVersion.appImagePathBankA,
                               appBankBImagePath=fwImageVersion.appImagePathBankB)
            else:
                OTWUpdate = True

        if OTWUpdate:
            waitIndicator = WaitIndicator()
            print()
            pretty.printInfo(f'Flashing {device} image ...')
            print()
            waitIndicator.start(f'Preparing {device}')
            try:
                if self.useAeolusPy:
                    if (device == "App"):
                        dlg.cmdSafeSend(tagId=(self.serialNumber if not useHardwareId else self.tagId),
                                        cmd="flashfw",
                                        data=0,
                                        stringData=fwImageVersion.appImagePath)
                    elif (device == "Uwb"):
                        dlg.cmdSafeSend(tagId=(self.serialNumber if not useHardwareId else self.tagId),
                                        cmd="flashfw",
                                        data=1,
                                        stringData=fwImageVersion.uwbImagePath)
                else:
                    if (device == "App"):
                        self._firmwareFlashConnection.flashFW(deviceId=(self.serialNumber if not useHardwareId else str(self.tagId).upper()[:11]),
                                                              fwImage=fwImageVersion.appImagePath,
                                                              device=device)
                    elif (device == "Uwb"):
                        self._firmwareFlashConnection.flashFW(deviceId=(self.serialNumber if not useHardwareId else str(self.tagId).upper()[:11]),
                                                              fwImage=fwImageVersion.uwbImagePath,
                                                              device=device)
                self.addBooleanRecordToLog(f"{device}Mcu_{fwImageVersion.versionType}_FW_Flash", True)
            except Exception as error:
                self.addBooleanRecordToLog(f"{device}Mcu_{fwImageVersion.versionType}_FW_Flash", False)
                self.logErrorReport(code=dt.ErrorCodes.WriteError,
                                    description=dt.ReportDescriptions.firmwareFlashError,
                                    exception=error,
                                    line=sc.getLineNumber())
                raise Exception(
                    f'Flashing {device} image failed.\n{str(error)}') from error
            finally:
                waitIndicator.stop()
    
    def getCurrent(self):
        print()
        pretty.printInfo("Reading slow sensor ...")
        try:
            self._slowSensorConnection = ds.SlowSensorClient()
            current_mA = self._slowSensorConnection.getAvgCurrent(self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.slowSensorError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Reading slow sensor failed.\n{str(error)}') from error
        return current_mA
    
    def getExtendedBattery(self) -> dt.ExtendedBattery:
        print()
        pretty.printInfo("Reading slow sensor ...")
        try:
            self._extendedSlowSensorConnection = ds.ExtendedSlowSensorClient()
            extendedBattery = self._extendedSlowSensorConnection.getExtendedBattery(
                self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.extendedSlowSensorError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Reading extended battery failed.\n{str(error)}') from error
        return extendedBattery

    def getPressure(self) -> dt.PressureSensor:
        print()
        pretty.printInfo("Reading pressure sensor ...")
        try:
            self._extendedSlowSensorConnection = ds.ExtendedSlowSensorClient()
            pressureSensor = self._extendedSlowSensorConnection.getPressure(self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.slowSensorError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Reading slow sensor failed.\n{str(error)}') from error
        return pressureSensor
    
    def getStandbyCurrent(self):
        print()
        pretty.printInfo("Recording standby current ...")
        try:
            self.disableCharger()
            self.recordCurrent("Standby")
            self.enableCharger()
        except Exception as error:
            raise Exception(
                f'Recording standby current failed.\n{str(error)}') from error
    
    def checkOnline(self) -> bool:
        print()
        pretty.printInfo("Checking if the DUT is connected to the network ...")
        try:
            self._rangingConnection = ds.RangingClient()
            retVal = self._rangingConnection.checkOnline(self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.rangingDataError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Reading ranging data failed.\n{str(error)}') from error
        return retVal
    
    def getPSR(self):
        print()
        pretty.printInfo("Checking the Packet Success Rate ...")
        try:
            retVal = self._networkMetricsConnection.getPSR(self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ReadError,
                                description=dt.ReportDescriptions.networkMetricsError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Reading network metrics failed.\n{str(error)}') from error
        return retVal
    
    def turnOff(self):
        print()
        pretty.printInfo("Turning off the DUT ...")
        try:
            self._masterConnection.turnOff(deviceId=self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.dutOffError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Turning off the DUT failed.\n{str(error)}') from error
    
    def turnOffUwb(self):
        print()
        pretty.printInfo("Turning off the DUT ...")
        try:
            self._dutConnection.turnOffUwb(deviceId=self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.uwbOffError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Turning off the DUT failed.\n{str(error)}') from error
    
    def turnOnUwb(self):
        print()
        pretty.printInfo("Turning on the DUT ...")
        try:
            self._dutConnection.turnOnUwb(deviceId=self.serialNumber)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.uwbOnError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Turning onthe DUT failed.\n{str(error)}') from error

    def formatDUT(self):
        print()
        pretty.printInfo("Formatting the DUT ...")
        print()
        try:
            self.stopSession()
            self.formatTag()
            self.resetTag()
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.dutFormatError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f"Formatting the DUT failed.\n{str(error)}") from error
    
    def runLiveTest(self, testName: str):
        print()
        pretty.printInfo("Running Live Test ...")
        try:
            self._dutConnection.runLiveTest(deviceId=self.serialNumber,
                                            testName=testName)
        except Exception as error:
            self.logErrorReport(code=dt.ErrorCodes.ConnectionError,
                                description=dt.ReportDescriptions.runLiveTestError,
                                exception=error,
                                line=sc.getLineNumber())
            raise Exception(
                f'Running Live test failed.\n{str(error)}') from error
        print()
        pretty.printInfo("Getting Live Test result ...")
        try:
            retVal = self._liveTestConnection.getLiveTestValue(
                deviceId=self.serialNumber)
        except Exception as error:
            raise Exception(
                f'Getting Live test failed.\n{str(error)}') from error
        return retVal

    def printDaemonVersion(self, daemonVersionString):
        """Prints Daemon version on the screen.
        
        Params:
            daemonVersionString: string containing the Daemon version.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f'Daemon {str(daemonVersionString)}')
        pretty.printInfo("********************************")

    def printVersions(self,
                      versions: Versions):
        """Prints UWB, App and Hardware versions on the screen.
        
        Params:
            Version object containing:
                uwbVersion: string containing the UWB QA version.
                appVersion: string containing the App QA version.
                hardwareVersion: string containing the Hardware version.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f'MCUAPP: {str(versions.appMcuVersion)}')
        pretty.printInfo(f'MCUWB: {str(versions.uwbMcuVersion)}')
        pretty.printInfo(f'HW: {str(versions.hwVersion)}')
        if versions.daemonVersion:
            pretty.printInfo(f'Daemon: {str(versions.daemonVersion)}')
        pretty.printInfo("********************************")

    def printHardwareVariant(self,
                             device: str,
                             hardwareVariant: dt.HardwareVariant):
        """Prints Hardware Variant on the screen.
        
        Params:
            device: string containing AppMcu or UwbMcu.
            hardwareVariant: hardware variant object containing
                             the DUT hardware variant.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(
            f'{str(device)}_Pcb_Type: {str(hardwareVariant.pcbType)}')
        pretty.printInfo(
            f'{str(device)}_Pcb_Revision: {str(hardwareVariant.pcbRevision)}')
        pretty.printInfo(
            f'{str(device)}_BOM_Variant: {str(hardwareVariant.bomVariant)}')
        pretty.printInfo(
            f'{str(device)}_BOM_Revision: {str(hardwareVariant.bomRevision)}')
        pretty.printInfo(
            f'{str(device)}_Assembly_Variant: {str(hardwareVariant.assemblyVariant)}')
        pretty.printInfo("********************************")

    def printTxPower(self, txPower: dt.TxPower):
        """Prints Tx power levels on the screen
        
        Params:
            txPower: Object containing the Tx powes.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f'Tx Avg Power: {str(txPower.txAvgPower)}')
        pretty.printInfo(f'Tx Chirp Power: {str(txPower.txChirpPower)}')
        pretty.printInfo(f'Tx Data Power: {str(txPower.txDataPower)}')
        pretty.printInfo("********************************")

    def printCurrent(self, current_mA):
        """Prints current consumption level in mA on the screen
        
        Params:
            current_mA: integer containing the current consumption level in mA.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f'Current [mA]: {str(current_mA)}')
        pretty.printInfo("********************************")
    
    def printExtendedBattery(self, extBattery: dt.ExtendedBattery):
        """Prints extended battery info on the screen
        
        Params:
            extBattery: extended battery object.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f'State of Charge [%]: {str(extBattery.stateOfCharge)}')
        pretty.printInfo(f'Voltage [mV]: {str(extBattery.voltage)}')
        pretty.printInfo(f'Average Current [mA]: {str(extBattery.averageCurrent)}')
        pretty.printInfo("********************************")

    def logExtendedBattery(self, extBattery: dt.ExtendedBattery):
        """Logs xtended battery info into the log file
        
        Params:
            extBattery: extended battery object.

        Returns:
            None.
        """
        self.addRecordToLog(f'FuelGauge_Average_Charge_State[%]', extBattery.stateOfCharge)
        self.addRecordToLog(f'FuelGauge_Battery_Voltage[mV]', extBattery.voltage)
        self.addRecordToLog(f'FuelGauge_Average_Current[mA]', extBattery.averageCurrent)

    def printPressure(self, pressure, temperature):
        """Prints Pressure as read from pressure sensor.
        
        Params:
            pressure: Pa.
            temperature: Celcius.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f'Pressure: {str(pressure)}')
        pretty.printInfo(f'Temperature: {str(temperature)}')
        pretty.printInfo("********************************")


    def logPressure(self, pressure, temperature):
        """Logs Pressure as read from pressure sensor.
        
        Params:
            pressure: hPa.
            temperature: Celcius.

        Returns:
            None.
        """
        self.addRecordToLog(f'Pressure', pressure)
        self.addRecordToLog(f'Temperature', temperature)
    
    def printRtcRatio(self, rtcRatio: float) -> None:
        """Prints RTC ratio.
        
        Params:
            rtcRatio: RTC ratio.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f'RTC Ratio: {str(rtcRatio)}')
        pretty.printInfo("********************************")
    
    def logRtcRatio(self, rtcRatio: float) -> None:
        """Logs RTC ratio
        
        Params:
            rtcRatio: RTC ratio

        Returns:
            None.
        """
        self.addRecordToLog(f'32K_VS_32M', str(rtcRatio))

    def logCurrentConsumption(self, pre_label: str, post_label: str, current_mA: float):
        """Logs current consumption level in mA into the log file
        
        Params:
            current_mA: integer containing the current consumption level in mA.
            label: string containing Online or Standby.

        Returns:
            None.
        """
        self.addRecordToLog(f'{pre_label}_Current_{post_label}[mA]', current_mA)

    def addTxPowerToLog(self, powType: str, txPower: dt.TxPower):
        """Logs Tx power levels into the log file
        
        Params:
            txPower: Object containing the Tx powes.

        Returns:
            None.
        """
        self.addRecordToLog(f'{str(powType)}_Tx_Avg_Power',
                            str(txPower.txAvgPower))
        self.addRecordToLog(f'{str(powType)}_Tx_Chirp_Power',
                            str(txPower.txChirpPower))
        self.addRecordToLog(f'{str(powType)}_Tx_Data_Power',
                            str(txPower.txDataPower))

    def logVersions(self,
                    versions: Versions):
        """Logs UWB, App and Hardware versions into the log file.
        
        Params:
            Version object containing:
                uwbVersion: string containing the UWB QA version.
                appVersion: string containing the App QA version.
                hardwareVersion: string containing the Hardware version.

        Returns:
            None.
        """
        self.addVersionNumbers(versions)

    def logQAVersions(self,
                      versions: Versions):
        """Logs UWB QA, App QA and Hardware versions into the log file.
        
        Params:
            Version object containing:
                uwbVersion: string containing the UWB QA version.
                appVersion: string containing the App QA version.
                hardwareVersion: string containing the Hardware version.

        Returns:
            None.
        """
        self.addRecordToLog("MCUWB_QA_FW_VERSION", str(versions.uwbMcuVersion))
        self.addRecordToLog("MCUAPP_QA_FW_VERSION", str(versions.appMcuVersion))
        self.addRecordToLog("HW_VERSION", str(versions.hwVersion))

    def logRelVersions(self,
                       versions: Versions):
        """Logs UWB Release, App Release and Hardware versions into the log file.
        
        Params:
            Version object containing:
                uwbVersion: string containing the UWB QA version.
                appVersion: string containing the App QA version.
                hardwareVersion: string containing the Hardware version.

        Returns:
            None.
        """
        self.addRecordToLog("MCUWB_REL_FW_VERSION", str(versions.uwbMcuVersion))
        self.addRecordToLog("MCUAPP_REL_FW_VERSION", str(versions.appMcuVersion))
        self.addRecordToLog("HW_VERSION", str(versions.hwVersion))

    def logMasterVersions(self,
                          versions: Versions):
        """Logs UWB Release, App Release and Hardware versions into the log file.
        
        Params:
            Version object containing:
                uwbVersion: string containing the UWB QA version.
                appVersion: string containing the App QA version.
                hardwareVersion: string containing the Hardware version.

        Returns:
            None.
        """
        self.addRecordToLog("MCUWB_MASTER_FW_VERSION", str(versions.uwbMcuVersion))
        self.addRecordToLog("MCUAPP_MASTER_FW_VERSION", str(versions.appMcuVersion))
        self.addRecordToLog("MASTER_HW_VERSION", str(versions.hwVersion))
        if versions.daemonVersion:
            self.addRecordToLog("DAEMON_VERSION", str(versions.daemonVersion))

    def logDaemonVersion(self, daemonVersion: Version):
        """Logs Daemon version into the log file.
        
        Params:
            daemonVersionString: object containing the Daemon's version.

        Returns:
            None.
        """
        self.addRecordToLog("DAEMON_VERSION", str(daemonVersion))

    def logHardwareVariant(self,
                           label: str,
                           device: str,
                           hardwareVariant: dt.HardwareVariant):
        """Logs Hardware Variant into the log file.
        
        Params:
            label: string containing the label text.
            device: string containing AppMcu or UwbMcu.
            hardwareVariant: hardware variant object containing the DUT hardware variant.

        Returns:
            None.
        """
        self.addRecordToLog(f'{str(label)}_{str(device)}_Pcb_Type',
                            str(hardwareVariant.pcbType))
        self.addRecordToLog(f'{str(label)}_{str(device)}_Pcb_Revision',
                            str(hardwareVariant.pcbRevision))
        self.addRecordToLog(f'{str(label)}_{str(device)}_BOM_Variant',
                            str(hardwareVariant.bomVariant))
        self.addRecordToLog(f'{str(label)}_{str(device)}_BOM_Revision',
                            str(hardwareVariant.bomRevision))
        self.addRecordToLog(f'{str(label)}_{str(device)}_Assembly_Variant',
                            str(hardwareVariant.assemblyVariant))
    
    def printImu(self, imuData: Imu) -> None:
        """Prints IMU data on the screen.
        
        Params:
            imuData: imu data object.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(str(imuData))
        pretty.printInfo("********************************")

    def logImu(self, imuData: Imu) -> None:
        """Logs IMU data into the log file.
        
        Params:
            imuData: imu data object.

        Returns:
            None.
        """
        self.addRecordToLog('IMU_ST_AXL_X', str(imuData.accel.X))
        self.addRecordToLog('IMU_ST_AXL_Y', str(imuData.accel.Y))
        self.addRecordToLog('IMU_ST_AXL_Z', str(imuData.accel.Z))
        self.addRecordToLog('IMU_ST_GYR_X', str(imuData.gyro.X))
        self.addRecordToLog('IMU_ST_GYR_Y', str(imuData.gyro.Y))
        self.addRecordToLog('IMU_ST_GYR_Z', str(imuData.gyro.Z))
        self.addRecordToLog('MAG_ST_X', str(imuData.magnet.X))
        self.addRecordToLog('MAG_ST_Y', str(imuData.magnet.Y))
        self.addRecordToLog('MAG_ST_Z', str(imuData.magnet.Z))
    
    def printPsr(self, psrData: Psr) -> None:
        """Prints PSR data on the screen.
        
        Params:
            psrData: PSR data object.

        Returns:
            None.
        """
        pretty.printInfo("********************************")
        pretty.printInfo(f"Average PSR: {str(psrData.value)}")
        pretty.printInfo("********************************")

    def logPsr(self, psrData: Psr) -> None:
        """Logs PSR data into the log file.
        
        Params:
            psrData: PSR data object.

        Returns:
            None.
        """
        self.addRecordToLog('UWB_PERC', str(psrData.value))

    @staticmethod
    def ensureHardwareVariant(config: ProductionConfig,
                              checkAssemblyVar: bool = False) -> None:
        if config.hardwareVariant.pcbType == dt.HardwarePcbType.PcbTypeUnknown:
            raise ValueError('Production config has not specified a Pcb Type.')
        if config.hardwareVariant.pcbRevision == None:
            raise ValueError('Production config has not specified a Pcb Revision.')
        if config.hardwareVariant.bomVariant == dt.HardwareBomVariant.NoBomVariant:
            raise ValueError('Production config has not specified a BOM Variant.')
        if config.hardwareVariant.bomRevision == dt.HardwareBomRevision.NoBomRevision:
            raise ValueError('Production config has not specified a BOM Revision.')
        if checkAssemblyVar:
            if config.hardwareVariant.assemblyVariant == dt.HardwareAssemblyVariant.NoAssemblyVariant:
                raise ValueError('Production config has not specified an Assembly Variant.')

    def checkHardwareVariant(self, args: Parser, config: ProductionConfig):
        if not args.skipConfigCheck:    
            if self.hardwareVariantAppMcu.pcbType != config.hardwareVariant.pcbType:
                raise Exception("Device under test does not match expected PCB type")
            if self.hardwareVariantAppMcu.pcbRevision != config.hardwareVariant.pcbRevision:
                raise Exception("Device under test does not match expected PCB revision")

        unprogrammedVariant = dt.HardwareVariant()
        unprogrammedVariant.setUnprogrammed(config.hardwareVariant.pcbType, config.hardwareVariant.pcbRevision)
        
        if ((self.hardwareVariantAppMcu.pcbType != config.hardwareVariant.pcbType and
            self.hardwareVariantAppMcu.pcbType != unprogrammedVariant.pcbType) or
            (self.hardwareVariantAppMcu.pcbRevision != config.hardwareVariant.pcbRevision and
            self.hardwareVariantAppMcu.pcbRevision != unprogrammedVariant.pcbRevision) or
            (self.hardwareVariantAppMcu.bomVariant != config.hardwareVariant.bomVariant and
            self.hardwareVariantAppMcu.bomVariant != unprogrammedVariant.bomVariant) or
            (self.hardwareVariantAppMcu.bomRevision != config.hardwareVariant.bomRevision and
            self.hardwareVariantAppMcu.bomRevision != unprogrammedVariant.bomRevision) or
            (self.hardwareVariantAppMcu.assemblyVariant != config.hardwareVariant.assemblyVariant and
            self.hardwareVariantAppMcu.assemblyVariant != unprogrammedVariant.assemblyVariant) and
            not args.skipConfigCheck):
            raise Exception("Programmed hardware variant in AppMcu does not match the production config variant.")