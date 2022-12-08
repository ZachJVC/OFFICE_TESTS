#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TcpConnection.py
  ______              ______                            __  _
 /_  __/________     / ____/___  ____  ____  ___  _____/ /_(_)___  ____
  / / / ___/ __ \   / /   / __ \/ __ \/ __ \/ _ \/ ___/ __/ / __ \/ __ \
 / / / /__/ /_/ /  / /___/ /_/ / / / / / / /  __/ /__/ /_/ / /_/ / / / /
/_/  \___/ .___/   \____/\____/_/ /_/_/ /_/\___/\___/\__/_/\____/_/ /_/
        /_/

@author: sportable
"""
import socket
import select
import time
import json
import numpy as np
from typing import Union

from src.datatypes import TxPower, TcpServerError, ReportDescriptions
from src.datatypes import ErrorModule, ErrorCodes, ReturnCode


class tcpConnection():
    """Manage TCP cpnnection to the daemon"""
    @property
    def tcpIP(self):
        return self._tcpIP
    
    @tcpIP.setter
    def tcpIP(self, tcp_ip: str):
        self._tcpIP = tcp_ip
    
    @property
    def tcpPort(self):
        return self._tcpPort
    
    @tcpPort.setter
    def tcpPort(self, tcp_port: int):
        self._tcpPort = tcp_port
    
    @property
    def maxWait(self):
        return self._maxWait
    
    @maxWait.setter
    def maxWait(self, max_wait: float):
        if max_wait > 0:
            self._maxWait = max_wait

    def __init__(self, tcpIp: str, tcpPort: int, maxWait = 20):
        self._tcpSock = None
        self._tcpIP = tcpIp
        self._tcpPort = tcpPort
        self._maxWait = maxWait
        self.open()

    def frameNumberGenerator(self):
        frameNumber = np.random.randint(0x1, 0xFFFFFFFF)
        return frameNumber

    def daemonInterface(self, 
                        command: str,
                        destination: str,
                        acknowledgement: str,
                        useFrameNum: bool = False) -> dict:
        """Sends commands and returns the response"""
        frame_number = self.frameNumberGenerator() if useFrameNum else 0
        full_command = (f'{{{command},"destination":"{destination}",'
                        f'"frameNumber":{frame_number}}}\n')
        self._tcpSock.send(full_command.encode())
        jsonResponse = self.getResponse(acknowledgement=acknowledgement,
                                        source=destination,
                                        frameNum=frame_number)
        return jsonResponse

    def getResponse(self,
                    acknowledgement: str,
                    source: str,
                    frameNum: int = 0) -> Union[dict,None]:
        """
        Gets a response from the Daemon, submits it to getJsonResponse which
        parses and checks for correct acknowledgement, then returns correct
        json response from daemon
        """
        if acknowledgement is None:
            return
        startTime = time.time()
        while True:
            time.sleep(0.05)
            currentTime = time.time() - startTime
            if currentTime > self._maxWait:
                # We've waited too long for the response
                raise TimeoutError(
                    'Connection timed out - no response from Daemon')
            try:
                ready = select.select([self._tcpSock], [], [], self._maxWait)
                if ready[0]:
                    response = self._tcpSock.recv(1600).decode("utf-8")
                    jsonResponse = self.getJsonResponse(response,
                                                        acknowledgement,
                                                        source,
                                                        frameNum)
                    if not jsonResponse:  # We didn't find correct acknowledgement
                        continue
                    else:  # The acknowledgement was received, return
                        break
                else:  # Not ready, keep waiting
                    continue
            except Exception:
                continue
        return jsonResponse

    def getJsonResponse(self,
                        response: str,
                        acknowledgement: str,
                        source: str,
                        frameNum: int) -> dict:
        """Extracts the JSON response from the response string"""
        # Return empty dict if acknowledgement not in response
        jsonResponse = {}
        for fragment in response.split('\n'):
            if not fragment:
                continue
            if (frameNum and
                not (f'"sourceFrameNumber":{frameNum}' in str(fragment))):
                continue         
            if ((acknowledgement in fragment) and
                (str(source).casefold() in str(fragment).casefold())):
                try:
                    jsonResponse = json.loads(fragment)
                except Exception as error:
                    raise error
                break
        return jsonResponse

    def open(self):
        """ Open a TCP socket """
        if self._tcpSock is not None:
            return
        self._tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcpSock.settimeout(self.maxWait)
        self._tcpSock.connect((self._tcpIP, self._tcpPort))
    
    def close(self):
        """ Close a TCP socket """
        if self._tcpSock is None:
            return
        self._tcpSock.close()
        self._tcpSock = None
    
    def restart(self):
        """ Restart a TCP socket"""
        self.close()
        self.open()

    def lockMemory(self,
                   dest: str,
                   targetMcu: str = "UwbMcu") -> dict:
        """ Locks the non-volatile memory
        
        Params:
            dest: serial number of the device.
            targetMcu: string containing AppMcu or UwbMcu.

        Returns:
            Json response.
        """
        command = f'"lock":{{"section":"NVConfig",'\
                  f'"device":"{str(targetMcu)}","mode":"Lock"}}'     
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneLock',
                                    useFrameNum=True)

    def unlockMemory(self,
                     dest: str,
                     targetMcu: str = "UwbMcu") -> dict:
        """ Unlocks the non-volatile memory
        
        Params:
            dest: serial number of the device.
            targetMcu: string containing AppMcu or UwbMcu.

        Returns:
            Json response.
        """
        command = f'"lock":{{"section":"NVConfig",'\
                  f'"device":"{str(targetMcu)}","mode":"Unlock"}}'
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneLock',
                                    useFrameNum=True)

    def getHardwareVariant(self,
                           dest: str,
                           targetMcu: str = "AppMcu") -> dict:
        """Gets hardvare variant info for selected device using TCP socket.
        
        Params:
            dest: serial number of the device.
            targetMcu: string containing AppMcu or UwbMcu.

        Returns:
            Json reply containing hardware variant data.
        """
        command = f'"getHardwareVariant":"{targetMcu}"'
        return self.daemonInterface(command, dest, 'gotHardwareVariant')

    def setHardwarePcbType(self,
                           dest:str,
                           pcbType: str,
                           targetMcu: str = "AppMcu") -> dict:
        """Sets the pcb type using TCP socket.
        
        Params:
            dest: serial number of the device.
            pcbType: enum containing pcb type.
            targetMcu: string containing AppMcu or UwbMcu.
        
        Return:
            Json response.
        """
        command = f'"setHardwareVariant":{{"pcbType":"{pcbType}",'\
                  f'"device":"{targetMcu}"}}'
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneHardwareVariant',
                                    useFrameNum=True)

    def setHardwarePcbRevision(self,
                               dest: str,
                               pcbRevision: int,
                               targetMcu: str = "AppMcu") -> dict:
        """Sets the pcb revision using TCP socket.
        
        Params:
            dest: serial number of the device.
            pcbRevision: integer containing pcb revision.
            targetMcu: string containing AppMcu or UwbMcu.
        
        Returns:
            Json response.
        """
        command = f'"setHardwareVariant":{{"pcbRevision":{pcbRevision},'\
                  f'"device":"{targetMcu}"}}'
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneHardwareVariant',
                                    useFrameNum=True)

    def setHardwareBomVariant(self,
                              dest: str,
                              bomVariant: str,
                              targetMcu: str = "AppMcu") -> dict:
        """Sets the hardware bom variant using TCP socket.
        
        Params:
            dest: serial number of the device.
            bomVariant: enum containing hardware bom variant.
            targetMcu: string containing AppMcu or UwbMcu.
        
        Returns:
            Json response.
        """
        command = f'"setHardwareVariant":{{"bomVariant":"{bomVariant}",'\
                  f'"device":"{targetMcu}"}}'
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneHardwareVariant',
                                    useFrameNum=True)

    def setHardwareBomRevision(self,
                               dest: str,
                               bomRevision: str,
                               targetMcu: str = "AppMcu") -> dict:
        """Sets the hardware bom revision using TCP socket.
        
        Params:
            dest: serial number of the device.
            bomRevision: enum containing hardware bom revision.
            targetMcu: string containing AppMcu or UwbMcu.
        
        Returns:
            Json response.
        """
        command = f'"setHardwareVariant":{{"bomRevision":"{bomRevision}",'\
                  f'"device":"{targetMcu}"}}'
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneHardwareVariant',
                                    useFrameNum=True)

    def setHardwareAssemblyVariant(self,
                                   dest: str,
                                   assemblyVariant: str,
                                   targetMcu: str = "AppMcu") -> dict:
        """Sets the hardware assembly variant using TCP socket
        
        Params:
            dest: serial number of the device
            assemblyVariant: enum containing hardware assembly variant
            targetMcu: string containing AppMcu or UwbMcu
        
        Returns:
            Json response
        """
        command = f'"setHardwareVariant":{{"assemblyVariant":"{assemblyVariant}",'\
                  f'"device":"{targetMcu}"}}'
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneHardwareVariant',
                                    useFrameNum=True)

    def eraseHardwareVariant(self,
                             dest: str,
                             targetMcu: str = "AppMcu") -> dict:
        """Erases hardware variant information from devices

        Params:
            dest: serial number of the device
            targetMcu: string containing AppMcu or UwbMcu

        Returns:
            JsonResponse
        """
        return self.erase(dest=dest,
                          section="HWVariant",
                          targetMcu=targetMcu)

    def erase(self,
              dest: str,
              section: str,
              targetMcu: str = "AppMcu") -> dict:
        """Erases a given section of memory
        (Needs unlock before erase and lock after)

        Params:
            dest: serial number of the device
            section: string containing specific device's
                     memory section e.g. HWVariant
            targetMcu: string containing AppMcu or UwbMcu

        Returns:
            JsonResponse
        """
        command = f'"erase":{{"section":"{section}","device":"{targetMcu}"}}'
        return self.daemonInterface(command, dest, 'doneErase')

    def disableRssi(self, **kwargs):
        """
        Disables RSSI data from being sent through the network

        Parameters
        ----------
        **kwargs :
            deviceType : anchor / tag
            deviceList : list of anchors / tags

        Returns
        -------
        None.

        """
        deviceList = kwargs['devices']
        deviceType = kwargs['deviceType']

        if deviceType == 'anchor' or deviceType == 'anchors':
            if not deviceList:
                print('No anchors to disable')
                return

            for deviceName in deviceList:
                command = '"setConfigScheme":{"rangingMode":"rangeDataOnly"}'
                jsonResponse = self.daemonInterface(
                    command, deviceName, 'doneConfigScheme')

                if jsonResponse:
                    print(f"Rssi disabled for anchor {deviceName}")
                else:
                    print(f"Rssi NOT DISABLED for anchor {deviceName}")

        elif (deviceType == 'tag') or (deviceType == 'tags'):
            if not deviceList:
                print('No tags to disable')
                return

            for deviceName in deviceList:
                command = '"setConfigUwb":{"rangingMode":"rangeDataOnly"}'
                jsonResponse = self.daemonInterface(
                    command, deviceName, 'doneConfigUwb')
                if jsonResponse:
                    print(f"Rssi disabled for tag {deviceName}")
                else:
                    print(f"Rssi NOT DISABLED for tag {deviceName}")

        return

    def enableRssi(self, **kwargs):
        """
        Enables the RSSI data to be sent through the network

        Parameters
        ----------
        **kwargs :
            deviceType : anchor / tag
            deviceList : list of anchors / tags

        Returns
        -------
        None.

        """

        deviceList = kwargs['devices']
        deviceType = kwargs['deviceType']

        if deviceType == 'anchor' or deviceType == 'anchors':
            if not deviceList:
                print('No anchors to enable')
                return

            for deviceName in deviceList:
                command = '"setConfigScheme":{"rangingMode":"rangeDataRSSI"}'
                jsonResponse = self.daemonInterface(
                    command, deviceName, 'doneConfigScheme')
                if jsonResponse:
                    print(f"Rssi enabled for anchor {deviceName}")
                else:
                    print(f"Rssi NOT ENABLED for anchor {deviceName}")
        elif deviceType == 'tag' or deviceType == 'tags':
            if not deviceList:
                print('No tags to enable')
                return

            for deviceName in deviceList:
                command = '"setConfigUwb":{"rangingMode":"rangeDataRSSI"}'
                jsonResponse = self.daemonInterface(
                    command, deviceName, 'doneConfigUwb')

                if jsonResponse:
                    print(f"Rssi enabled for tag {deviceName}")
                else:
                    print(f"Rssi NOT ENABLED for tag {deviceName}")

        return

    def flashFW(self,
                deviceId: str,
                fwImage: str,
                dest: str = "DM0N00") -> dict:
        """Flashes firmware image using the TCP.
        
        Params:
            deviceId: serial number of the device.
            fwImage: string containing path to the firmware image.
            dest: serial number of the Daemon.

        Returns:
            An object with json response.
        """
        command = f'"setCli":{{"command":"flash","data":"{deviceId} {fwImage}"}}'
        return self.daemonInterface(command, dest, "gotCli")

    def turnOnUwb(self, dest: str) -> dict:
        """Turns off the UwbMcu using the TCP.
        
        Params:
            dest: serial number of the device.

        Returns:
            Json response.
        """
        command = '"changeState":"eUwbOn"'
        return self.daemonInterface(command, dest, "doneChangeState")

    def turnOffUwb(self, dest: str) -> dict:
        """Turns off the UwbMcu using the TCP.
        
        Params:
            dest: serial number of the device.

        Returns:
            Json response.
        """
        command = '"changeState":"eUwbOff"'
        return self.daemonInterface(command, dest, "doneChangeState")

    def turnOff(self, dest: str) -> bool:
        """Turns off the device using the TCP
        
        Params:
            dest: serial number of the device

        Returns:
            Boolean
        """
        command = '"changeState":"eShutdown"'
        self.daemonInterface(command, dest, None)
        return True

    def resetDevice(self, dest: str) -> bool:
        """Resets the device using the TCP
        
        Params:
            dest: serial number of the device

        Returns:
            Boolean
        """
        command='"changeState":"eResetDevice"'
        self.daemonInterface(command, dest, None)
        return True

    def setAsAnchor(self, dest: str) -> dict:
        """Sets the device as an Anchor using TCP
        
        Params:
            dest: serial number of the device

        Returns:
            json response or boolean False
        """
        command = '"setConfigSeat":{"type":"uwbAnchor"}'
        return self.daemonInterface(command, dest, 'doneConfigSeat')

    def runLiveTest(self, dest: str, testName: str) -> bool:
        """Runs the Live Test
        
        Params:
            dest: serial number of the device
            testName: the name of the live test e.g. currentOnlineTest
        Returns:
            Boolean
        """
        command=(f'"runTest":"{testName}"')
        self.daemonInterface(command, dest, None)
        return True

    def getLiveTestValue(self, dest: str) -> dict:
        """Gets the Live Test value
        
        Params:
            dest: serial number of the device

        Returns:
            The return value of the live test
            To get the value parse the json output
            jsonResponse['channelValue']['value']
        """
        return self.getResponse("channelValue",dest)

    def getAllDelays(self, deviceList):
        """
        Get tx and rxDelays for all devices

        Parameters
        ----------
        deviceList : list
            list of the device names in Crockford.

        Returns
        -------
        antennaDelays : np.array([[txDelay1, rxDelay1],[txDelay2, rxDelay2]...[txDelayN, rxDelayN]])

        """
        antennaDelays = np.empty((0, 2))

        for deviceName in deviceList:
            deviceDelays = self.getConfigUwb(deviceName)
            antennaDelays = np.vstack((antennaDelays, deviceDelays))

        return antennaDelays

    def getAllTxPowers(self, deviceList):
        """
        Get tx powers for all devices

        Parameters
        ----------
        deviceList : list
            list of the device names in Crockford.

        Returns
        -------
        txPowers : np.array([[txAvgPower1, txChirpPower1, txDataPower1]...[txAvgPowerN, txChirpPowerN, txDataPowerN]])
        """
        txPowers = np.empty((0, 3))

        for deviceName in deviceList:
            devicePower = self.getTxPower(deviceName)
            txPowers = np.vstack((txPowers, devicePower))

        return txPowers

    def getConfigUwb(self, anchorID):
        """Returns the UWB config which contains the TX and RX delay"""

        command = '"getConfigUwb":1'
        jsonResponse = self.daemonInterface(
            command, anchorID, 'gotConfigUwb')

        print(jsonResponse)
        print('\n\n')
        txDelay = jsonResponse['gotConfigUwb']['txAntennaDelay']
        rxDelay = jsonResponse['gotConfigUwb']['rxAntennaDelay']

        return np.array([txDelay, rxDelay])

    def getPSR(self, dest: str) -> dict:
        """Gets the Packet Success Rate
        
        Params:
            dest: serial number of the device
        
        Returns:
            json response containing PSR
            To get the value parse the json reply
            jsonResponse['liveNetworkMetrics']['psr']
        """
        return self.getResponse("psr",dest)
    
    def getLiveNetworkMetrics(self, dest: str) -> dict:
        """Gets the Packet Success Rate
        
        Params:
            dest: serial number of the device
        
        Returns:
            json response containing PSR
            To get the value parse the json reply
            jsonResponse['liveNetworkMetrics']['psr']
        """
        return self.getResponse("liveNetworkMetrics",dest)

    def getTxPower(self, dest: str) -> dict:
        """
        Returns the TX power from UWB Config

        Parameters
        ----------
        anchorID : string
            Crockford ID.

        Returns
        -------
        txPower : np.array([txAvgPower, txChirpPower, txDataPower])

        """

        command = '"getConfigUwb":1'
        return self.daemonInterface(command, dest, 'gotConfigUwb')

    def getContextDevice(self,
                         dest: str,
                         targetMcu: str = "AppMcu") -> dict:
        """Gets the device context
        
        Params:
            dest: serial number of the device
        
        Returns:
            jsonResponse: a dict containing json response
        """
        command = f'"getContextDevice":"{targetMcu}"'
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement="gotContextDevice")

    def getAppVersion(self, dest: str) -> dict:
        command = '"getVersion":"AppMcu"'
        replyType = 'gotVersion'
        startTime = time.time()
        self._tcpSock.settimeout(0.5)
        try:
            self._tcpSock.recv(1600)
        except:
            pass
        self._tcpSock.settimeout(None)
        while True:
            currentTime = time.time() - startTime
            if currentTime > self._maxWait:
                # We've waited too long for the response
                raise TimeoutError(
                    'Connection timed out - cannot get App version')
            jsonResponse = self.daemonInterface(command, dest, replyType)
            if str(jsonResponse[replyType]['device']) == "AppMcu":
                return jsonResponse[replyType]
            time.sleep(0.5)

    def getUwbVersion(self, dest: str) -> dict:
        command = '"getVersion":"UwbMcu"'
        replyType = 'gotVersion'
        startTime = time.time()
        while True:
            currentTime = time.time() - startTime
            if currentTime > self._maxWait:
                # We've waited too long for the response
                raise TimeoutError(
                    'Connection timed out - cannot get UWB version')
            jsonResponse = self.daemonInterface(command, dest, replyType)
            if str(jsonResponse[replyType]['device']) == "UwbMcu":
                return jsonResponse[replyType]
            time.sleep(0.5)

    def getDaemonVersion(self, dest: str = "DM0N00") -> dict:
        command = '"getVersion":"Daemon"'
        replyType = 'gotVersion'
        startTime = time.time()
        while True:
            currentTime = time.time() - startTime
            if currentTime > self._maxWait:
                # We've waited too long for the response
                raise TimeoutError(
                    'Connection timed out - cannot get Daemon version')
            jsonResponse = self.daemonInterface(command, dest, replyType)
            if str(jsonResponse[replyType]['device']) == "Daemon":
                return jsonResponse[replyType]
            time.sleep(0.5)
    
    def exportSensorData(self, sensor: str, dest: str = "DM0N00") -> None:
        """Exports IMU analyser data.
        
        Params:
            dest: serial number of the Daemon.

        Returns:
            An object with json response.
        """
        command = f'"CLICommand":{{"command":"export","data":"analyzer {sensor} {sensor}.csv"}}'
        self.daemonInterface(command=command,
                             destination=dest,
                             acknowledgement=None)

    def nvSetAllDelaysTo(self, **kwargs):
        """
        Set Rx and Tx delays in non-volatile memory
        """
        txDelay = kwargs['txDelay']
        rxDelay = kwargs['rxDelay']
        devices = kwargs['devices']

        if type(txDelay) == type(rxDelay) == int:
            # Give all the devices the same tx and rx delay
            for deviceName in devices:
                self.nvSetConfigUwb(
                    anchorID=deviceName,
                    txDelay=txDelay,
                    rxDelay=rxDelay)

        elif len(txDelay) == len(rxDelay) == len(devices):
            # Give all the devices distinct delay values
            for j, deviceName in enumerate(devices):
                self.nvSetConfigUwb(
                    anchorID=deviceName,
                    txDelay=txDelay[j],
                    rxDelay=rxDelay[j])
        return

    def nvSetConfigUwb(self, **kwargs):
        """
        Writes the TX and RX antenna delay paremeters into non-volatile memory
        """
        anchorID = kwargs['anchorID']
        txDelay = kwargs['txDelay']
        rxDelay = kwargs['rxDelay']

        command = f'"nvSetConfigUwb":{{"txAntennaDelay":{txDelay},'\
                  f'"rxAntennaDelay":{rxDelay}}}'

        nvWriteAttemptCounter = 0
        nvWriteAttemptMaxTries = 5

        while nvWriteAttemptCounter <= nvWriteAttemptMaxTries:
            try:
                unlockBool = self.unlockMemory(anchorID)
                jsonResponse = self.daemonInterface(
                    command, anchorID, 'doneConfigUwb')
                lockBool = self.lockMemory(anchorID)
                if unlockBool and lockBool and len(jsonResponse) != 0:
                    print(
                        f"Successfully wrote nonvolatile delays for {anchorID}")
                    break
            except Exception:
                nvWriteAttemptCounter += 1
        else:
            raise TcpServerError(f"Failed to write nonvolatile "
                                 f"settings for the device {anchorID}")
        return

    def setAllDelaysTo(self, **kwargs):
        """
        Method to set same Tx and Rx delays on all devices
        """
        txDelay = kwargs['txDelay']
        rxDelay = kwargs['rxDelay']
        devices = kwargs['devices']

        if type(txDelay) == type(rxDelay) == int:
            # Give all the devices the same tx and rx delay
            for deviceName in devices:
                self.setConfigUwb(
                    anchorID=deviceName,
                    txDelay=txDelay,
                    rxDelay=rxDelay)
        elif len(txDelay) == len(rxDelay) == len(devices):
            # Give all the devices distinct delay values
            for j, deviceName in enumerate(devices):
                self.setConfigUwb(
                    anchorID=deviceName,
                    txDelay=txDelay[j],
                    rxDelay=rxDelay[j])
        return

    def setAllTxPowersTo(self, **kwargs):
        """
        Method to set same tx power on all devices
        """
        txPower = kwargs['txPower']
        devices = kwargs['devices']

        if isinstance(txPower, (int, np.integer)):
            # Give all the devices the same SINGLE tx power setting
            for deviceName in devices:
                self.setTxPower(anchorID=deviceName, txPower=np.array(
                    [txPower, txPower, txPower]))
        elif txPower.shape[0] == 1 and len(devices) != 1:
            # Give all the devices the same tx power settings
            for deviceName in devices:
                self.setTxPower(anchorID=deviceName, txPower=txPower)
        elif txPower.shape[0] == len(devices):
            # Give all the devices distinct txPowers
            for j, deviceName in enumerate(devices):
                self.setTxPower(anchorID=deviceName, txPower=txPower[j, :])
        else:
            raise ValueError('The shape of txPower does not '
                             'correspond with the number of devices')
        return

    def setConfigUwb(self, **kwargs) -> dict:
        """
        Writes the TX and RX delay paremeters into volatile memory
        """
        anchorID = kwargs['anchorID']
        txDelay = kwargs['txDelay']
        rxDelay = kwargs['rxDelay']

        command = f'"setConfigUwb":{{"txAntennaDelay":{txDelay},'\
                  f'"rxAntennaDelay":{rxDelay}}}'
        return self.daemonInterface(command=command,
                                    destination=anchorID,
                                    acknowledgement='doneConfigUwb')

    def setTxPower(self, **kwargs) -> dict:
        """
        Writes the TX Power into volatile memory
        """
        anchorID = kwargs['anchorID']
        txPower: TxPower = kwargs['txPower']

        command = (f'"setConfigUwb":{{"txAveragePower":{txPower.txAvgPower},'
                   f'"txChirpPower":{txPower.txChirpPower},'
                   f'"txDataPower":{txPower.txDataPower}}}')
        return self.daemonInterface(command=command,
                                    destination=anchorID,
                                    acknowledgement='doneConfigUwb')
    def bypassLNA(self, dest: str) -> dict:
        """ Bypasses LNA.

        Params:
            dest: serial number of the device.
        
        Returns:
            An object containing json response.
        """
        command = (f'"setConfigUwb":{{"mode":37}}')
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneConfigUwb')
                                    
    def restoreLNA(self, dest: str) -> dict:
        """ Restores LNA.

        Params:
            dest: serial number of the device.
        
        Returns:
            An object containing json response.
        """
        command = (f'"setConfigUwb":{{"mode":5}}')
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement='doneConfigUwb')
    
    def sendErrorReport(self,
                        dest: str,
                        code: ErrorCodes,
                        description: ReportDescriptions,
                        instanceNum: int,
                        line: int,
                        module: ErrorModule,
                        version: int,
                        returnCode: ReturnCode) -> dict:
        """Sends live error report.
        
        Params:
            dest: serial number of the device.
            code: code to representing top level error.
            description: error description.
            instanceNum: instance number of the production test.
            line: line number where the error originated.
            module: live error report module.
            version: production test version number in uint32 format.
            returnCode: return code generated when the error occured.
        
        Returns:
            An object containing json response.
        """
        command = (f'"liveErrorReport":{{"code":"{code}",'
                   f'"description":"{description}",'
                   f'"instanceNum":{instanceNum},'
                   f'"line":{line},'
                   f'"module":"{module}",'
                   f'"version":{version},'
                   f'"returnCode":{{"code":"{returnCode.code}",'
                   f'"layer":"{returnCode.layer}",'
                   f'"line":{returnCode.line}}}}}')
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement=None)

    def sendUserMessage(self,
                        dest: str,
                        info: str) -> dict:
        """Sends live user messages.
        
        Params:
            dest: serial number of the device.
            info: message limited to 127 bytes.
        
        Returns:
            An object containing json response.
        """
        command = (f'"liveUserMessage":{{"info":"{info}"}}')
        return self.daemonInterface(command=command,
                                    destination=dest,
                                    acknowledgement=None)