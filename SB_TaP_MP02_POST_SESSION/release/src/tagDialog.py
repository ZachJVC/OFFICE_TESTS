"""Handles communication with Daemon via file pipes or via aeolus script.

Author: Christos Bontozoglou
Date: 22 Aug 2019

Copyright (c) 2019, Sportable Technologies. All rights reserved.

"""
import os
import time
import src.prettyPrint as pretty

filePath = "./tagRep"
attachedTags = "./attachedTags.csv"
noReply = "NO REPLY"

maxRetries = 3

commandTimeouts = {
    "reset": 5,
    "offload": 200,
    "flashfw": 120,
    "charger": 10,
    "format": 60,
    "start": 20,
    "stop": 20,
    "setid": 40,
    "getdev": 30,
    "shutdown":10
}

def initPipes():
    """Clears file pipes.

    """
    with open(filePath, 'w'):
        pass
    with open(attachedTags, 'w'):
        pass

def waitConnection(tagId = "0", timeout = 60):
    """Waits until a tag is attached and connected to the Daemon, or times-out.

    Parameters
    ----------
    tagId : str
        Tag ID in string format. if 0", wait for any connection.
    timeout : int
        Maximum waiting time for the connection message

    Returns
    -------
    boolean
        True when tag connection is detected, otherwise false.

    """
    interval = 0.2
    steps = int(timeout / interval)
    for step in range(0,steps):
        with open(filePath, 'r') as file:
            text = file.readline()
        if tagId == "0" or tagId in text:
            if ":CONNECTED" in text:
                return True
        time.sleep(interval)
    raise IOError("Tag "+str(tagId)+" not connected over USB")
    return False

def waitConnectionUsingAttachedTags(tagId="0",timeout=60):
    """Waits until a tag is attached and connected to the Daemon, or times-out.

    Parameters
    ----------
    tagId : str
        Tag ID in string format. if 0", wait for any connection.
    timeout : int
        Maximum waiting time for the connection message

    Returns
    -------
    boolean
        True when tag connection is detected, otherwise false.

    """
    
    interval = 0.2
    steps = int(timeout / interval)
    for step in range(0, steps):
        with open(attachedTags, 'r') as file:
            lines = file.readlines()
        for line in lines:
            fields = line.split(",")
            if tagId == "0" or tagId in fields[0].strip():
                return True
        time.sleep(interval)
    return False


def waitDisconnection(tagId = "0", timeout = 60):
    """Waits until a tag is detached and disconnected by the Daemon, or times-out.

    Parameters
    ----------
    tagId : str
        Tag ID in string format. if 0", wait for any connection.
    timeout : int
        Maximum waiting time for the disconnetion message

    Returns
    -------
    boolean
        True when tag disconnetion is detected, otherwise false.

    """
    interval = 0.2
    steps = int(timeout / interval)
    for step in range(0,steps):
        with open(filePath, 'r') as file:
            text = file.readline()
        if tagId == "0" or tagId in text:
            if ":DISCONNECTED" in text:
                return True
        time.sleep(interval)
    raise IOError("Tag "+str(tagId)+" not disconnected from USB")
    return False

def waitOK(tagId = "0", timeout = 20):
    """Waits until a reply from the tag is received, or times-out.

    Parameters
    ----------
    tagId : str
        Tag ID in string format. if 0", wait for any connection.
    timeout : int
        Maximum waiting time for the connection message

    Returns
    -------
    boolean
        True when positive reply is received (OK), otherwise False

    str
        The actual reply message

    """
    interval = 0.2
    steps = int(timeout / interval)
    for step in range(0,steps):
        with open(filePath, 'r') as file:
            text = file.readline()
        if tagId == "0" or tagId in text:
            if ":OK" in text:
                return True, text
            if ":KO" in text:
                # raise IOError("Command failed")
                return False, text
        time.sleep(interval)
    return False, noReply

def getTimeoutForCommand(cmd):
    if cmd in commandTimeouts:
        timeout = commandTimeouts.get(cmd)
    else:
        timeout = 5
    return timeout

def cmdWithHandshake(tagId = "0", cmd = "reset", data = 0, stringData = "0"):
    cmdLine = "sudo ./aeolus.py" + " --tag " + str(tagId) + " --data " + str(data) + " --string " + str(stringData) + " " + str(cmd)
    os.system(cmdLine)
    time.sleep(1)
    ret = True
    msg = noReply
    if cmd != "reset":
        timeout = getTimeoutForCommand(cmd)
        ret, msg = waitOK(tagId, timeout)
        if msg == noReply:
            raise IOError("Failed to get reply from tag")
    else:
        time.sleep(15)
        return True, "OK"
    return ret, msg

def cmdSafeSend(tagId = "0", cmd = "reset", data = 0, stringData = "0"):
    retries = 0
    while True:
        try:
            ret, msg = cmdWithHandshake(tagId, cmd, data, stringData)
            if ret == True and ("OK" in msg):
                break
        except IOError:
            retries = retries + 1
            pretty.printError('Command ['+str(cmd)+'] failed, trying again (Retry: '+str(retries)+')... ')
        if(retries > maxRetries):
            pretty.printError("TEST FAILED: TIMEOUT")
            raise Exception("Test failed due to "+str(cmd)+" command timeout!")
