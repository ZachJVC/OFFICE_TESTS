""" Class FirmwareVersion definition

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

from optparse import Option
import os
import re

from typing import Optional
from src.versions import Version

class FirmwareVersion:
    OTW_VERSION_STRING: str = "1.5.3.0"
    def __init__(self):
        self._appVersionString: Optional[str] = None
        self._appVersion: Optional[Version] = None
        self._uwbVersionString: Optional[str] = None
        self._uwbVersion: Optional[Version] = None
        self._appImagePath: Optional[str] = None
        self._appImagePathBankA: Optional[str] = None
        self._appImagePathBankB: Optional[str] = None
        self._mbrImagePath: Optional[str] = None
        self._appImagePathBankAHex: Optional[str] = None
        self._appImagePathBankBHex: Optional[str] = None
        self._uwbImagePath: Optional[str] = None
        self._versionType: Optional[str] = None
    
    @property
    def appVersionString(self) -> str:
        return self._appVersionString

    @appVersionString.setter
    def appVersionString(self, version: str) -> None:
        if str(version).strip():
            self._appVersionString = str(version)
    
    @property
    def appVersion(self) -> Version:
        return self._appVersion
    
    @appVersion.setter
    def appVersion(self, version: Version) -> None:
        self._appVersion = version
    
    @property
    def uwbVersionString(self) -> str:
        return self._uwbVersionString

    @uwbVersionString.setter
    def uwbVersionString(self, version: str) -> None:
        if str(version).strip():
            self._uwbVersionString = str(version)
    
    @property
    def uwbVersion(self) -> Version:
        return self._uwbVersion
    
    @uwbVersion.setter
    def uwbVersion(self, version: Version) -> None:
        self._uwbVersion = version

    @property
    def appImagePath(self) -> str:
        return self._appImagePath

    @appImagePath.setter
    def appImagePath(self, path: str) -> None:
        if str(path).strip():
            self._appImagePath = str(path)
    
    @property
    def appImagePathBankA(self) -> str:
        return self._appImagePathBankA

    @appImagePathBankA.setter
    def appImagePathBankA(self, path: str) -> None:
        if str(path).strip():
            self._appImagePathBankA = str(path)
    
    @property
    def appImagePathBankB(self) -> str:
        return self._appImagePathBankB

    @appImagePathBankB.setter
    def appImagePathBankB(self, path: str) -> None:
        if str(path).strip():
            self._appImagePathBankB = str(path)

    @property
    def mbrImagePath(self) -> str:
        return self._mbrImagePath

    @mbrImagePath.setter
    def mbrImagePath(self, path: str) -> None:
        if str(path).strip():
            self._mbrImagePath = str(path)

    @property
    def appImagePathBankAHex(self) -> str:
        return self._appImagePathBankAHex

    @appImagePathBankAHex.setter
    def appImagePathBankAHex(self, path: str) -> None:
        if str(path).strip():
            self._appImagePathBankAHex = str(path)
    
    @property
    def appImagePathBankBHex(self) -> str:
        return self._appImagePathBankBHex

    @appImagePathBankBHex.setter
    def appImagePathBankBHex(self, path: str) -> None:
        if str(path).strip():
            self._appImagePathBankBHex = str(path)

    @property
    def uwbImagePath(self) -> str:
        return self._uwbImagePath

    @uwbImagePath.setter
    def uwbImagePath(self, path: str) -> None:
        if str(path).strip():
            self._uwbImagePath = str(path)
    
    @property
    def versionType(self) -> str:
        return self._versionType
    
    @versionType.setter
    def versionType(self, versionType: str) -> None:
        self._versionType = versionType
    
    def __str__(self):
        return str(f'appVersionString: {str(self.appVersionString)}\n'
                   f'uwbVersionString: {str(self.uwbVersionString)}\n'
                   f'appVersionString: {str(self.appImagePath)}\n'
                   f'appImagePathBankA: {str(self.appImagePathBankA)}\n'
                   f'appImagePathBankB: {str(self.appImagePathBankB)}\n'
                   f'mbrImagePath: {str(self.mbrImagePath)}\n'
                   f'appImagePathBankAHex: {str(self.appImagePathBankAHex)}\n'
                   f'appImagePathBankBHex: {str(self.appImagePathBankBHex)}\n'
                   f'uwbImagePath: {str(self.uwbImagePath)}\n'
                   f'versionType: {str(self.versionType)}')

class QAFirmwareVersion (FirmwareVersion):
    def __init__(self, file_path: str):
        FirmwareVersion.__init__(self)

        with open(str(file_path),"r") as f:
            try:
                for line in f:
                    if line.split(':')[0] == 'App QA':
                        self.appVersionString = (line.split(':')[1]).replace('\n', '')
                    if line.split(':')[0] == 'Uwb QA':
                        self.uwbVersionString = (line.split(':')[1]).replace('\n', '')
            except Exception as error:
                raise Exception(
                    f"Parsing versions file '{str(file_path)}"
                    f"' failed with error:\n\t{str(error)}"
                ) from error
        self.versionType = "QA"
        self.appVersion = Version(self.appVersionString)
        self.uwbVersion = Version(self.uwbVersionString)

class ReleaseFirmwareVersion(FirmwareVersion):
    def __init__(self, file_path: str):
        FirmwareVersion.__init__(self)

        with open(str(file_path),"r") as f:
            try:
                for line in f:
                    if line.split(':')[0] == 'App Release':
                        self.appVersionString = (line.split(':')[1]).replace('\n', '')
                    if line.split(':')[0] == 'Uwb Release':
                        self.uwbVersionString = (line.split(':')[1]).replace('\n', '')
            except Exception as error:
                raise Exception(
                    f"Parsing versions file '{str(file_path)}"
                    f"' failed with error:\n\t{str(error)}"
                ) from error
        self.versionType = "Release"
        self.appVersion = Version(self.appVersionString)
        self.uwbVersion = Version(self.uwbVersionString)

class SwiftFirmwareVersion(FirmwareVersion):
    def __init__(self):
        self.appVersionString = str(self.appVersionString.replace('_', '.'))
        self.uwbVersionString = str(self.uwbVersionString.replace('_', '.'))
    
    def isSwiftUSBFwUpdateSupported(self, version: Version):       
        OTWVersion = Version(FirmwareVersion.OTW_VERSION_STRING)
        return version >= OTWVersion

class CivetFirmwareVersion(FirmwareVersion):
    def __init__(self):
        self.appVersionString = str(self.appVersionString.replace('_', '.'))
        self.uwbVersionString = str(self.uwbVersionString.replace('_', '.'))

class QASwiftFirmwareVersion(QAFirmwareVersion, SwiftFirmwareVersion):
    def __init__(self, file_path: str = "./images/QAVersions.txt"):
        QAFirmwareVersion.__init__(self, file_path=file_path)
        
        bootMbr = self.isSwiftUSBFwUpdateSupported(self.appVersion)
        if bootMbr:
            self.appImagePathBankA = (
                f'./images/mcuapp_{str(self.appVersionString)}/swift-ab.bin')
            if not os.path.isfile(self.appImagePathBankA):
                raise FileNotFoundError(f'No MCUAPP QA image available '
                                            f'@{self.appImagePathBankA}')
        else:
            self.appImagePathBankA = (
                f'./images/mcuapp_{str(self.appVersionString)}/swift-a.bin')
            if not os.path.isfile(self.appImagePathBankA):
                raise FileNotFoundError(f'No MCUAPP QA image available '
                                        f'@{self.appImagePathBankA}')
        self.appImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}')
        if not os.path.isdir(self.appImagePath):
            raise FileNotFoundError(f'No MCUAPP QA directory available '
                                    f'@{self.appImagePath}')
        self.mbrImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}/mbrSwift.bin')
        if not os.path.isfile(self.mbrImagePath):
            raise FileNotFoundError(f'No MBR QA image available '
                                    f'@{self.mbrImagePath}')
        self.uwbImagePath = (
            f'./images/mcuwb_{str(self.uwbVersionString)}'
            f'/mcuwbSwiftAnchor.bin')
        if not os.path.isfile(self.uwbImagePath):
            raise FileNotFoundError(
                f'No MCUWB QA image available @{self.uwbImagePath}')
        
        SwiftFirmwareVersion.__init__(self)

class ReleaseSwiftFirmwareVersion(ReleaseFirmwareVersion, SwiftFirmwareVersion):
    def __init__(self, file_path: str = "./images/QAVersions.txt"):
        ReleaseFirmwareVersion.__init__(self, file_path=file_path)

        bootMbr = self.isSwiftUSBFwUpdateSupported(self.appVersion)
        if bootMbr:
            self.appImagePathBankA = (
                f'./images/mcuapp_{str(self.appVersionString)}/swift-ab.bin')
            if not os.path.isfile(self.appImagePathBankA):
                raise FileNotFoundError(f'No MCUAPP Release image available '
                                            f'@{self.appImagePathBankA}')
        else:
            self.appImagePathBankA = (
                f'./images/mcuapp_{str(self.appVersionString)}/swift-a.bin')
            if not os.path.isfile(self.appImagePathBankA):
                raise FileNotFoundError(f'No MCUAPP Release image available '
                                        f'@{self.appImagePathBankA}')
        self.mbrImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}/mbrSwift.bin')
        if not os.path.isfile(self.mbrImagePath):
            raise FileNotFoundError(f'No MBR Release image available '
                                    f'@{self.mbrImagePath}')
        self.appImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}')
        if not os.path.isdir(self.appImagePath):
            raise IsADirectoryError(f'No MCUAPP Release dir available '
                                    f'@{self.appImagePath}')
        self.appImagePathBankA = (
            f'./images/mcuapp_{str(self.appVersionString)}'
            f'/swift-ab.bin')
        if not os.path.isfile(self.appImagePathBankA):
            raise FileNotFoundError(f'No MCUAPP Release image available '
                                    f'@{self.appImagePathBankA}')
        self.uwbImagePath = (
            f'./images/mcuwb_{str(self.uwbVersionString)}'
            f'/mcuwbSwiftTag.bin')
        if not os.path.isfile(self.uwbImagePath):
            raise FileNotFoundError(f'No MCUWB Release image available '
                                    f'@{self.uwbImagePath}')
        
        SwiftFirmwareVersion.__init__(self)

class QACivetFirmwareVersion(QAFirmwareVersion, CivetFirmwareVersion):
    def __init__(self, file_path: str = "./images/QAVersions.txt"):
        QAFirmwareVersion.__init__(self, file_path=file_path)

        self.mbrImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}/mbr.hex')
        if not os.path.isfile(self.mbrImagePath):
            raise FileNotFoundError(f'No MBR QA image available '
                                    f'@{self.mbrImagePath}')
        self.appImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}')
        if not os.path.isdir(self.appImagePath):
            raise FileNotFoundError(f'No MCUAPP QA directory available '
                                    f'@{self.appImagePath}')
        self.appImagePathBankA = (f'{self.appImagePath}/civet-a.bin')
        if not os.path.isfile(self.appImagePathBankA):
            raise FileNotFoundError(f'No MCUAPP QA image available '
                                    f'@{self.appImagePathBankA}')
        self.appImagePathBankB = (f'{self.appImagePath}/civet-b.bin')
        if not os.path.isfile(self.appImagePathBankB):
            raise FileNotFoundError(f'No MCUAPP QA image available '
                                    f'@{self.appImagePathBankB}')
        self.appImagePathBankAHex = (
            f'{self.appImagePath}/civet-a.hex')
        if not os.path.isfile(self.appImagePathBankAHex):
            raise FileNotFoundError(f'No MCUAPP QA image available '
                                f'@{self.appImagePathBankAHex}')
        self.appImagePathBankBHex = (
            f'{self.appImagePath}/civet-b.hex')
        if not os.path.isfile(self.appImagePathBankBHex):
            raise FileNotFoundError(f'No MCUAPP QA image available '
                                    f'@{self.appImagePathBankBHex}')
        self.uwbImagePath = ('./images/mcuwb_' +
                                str(self.uwbVersionString.replace('.', '_')) +
                                '/mcuwbCivetAnchor.bin')
        if not os.path.isfile(self.uwbImagePath):
            raise FileNotFoundError(f'No MCUWB QA image available '
                                    f'@{self.uwbImagePath}')

        CivetFirmwareVersion.__init__(self)

class ReleaseCivetFirmwareVersion(ReleaseFirmwareVersion, CivetFirmwareVersion):
    def __init__(self, file_path: str = "./images/QAVersions.txt"):
        ReleaseFirmwareVersion.__init__(self, file_path=file_path)

        self.mbrImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}/mbr.hex')
        if not os.path.isfile(self.mbrImagePath):
            raise FileNotFoundError(f'No MBR Release image available '
                                    f'@{self.mbrImagePath}')
        self.appImagePath = (
            f'./images/mcuapp_{str(self.appVersionString)}')
        if not os.path.isdir(self.appImagePath):
            raise IsADirectoryError(f'No MCUAPP Release dir available '
                                    f'@{self.appImagePath}')
        self.appImagePathBankA = (
            f'{self.appImagePath}/civet-a.bin')
        if not os.path.isfile(self.appImagePathBankA):
            raise FileNotFoundError(f'No MCUAPP Release image available '
                                    f'@{self.appImagePathBankA}')
        self.appImagePathBankB = (
            f'{self.appImagePath}/civet-b.bin')
        if not os.path.isfile(self.appImagePathBankB):
            raise FileNotFoundError(f'No MCUAPP Release image available '
                                    f'@{self.appImagePathBankB}')
        self.appImagePathBankAHex = (
            f'{self.appImagePath}/civet-a.hex')
        if not os.path.isfile(self.appImagePathBankAHex):
            raise FileNotFoundError(f'No MCUAPP Release image available '
                                    f'@{self.appImagePathBankAHex}')
        self.appImagePathBankBHex = (
            f'{self.appImagePath}/civet-b.hex')
        if not os.path.isfile(self.appImagePathBankBHex):
            raise FileNotFoundError(f'No MCUAPP Release image available '
                                    f'@{self.appImagePathBankBHex}')
        self.uwbImagePath = (
            f'./images/mcuwb_{str(self.uwbVersionString)}'
            f'/mcuwbCivetAnchor.bin')
        if not os.path.isfile(self.uwbImagePath):
            raise FileNotFoundError(f'No MCUWB Release image available '
                                    f'@{self.uwbImagePath}')
        
        CivetFirmwareVersion.__init__(self)