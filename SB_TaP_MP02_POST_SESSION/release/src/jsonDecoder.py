#!/usr/bin/env python3

def decodeVersionString(versionPacket):
    major = versionPacket["firmware"]["major"]
    minor = versionPacket["firmware"]["minor"]
    release = versionPacket["firmware"]["release"]
    patch = versionPacket["firmware"]["patch"]
    return f'v{major}.{minor}.{release}.{patch}'

def decodeHardwareVersionString(versionPacket):
    return versionPacket["hardware"]["revision"]