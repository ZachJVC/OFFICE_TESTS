""" Version classes definition

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import re

from typing import Optional, Any
from dataclasses import dataclass
from ctypes import c_uint32 as uint32_t

from src.datatypes import FirmwareType

class Version:
    INTERNAL_RELEASE_BIT: int = 31
    DIRTY_BUILD_BIT: int = 7
    VERSION_MAJOR: int = 24
    VERSION_MINOR: int = 16
    VERSION_RELEASE: int = 8
    VERSION_PATCH: int = 0
    def __init__(self, version: str) -> None:
        if not version:
            raise ValueError("Empty version string")
        self.versionStr = version.replace('_', '.')
        self.fullVersionInt = self.toFullVersionInt(self.versionStr)
        self.firmwareType = self.findType(self.fullVersionInt)
        self.versionDirty = self.isDirty(self.fullVersionInt)
        self.versionInt = self.toTrueVersionInt(self.fullVersionInt)

    @property
    def versionStr(self) -> str:
        return self._versionStr
    
    @versionStr.setter
    def versionStr(self, version: str) -> None:
        self._versionStr = version

    @property
    def versionInt(self) -> int:
        return self._versionInt
    
    @versionInt.setter
    def versionInt(self, version: int) -> None:
        self._versionInt = version
    
    @property
    def fullVersionInt(self) -> int:
        return self._fullVersionInt
    
    @fullVersionInt.setter
    def fullVersionInt(self, version: int) -> None:
        self._fullVersionInt = version
    
    @property
    def firmwareType(self) -> FirmwareType:
        return self._firmwareType
    
    @firmwareType.setter
    def firmwareType(self, fwType: FirmwareType) -> None:
        self._firmwareType = fwType
    
    @property
    def versionDirty(self) -> bool:
        return self._versionDirty
    
    @versionDirty.setter
    def versionDirty(self, isDirty: bool) -> None:
        self._versionDirty = isDirty

    def isDirty(self, fullVersionInt: int) -> bool:
        return (True if (fullVersionInt & (0x1 << Version.DIRTY_BUILD_BIT))
                     else False)
    
    def toTrueVersionInt(self, versionInt: int) -> int:
        return (versionInt & uint32_t(~((0x1 << Version.INTERNAL_RELEASE_BIT) |
                                        (0x1 << Version.DIRTY_BUILD_BIT))).value)
    
    def toFullVersionInt(self, versionStr: str) -> int:
        versionRegex = re.search("([0-9]+).([0-9]).([0-9]).([0-9]+)", versionStr)
        if not versionRegex:
            raise ValueError("Version string in wrong format")
        return (int(versionRegex.group(1)) << Version.VERSION_MAJOR |
                int(versionRegex.group(2)) << Version.VERSION_MINOR |
                int(versionRegex.group(3)) << Version.VERSION_RELEASE |
                int(versionRegex.group(4)) << Version.VERSION_PATCH)
    
    def findType(self, fullVersionInt: int) -> FirmwareType:
        return (FirmwareType.INTERNAL if (fullVersionInt & (0x1 << Version.INTERNAL_RELEASE_BIT))
                                      else FirmwareType.RELEASE)
    
    def isExactMatch(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"Wrong type {type(other)}")
        return self.fullVersionInt == other.fullVersionInt
    
    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"Wrong type {type(other)}")
        return self.versionInt < other.versionInt
    
    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"Wrong type {type(other)}")
        return self.versionInt <= other.versionInt
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"Wrong type {type(other)}")
        return self.versionInt == other.versionInt
    
    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"Wrong type {type(other)}")
        return self.versionInt != other.versionInt
    
    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"Wrong type {type(other)}")
        return self.versionInt > other.versionInt
    
    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"Wrong type {type(other)}")
        return self.versionInt >= other.versionInt
    
    def __str__(self) -> str:
        return self.versionStr

@dataclass
class Versions:
    appMcuVersion: Version
    uwbMcuVersion: Version
    daemonVersion: Optional[Version] = None
    hwVersion: Optional[int] = None