#!/usr/bin/python3
"""Implements version class for the production test suite

Author: Sportable
Date: 16 Mar 2022

Copyright (c) 2022, Sportable Technologies. All rights reserved.
"""

from typing import Optional
from version import __version__

class BuildVersion:
    NUM_OF_BITS = 8

    def __init__(self) -> None:
        self._version: Optional[list] = None
        self._major: Optional[int] = None
        self._minor: Optional[int] = None
        self._release: Optional[int] = None
        self._patch: Optional[int] = None
        self._uint32Version: Optional[int] = None

        self._version = str(__version__).split(".")
        if self._version:
            try:
                self._major = int(self._version[0])
                self._minor = int(self._version[1])
                self._release = int(self._version[2])
                self._patch = int(self._version[3])
            except ValueError as error:
                raise ValueError(
                    f"Version string conversion failed.\n{error}") from error
        else:
            raise ValueError(f"Wrong version string: {self._version}")
        
        self._uint32Version = self._major
        self._uint32Version = (self._uint32Version << self.NUM_OF_BITS) + self._minor
        self._uint32Version = (self._uint32Version << self.NUM_OF_BITS) + self._release
        self._uint32Version = (self._uint32Version << self.NUM_OF_BITS) + self._patch

    @property
    def uint32Version(self):
        return self._uint32Version
    
    def __str__(self) -> str:
        return (f"Version string: {__version__}\n"
                f"Major: {self._major}\n"
                f"Minor: {self._minor}\n"
                f"Release: {self._release}\n"
                f"Patch: {self._patch}\n"
                f"uint32: {hex(self._uint32Version)}")

if __name__ == "__main__":
    buildVersion = BuildVersion()
    print(buildVersion)