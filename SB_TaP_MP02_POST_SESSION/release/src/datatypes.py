"""Shared datatypes.

Author: Sportable
Date: 27 Jun 2022

Copyright (c) 2022, Sportable Technologies. All rights reserved.

"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

@dataclass
class Gyro:
    X: float
    Y: float
    Z: float
    scale: float = 140

@dataclass
class Accel:
    X: float
    Y: float
    Z: float
    scale: float = 0.488

@dataclass
class Magnet:
    X: float
    Y: float
    Z: float
    scaleSwift: float = 1.524999976158142
    scaleCivet: float = (1 / 1711)

class testStage:
    """Production testing stages."""
    BOOT: str = "Boot"
    MAIN: str = "Main"
    GNSS: str = "GNSS"
    ASSEMBLED: str = "Assembled"
    PRESSURE: str = "Pressure"
    FULL: str = "Full"
    VALVE: str = "Valve"
    BLADDER: str = "Bladder"
    BALL: str = "Ball"
    SWIFT: str = "Swift"

class testType(Enum):
    PRE_KICK = 0
    POST_KICK = 1

class FirmwareType(Enum):
    RELEASE = 0
    INTERNAL = 1

class product(Enum):
    """Supported products by this test."""
    UNKNOWN = 0
    AEOLUS= 1
    CIVET = 2
    SWIFT = 3
    LYNX = 4

class cmd:
    """ ... """
    STOP: str = "stop"
    START: str = "start"
    FORMAT: str = "format"
    FLASH: str = "flashfw"
    RESET: str = "reset"
    OFFLOAD: str = "offload"
    CHARGER: str = "charger"
    DEVCTX: str = "getdev"
    SESCTX: str = "getsesctx"
    SESCFG: str = "getsescfg"
    SETID: str = "setid"
    SHUTDOWN: str = "shutdown"

class LiveTest:
    BUZZER: str = "buzzerTest"
    LED_WHITE: str = "ledWhiteTest"
    LED_RGB: str = "ledRgbTest"
    LED_STANDBY: str = "ledStandbyTest"
    LED_SNIFF: str = "ledSniffTest"
    LED_SCAN: str = "ledScanTest"
    LED_ONLINE: str = "ledOnlineTest"
    CURRENT_ONLINE: str = "currentOnlineTest"
    CURRENT_SNIFF: str = "currentSniffTest"
    CURRENT_SCAN: str = "currentScanTest"
    CURRENT_STANDBY: str = "currentStandbyTest"
    CURRENT_CHARGING: str = "currentChargingTest"
    CURRENT_CHARGED: str = "currentChargedTest"
    EX_FLASH_DEVICE_ID: str = "exFlashDeviceIdTest"
    EX_FLASH_REPEATED_WRITE: str = "exFlashRepeatedWriteTest"

class ReportDescriptions:
    initDfu: str = "Failed to initialise DFU mode"
    valueError: str = "Wrong value"
    memoryError: str = "Failed to retrieve data"
    dataProcessingError: str = "Failed to process data"
    tagUSBConnectionError: str = "Tag not connected over the USB"
    masterUSBConnectionError: str = "Master not connected over the USB"
    hardwareIdError: str = "Failed to retrieve hardware id"
    eraseHardwareVariantError: str = "Failed to erase hardware variant"
    getHardwareVariantError: str = "Failed to retrieve hardware variant"
    setHardwareVariantError: str = "Failed to set hardware variant"
    getMasterFirmwareVersionError: str = "Failed to retrieve master firmware version"
    getDutFirmwareVersionError: str = "Failed to retrieve DUT firmware version"
    getMasterTxPowerError: str = "Failed to retrieve master Tx power"
    getDutTxPowerError: str = "Failed to retrieve DUT Tx power"
    setDutTxPowerError: str = "Failed to set DUT Tx power"
    resetMasterDeviceError: str = "Failed to reset master device"
    resetDutError: str = "Failed to reset the DUT"
    firmwareFlashError: str = "Failed to flash firmware"
    rangingDataError: str = "Failed to retrieve ranging data"
    networkMetricsError: str = "Failed to retrieve network metrics data"
    slowSensorError: str = "Failed to retrieve slow sensor data"
    extendedSlowSensorError: str = "Failed to retrieve extended slow sensor data"
    dutOffError: str = "Failed to turn off the DUT"
    uwbOffError: str = "Failed to turn off the UWB"
    uwbOnError: str = "Failed to turn on the UWB"
    dutFormatError: str = "Failed to format the DUT"
    runLiveTestError: str = "Failed to run live test"
    getIdFromJtagError: str = "Failed to retrieve Id from JTAG"
    exportImuDataError: str = "Failed to export IMU data"
    processImuDataError: str = "Failed to process IMU data"
    exportPsrDataError: str = "Failed to export PSR data"
    processPsrDataError: str = "Failed to process PSR data"

class ErrorModule:
    productionTestModule: str = "productionTestModule"

class ErrorCodes:
    Success: str = "Success"
    InternalError: str = "Internal"
    AllocError: str = "Alloc"
    InvalidAddressError: str = "InvalidAddress"
    ResourceError: str = "Resource"
    OutOfBoundsError: str = "OutOfBounds"
    NullDataError: str = "NullData"
    EmptyDataError: str = "EmptyData"
    IncompleteDataError: str= "IncompleteData"
    InvalidLengthError: str = "InvalidLength"
    InvalidDataError: str = "InvalidData"
    InvalidCRCError: str = "InvalidCRC"
    NotFoundError: str = "NotFound"
    NotAvailableError: str = "NotAvailable"
    NotSupportedError: str = "NotSupported"
    NotEnabledError: str = "NotEnabled"
    NotAllowedError: str = "NotAllowed"
    BusyError: str = "Busy"
    ReadError: str = "Read"
    WriteError: str = "Write"
    InvalidStateError: str = "InvalidState"
    NackError: str = "Nack"
    InvalidParamError: str = "InvalidParam"
    TimeoutError: str = "Timeout"
    RetryError: str = "Retry"
    NoHandlerError: str = "NoHandler"
    SyncError: str = "Sync"
    MutexError: str = "Mutex"
    NotDoneError: str = "NotDone"
    NotEmptyDataError: str = "NotEmpty"
    EraseError: str = "Erase"
    NotInit: str = "NotInit"
    EventFailedError: str = "EventFailed"
    NotProcessedError: str = "NotProcessed"
    AssertionError: str = "Assertion"
    IgnoredError: str = "Ignored"
    ConnectionError: str = "Connection"
    NoError: str = "NoError"
    MaxError: str = "MaxError"

class ErrorLayer:
    eUnknownModule: str= "Unknown"
    eSoCModule: str = "SoC"
    eSDKModule: str = "SDK"
    eKernelModule: str = "Kernel"
    eGlueModule: str = "Glue"
    eCommsModule: str = "Comms"
    eDriverModule: str = "Driver"
    eHalModule: str = "Hal"
    eApiModule: str = "Api"
    eProtocolModule: str = "Protocol"
    eSensorModule: str = "Sensor"
    eProcessModule: str = "Process"
    eAppModule: str = "App"
    eTestModule: str = "Test"
    eNoLayerModule: str = "NoLayer"
    eMaxModule: str = "Max"

@dataclass
class ReturnCode:
    code: ErrorCodes = ErrorCodes.Success
    layer: ErrorLayer = ErrorLayer.eUnknownModule
    line: int = 0

class HardwarePcbType:
    """Supported PCB types"""
    PcbTypeUnknown: str = "PcbTypeUnknown"
    PcbTypeReserved: str = "PcbTypeReserved"
    PcbTypeCivet: str = "PcbTypeCivet"
    PcbTypeSwift: str = "PcbTypeSwift"
    PcbTypeMeerkat: str = "PcbTypeMeerkat"
    PcbTypeNotProgrammed: str = "PcbTypeNotProgrammed"
    def as_dict():
        return {  
            HardwarePcbType.PcbTypeUnknown : 0,
            HardwarePcbType.PcbTypeReserved : 1,
            HardwarePcbType.PcbTypeCivet : 2,
            HardwarePcbType.PcbTypeSwift : 3,
            HardwarePcbType.PcbTypeMeerkat : 4,
            HardwarePcbType.PcbTypeNotProgrammed : 63}

class HardwareBomVariant:
    """Possible hardware bom variants"""
    NoBomVariant: str = "NoBomVariant"
    BomVariantAlpha: str = "BomVariantAlpha"
    BomVariantBravo: str = "BomVariantBravo"
    BomVariantCharlie: str = "BomVariantCharlie"
    BomVariantDelta: str = "BomVariantDelta"
    BomVariantEcho: str = "BomVariantEcho"
    BomVariantAlphaAlpha: str = "BomVariantAlphaAlpha"
    BomVariantNotProgrammed: str = "BomVariantNotProgrammed"
    def as_dict():
        return {    
            HardwareBomVariant.NoBomVariant : 0,
            HardwareBomVariant.BomVariantAlpha : 1,
            HardwareBomVariant.BomVariantBravo : 2,
            HardwareBomVariant.BomVariantCharlie : 3,
            HardwareBomVariant.BomVariantDelta : 4,
            HardwareBomVariant.BomVariantEcho : 5,
            HardwareBomVariant.BomVariantAlphaAlpha : 27,
            HardwareBomVariant.BomVariantNotProgrammed : 63}

class HardwareBomRevision:
    """Possible hardware bom revisions"""
    NoBomRevision: str = "NoBomRevision"
    BomRevisionA: str = "BomRevisionA"
    BomRevisionB: str = "BomRevisionB"
    BomRevisionC: str = "BomRevisionC"
    BomRevisionD: str = "BomRevisionD"
    BomRevisionE: str = "BomRevisionE"
    BomRevisionF: str = "BomRevisionF"
    BomRevisionG: str = "BomRevisionG"
    BomRevisionH: str = "BomRevisionH"
    BomRevisionI: str = "BomRevisionI"
    BomRevisionJ: str = "BomRevisionJ"
    BomRevisionK: str = "BomRevisionK"
    BomRevisionL: str = "BomRevisionL"
    BomRevisionM: str = "BomRevisionM"
    BomRevisionN: str = "BomRevisionN"
    BomRevisionO: str = "BomRevisionO"
    BomRevisionP: str = "BomRevisionP"
    BomRevisionQ: str = "BomRevisionQ"
    BomRevisionR: str = "BomRevisionR"
    BomRevisionS: str = "BomRevisionS"
    BomRevisionT: str = "BomRevisionT"
    BomRevisionU: str = "BomRevisionU"
    BomRevisionV: str = "BomRevisionV"
    BomRevisionW: str = "BomRevisionW"
    BomRevisionX: str = "BomRevisionX"
    BomRevisionY: str = "BomRevisionY"
    BomRevisionZ: str = "BomRevisionZ"
    BomRevisionAA: str = "BomRevisionAA"
    BomRevisionNotProgrammed: str = "BomRevisionNotProgrammed"
    def as_dict():
        return { 
            HardwareBomRevision.NoBomRevision : 0,
            HardwareBomRevision.BomRevisionA : 1,
            HardwareBomRevision.BomRevisionB : 2,
            HardwareBomRevision.BomRevisionC : 3,
            HardwareBomRevision.BomRevisionD : 4,
            HardwareBomRevision.BomRevisionE : 5,
            HardwareBomRevision.BomRevisionF : 6,
            HardwareBomRevision.BomRevisionG : 7,
            HardwareBomRevision.BomRevisionH : 8,
            HardwareBomRevision.BomRevisionI : 9,
            HardwareBomRevision.BomRevisionJ : 10,
            HardwareBomRevision.BomRevisionK : 11,
            HardwareBomRevision.BomRevisionL : 12,
            HardwareBomRevision.BomRevisionM : 13,
            HardwareBomRevision.BomRevisionN : 14,
            HardwareBomRevision.BomRevisionO : 15,
            HardwareBomRevision.BomRevisionP : 16,
            HardwareBomRevision.BomRevisionQ : 17,
            HardwareBomRevision.BomRevisionR : 18,
            HardwareBomRevision.BomRevisionS : 19,
            HardwareBomRevision.BomRevisionT : 20,
            HardwareBomRevision.BomRevisionU : 21,
            HardwareBomRevision.BomRevisionV : 22,
            HardwareBomRevision.BomRevisionW : 23,
            HardwareBomRevision.BomRevisionX : 24,
            HardwareBomRevision.BomRevisionY : 25,
            HardwareBomRevision.BomRevisionZ : 26,
            HardwareBomRevision.BomRevisionAA : 27,
            HardwareBomRevision.BomRevisionNotProgrammed : 63}
    
class HardwareAssemblyVariant:
    """Possible hardware assembly variants"""
    NoAssemblyVariant: str = "NoAssemblyVariant"
    AssemblyVariantCivet: str = "AssemblyVariantCivet"
    AssemblyVariantSwift: str = "AssemblyVariantSwift"
    AssemblyVariantLynx: str = "AssemblyVariantLynx"
    AssemblyVariantMantis: str = "AssemblyVariantMantis"
    AssemblyVariantLynxPlus: str = "AssemblyVariantLynxPlus"
    AssemblyVariantLynxRetro: str = "AssemblyVariantLynxRetro"
    AssemblyVariantNotProgrammed: str = "AssemblyVariantNotProgrammed"
    def as_dict():
        return  {
            HardwareAssemblyVariant.NoAssemblyVariant : 0,
            HardwareAssemblyVariant.AssemblyVariantCivet : 1,
            HardwareAssemblyVariant.AssemblyVariantSwift : 2,
            HardwareAssemblyVariant.AssemblyVariantLynx : 3,
            HardwareAssemblyVariant.AssemblyVariantMantis : 4,
            HardwareAssemblyVariant.AssemblyVariantLynxPlus : 5,
            HardwareAssemblyVariant.AssemblyVariantLynxRetro : 6,
            HardwareAssemblyVariant.AssemblyVariantNotProgrammed : 63}

@dataclass
class ExtendedBattery:
    averageCurrent: Optional[int] = None
    fullAvailableCapacity: Optional[int] = None
    fullChargeCapacityFiltered: Optional[int] = None
    fullChargeCapacityUnfiltered: Optional[int] = None
    remainingCapacityFiltered: Optional[int] = None
    remainingCapacityUnfiltered: Optional[int] = None
    stateOfCharge: Optional[int] = None
    stateOfChargeUnfiltered: Optional[int] = None
    voltage: Optional[int] = None

@dataclass
class PressureSensor:
    pressure: Optional[float] = None
    temperature: Optional[float] = None

class TxPower:
    _MIN_POWER_VALUE = 1
    _MAX_POWER_VALUE = 68

    @property
    def txAvgPower(self):
        return self._txAvgPower
    
    @txAvgPower.setter
    def txAvgPower(self, power):
        if power >= TxPower._MIN_POWER_VALUE and power <= TxPower._MAX_POWER_VALUE:
            self._txAvgPower = power
        else:
            raise ValueError(
                f'txAvgPower of {power} is outside the allowed range')
    
    @property
    def txChirpPower(self):
        return self._txChirpPower
    
    @txChirpPower.setter
    def txChirpPower(self, power):
        if power >= TxPower._MIN_POWER_VALUE and power <= TxPower._MAX_POWER_VALUE:
            self._txChirpPower = power
        else:
            raise ValueError(
                f'txChirpPower of {power} is outside the allowed range')
    
    @property
    def txDataPower(self):
        return self._txDataPower
    
    @txDataPower.setter
    def txDataPower(self, power):
        if power >= TxPower._MIN_POWER_VALUE and power <= TxPower._MAX_POWER_VALUE:
            self._txDataPower = power
        else:
            raise ValueError(
                f'txDataPower of {power} is outside the allowed range')
    
    def __init__(self,
                 txAvgPower: int = None,
                 txChirpPower: int = None,
                 txDataPower: int = None) -> None:
        if txAvgPower:
            self.txAvgPower = txAvgPower
        if txChirpPower:
            self.txChirpPower = txChirpPower
        if txDataPower:
            self.txDataPower = txDataPower
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TxPower):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return (self.txAvgPower == other.txAvgPower and
                self.txChirpPower == other.txChirpPower and
                self.txDataPower == other.txChirpPower)
        

class HardwareVariant: 
    def __init__(self):
        self._pcbType = HardwarePcbType.PcbTypeUnknown
        self._pcbRevision = None
        self._bomVariant = HardwareBomVariant.NoBomVariant
        self._bomRevision = HardwareBomRevision.NoBomRevision
        self._assemblyVariant = HardwareAssemblyVariant.NoAssemblyVariant
    
    def __str__(self):
        return str( 
                    '{ pcbType : ' + self.pcbType + ',\n' + 
                    '  pcbRevision : ' + str(self.pcbRevision) + ',\n' +
                    '  bomVariant : ' + self.bomVariant + ',\n' + 
                    '  bomRevision : ' + self.bomRevision + ',\n' +
                    '  assemblyVariant : ' + self.assemblyVariant + ' }')

    def __eq__(self, other): 
        if not isinstance(other, HardwareVariant):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return (self.pcbType == other.pcbType and self.pcbRevision == other.pcbRevision and
                self.bomVariant == other.bomVariant and self.bomRevision == other.bomRevision and
                self.assemblyVariant == other.assemblyVariant)

    
    @property
    def pcbType(self):
        return self._pcbType

    @pcbType.setter
    def pcbType(self, value):
        if value in HardwarePcbType.as_dict():
            self._pcbType = value
        elif value is None:
            return
        else:
            raise ValueError(f"Unknown pcbType: {value}")


    @property
    def pcbRevision(self):
        return self._pcbRevision

    @pcbRevision.setter
    def pcbRevision(self, value):
        self._pcbRevision = value

    @property
    def bomVariant(self):
        return self._bomVariant

    @bomVariant.setter
    def bomVariant(self, value):
        if value in HardwareBomVariant.as_dict():
            self._bomVariant = value
        elif value is None:
            return
        else:
            raise ValueError(f"Unknown bomVariant: {value}")

    @property
    def bomRevision(self):
        return self._bomRevision

    @bomRevision.setter
    def bomRevision(self, value):
        if value in HardwareBomRevision.as_dict():
            self._bomRevision = value
        elif value is None:
            return
        else:
            raise ValueError(f"Unknown bomRevision: {value}")

    @property
    def assemblyVariant(self):
        return self._assemblyVariant

    @assemblyVariant.setter
    def assemblyVariant(self, value): 
        if value in HardwareAssemblyVariant.as_dict():
            self._assemblyVariant = value
        elif value is None:
            return
        else:
            raise ValueError(f"Unknown assemblyVariant: {value}")

    # TODO: Are devices be delivered with pcbType and pcbRevision programmed?
    # If not remove those arguments or just use default constructor
    def setUnprogrammed(self, pcbType, pcbRevision):
        self.pcbType = pcbType
        self.pcbRevision = pcbRevision
        self.bomVariant = HardwareBomVariant.BomVariantNotProgrammed
        self.bomRevision = HardwareBomRevision.BomRevisionNotProgrammed
        self.assemblyVariant = HardwareAssemblyVariant.AssemblyVariantNotProgrammed

class RangingServerError(ConnectionError):
    pass

class NetworkMetricsServerError(ConnectionError):
    pass

class SlowSensorServerError(ConnectionError):
    pass

class ExtendedSlowSensorServerError(ConnectionError):
    pass

class TcpServerError(ConnectionError):
    pass

class FlashingImageError(MemoryError):
    pass

class LiveTestChannelError(ConnectionError):
    pass

class OperatorInputError(ValueError):
    pass