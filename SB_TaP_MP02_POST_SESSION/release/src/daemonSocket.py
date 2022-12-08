#!/usr/bin/env python3
""" Daemon Socket Interface

Copyright (c) 2022, Sportable Technologies. All rights reserved.

"""

import time
import src.networkedProductionTest.TcpConnection as TcpConnection
import src.networkedProductionTest.UdpConnection as UdpConnection
import src.jsonDecoder as json
import src.datatypes as dt

from src.versions import Version, Versions

class DaemonSocket:
    IP_ADDRESS = '127.0.0.1'
    SEND_COMMAND_DELAY = 0.5     # Delay in seconds
    
    def __init__(self) -> None:
        self._connection = None
        self._port = None
        self._timeout = None
    
    def openConnection(self):
        pass
    
    def closeConnection(self):
        self._connection.close()
    
    def restartConnection(self):
        self._connection.restart()

class DaemonTcpSocket(DaemonSocket):
    def __init__(self, tcpPort: int, timeout: float = 20) -> None:
        super().__init__()
        self._port = tcpPort
        self._timeout = timeout
        self.openConnection()

    def openConnection(self):
        self._connection = TcpConnection.tcpConnection(tcpIp=DaemonSocket.IP_ADDRESS,
                                                       tcpPort=self._port,
                                                       maxWait=self._timeout)

class DaemonUdpSocket(DaemonSocket):
    def __init__(self, udpPort: int, timeout: float = 20) -> None:
        super().__init__()
        self._port = udpPort
        self._timeout = timeout
        self.openConnection()

    def openConnection(self):
        self._connection = UdpConnection.udpConnection(udpIp=DaemonSocket.IP_ADDRESS,
                                                       udpPort=self._port,
                                                       maxWait=self._timeout)

class FirmwareFlashClient(DaemonTcpSocket):
    DUT_TCP_SOCKET = 8693

    def __init__(self,
                 tcpPort: int = DUT_TCP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(tcpPort=tcpPort, timeout=timeout)
    
    def flashFW(self,
                deviceId: str,
                fwImage: str,
                device: str = "Uwb"):
        """Flashes UWB image using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.
            fwImage: string containing path to the firmware image.
            device: string containing App or Uwb.

        Returns:
            None.

        Raises:
            MemoryError: If flashing process failed.
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            jsonResponse = self._connection.flashFW(
                deviceId, str(fwImage), "DM0N00")
        except Exception as ex:
            raise dt.TcpServerError(f'Failed to upload {device} '
                                    f'image to the device.\n{ex}') from ex
        reply = str(jsonResponse['gotCli']['data']).split('@')
        if str(reply[0]) != "Success":
            raise dt.FlashingImageError(
                f'Failed to upload {device} image to the device {deviceId}.')
        else:
            print(f'Upload {device} image successful.')

class ErrorReportClient(DaemonTcpSocket):
    DUT_TCP_SOCKET = 8690

    def __init__(self,
                 tcpPort: int = DUT_TCP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(tcpPort=tcpPort, timeout=timeout)
    
    def reportError(self,
                    deviceId: str,
                    code: dt.ErrorCodes,
                    description: dt.ReportDescriptions,
                    instanceNum: int,
                    line: int,
                    module: dt.ErrorModule,
                    version: int,
                    returnCode: dt.ReturnCode) -> dict:
        """Sends error report.
        
        Params:
            deviceId: string containing serial number of the device.
            code: code to representing top level error.
            description: error description.
            instanceNum: instance number of the production test.
            line: line number where the error originated.
            module: live error report module.
            version: production test version number in uint32 format.
            returnCode: return code generated when the error occured.

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            jsonResponse = self._connection.sendErrorReport(dest=deviceId,
                                                            code=code,
                                                            description=description,
                                                            instanceNum=instanceNum,
                                                            line=line,
                                                            module=module,
                                                            version=version,
                                                            returnCode=returnCode)
        except Exception as ex:
            raise dt.TcpServerError(f'Failed to send error report.\n{ex}') from ex
        return jsonResponse

    def sendUserMessage(self,
                        deviceId: str,
                        info: str) -> dict:
        """Sends live user messages.
        
        Params:
            dest: serial number of the device.
            info: message limited to 127 bytes.
        
        Returns:
            An object containing json response.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            jsonResponse = self._connection.sendUserMessage(dest=deviceId,
                                                            info=info)
        except Exception as ex:
            raise dt.TcpServerError(f'Failed to send user message.\n{ex}') from ex
        return jsonResponse

class ControlClient(DaemonTcpSocket):
    DUT_TCP_SOCKET = 8694

    def __init__(self,
                 tcpPort: int = DUT_TCP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(tcpPort=tcpPort, timeout=timeout)
           
    def getHardwareVersion(self, deviceId: str) -> int:
        """Gets hardware version using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            An integer containing hardware version.

        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            appVersion = self._connection.getAppVersion(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve hardware version.\n{ex}') from ex
        return int(json.decodeHardwareVersionString(appVersion))
    
    def getVersions(self, deviceId: str) -> Versions:
        """Gets App, MCU and hardware versions using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            A Versions object containing the App version number,  the UWB version number
            and the hardware version number.

        Raises:
            ConnectionError: if sending the command failed.
        """
        try:
            time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
            appVersion = self._connection.getAppVersion(deviceId)
            time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
            uwbVersion = self._connection.getUwbVersion(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve firmware versions.\n{ex}') from ex
        appVersionString = json.decodeVersionString(appVersion)
        uwbVersionString = json.decodeVersionString(uwbVersion)
        hardwareVersionString = json.decodeHardwareVersionString(appVersion)
        return Versions(appMcuVersion=Version(str(appVersionString)),
                        uwbMcuVersion= Version(str(uwbVersionString)),
                        hwVersion=int(hardwareVersionString))

    def getUwbVersionAllFields(self, deviceId: str) -> dict:
        """Gets the UWB version json response using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            uwbVersion: an object containing json response.

        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            uwbVersion = self._connection.getUwbVersion(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(f'Failed to retrieve Uwb firmware '
                                    f'version in json format.\n{ex}') from ex
        return uwbVersion

    def getAppVersionAllFields(self, deviceId: str) -> dict:
        """Gets the App version json response using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            appVersion = self._connection.getAppVersion(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(f'Failed to retrieve App firmware '
                                    f'version in json format.\n{ex}') from ex
        return appVersion

    def getUwbVersion(self, deviceId: str) -> str:
        """Gets the UWB version number using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            String containing the UWB version number.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            uwbVersion = self._connection.getUwbVersion(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve Uwb firmware version.\n{ex}') from ex
        uwbVersionString = json.decodeVersionString(uwbVersion)
        return str(uwbVersionString)

    def getAppVersion(self, deviceId: str) -> str:
        """Gets the App version number using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            String containing the App version number.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            appVersion = self._connection.getAppVersion(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve App firmware version.\n{ex}') from ex
        appVersionString = json.decodeVersionString(appVersion)
        return str(appVersionString)

    def getInternalAppVersion(self, deviceId: str) -> str:
        """Gets the internal App version using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            String containing the App version after conversion from internal version number.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        versionPacket = self.getAppVersionAllFields(deviceId=deviceId)
        major = versionPacket["firmware"]["major"]
        major = major - 128
        minor = versionPacket["firmware"]["minor"]
        release = versionPacket["firmware"]["release"]
        patch = versionPacket["firmware"]["patch"]   
        return str(f'{major}.{minor}.{release}.{patch}')

    def getDaemonVersion(self) -> Version:
        """Gets the Daemon version number using the TCP protocol.
        
        Params:
            tcpConnection: an object of TcpConnection type.
            socketNumber: a number of a socket to connect to if
                          tcpConnection is None.
            closeConnection: boolean to determine should the connection
                             be closed after sending the command.

        Returns:
            String containing the Daemon version number.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            daemonVersion = self._connection.getDaemonVersion()
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve Daemon firmware version.\n{ex}') from ex
        daemonVersionString = json.decodeVersionString(daemonVersion)
        return Version(str(daemonVersionString))
    
    def exportImuData(self) -> None:
        """Exports IMU analyser data.
        
        Params:
            None.

        Returns:
            None.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.exportSensorData(sensor="IMU")
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to export IMU analyser data.\n{ex}') from ex
    
    def exportPsrData(self) -> None:
        """Exports PSR analyser data.
        
        Params:
            None.

        Returns:
            None.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.exportSensorData(sensor="psrData")
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to export PSR analyser data.\n{ex}') from ex

    def formatDevice(self, deviceId: str) -> dict:
        """Erases all section on the device.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        print("Formatting the device ...")
        try:
            self._connection.unlockMemory(deviceId, "AppMcu")
            retVal = self._connection.erase(deviceId, "All", "AppMcu")      
            self._connection.lockMemory(deviceId, "AppMcu")
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to format the device.\n{ex}') from ex
        return retVal
    
    def bypassLNA(self, dest: str):
        """ Bypasses LNA.

        Params:
            dest: serial number of the device.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.bypassLNA(dest=dest)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to bypass LNA.\n{ex}') from ex

    def restoreLNA(self, dest: str):
        """ Restores LNA.

        Params:
            dest: serial number of the device.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.restoreLNA(dest=dest)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to restore LNA.\n{ex}') from ex

    def getTxPower(self, deviceId: str) -> dt.TxPower:
        """Gets Tx power values using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            txAvgPower: integer containing the Tx average power value.
            txChirpPower: integer containing the Tx chirp power value.
            txDataPower: integer containing the Tx data power value.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            jsonResponse = self._connection.getTxPower(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(f'Failed to retrieve the Tx power '
                                    f'of the device.\n{ex}') from ex
        txPower = dt.TxPower()
        txPower.txAvgPower = jsonResponse['gotConfigUwb']['txAveragePower']
        txPower.txChirpPower = jsonResponse['gotConfigUwb']['txChirpPower']
        txPower.txDataPower = jsonResponse['gotConfigUwb']['txDataPower']
        return txPower
    
    def setTxPower(self, deviceId: str, level: int):
        """Sets the Tx power level using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.
            level: integer containing the desired Tx power level.

        Returns:
            None.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        txPower = dt.TxPower(level, level, level)
        try:
            self._connection.setTxPower(anchorID=deviceId, txPower=txPower)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to set the Tx power of the device.\n{ex}') from ex

    def setMinTxPower(self, deviceId: str):
        """Sets the minimum Tx power level using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            None.

        Raises:
            ConnectionError: if sending the command failed.
        """
        minPower = 1
        self.setTxPower(deviceId=deviceId, level=minPower)

    def setDefaultTxPower(self, deviceId: str):
        """Sets the default Tx power level usign the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            None.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        defaultPower = 68
        self.setTxPower(deviceId=deviceId, level=defaultPower)

    def getHardwareVariant(self,
                           deviceId: str,
                           device: str) -> dt.HardwareVariant:
        """Gets the hardware variant usign the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.
            device: string containing AppMcu or UwbMcu.

        Returns:
            hardwareVariant object:
                pcbType: string containing hardware type.
                pcbRevision: integer containing pcb revision.
                bomVariant: string containing hardware bom variant.
                bomRevision: string containing hardware bom revision.
                assemblyVariant: string containing hardware assembly variant.

        Raises:
            ConnectionError: If hardware variant cannot be retrieved.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            hardwareVariant = self._connection.getHardwareVariant(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve hardware variant.\n{ex}') from ex
        hVar = dt.HardwareVariant()
        hVar.pcbType = hardwareVariant['gotHardwareVariant']['pcbType']
        hVar.pcbRevision = hardwareVariant['gotHardwareVariant']['pcbRevision']
        hVar.bomVariant = hardwareVariant['gotHardwareVariant']['bomVariant']
        hVar.bomRevision = hardwareVariant['gotHardwareVariant']['bomRevision']
        hVar.assemblyVariant = hardwareVariant['gotHardwareVariant']['assemblyVariant']
        return hVar
    
    def eraseHardwareVariant(self,
                             deviceId: str,
                             device: str = "AppMcu") -> dict:
        """Erases Hardware Variant section on the device.
        
        Params:
            deviceId: string containing serial number of the device.
            device: string containing AppMcu or UwbMcu.

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            retVal = self._connection.erase(deviceId, "HWVariant", device)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to erase Hardware Variant.\n{ex}') from ex
        return retVal

    def setHardwareVariant(self,
                           deviceId: str,
                           hw_variant: dt.HardwareVariant,
                           device: str,
                           setAssemblyVar: bool = False) -> dict:
        """Sets the hardware variant usign the TCP protocol.
        
        Params:
            deviceId: serial number of the device.
            hw_variant: HardwareVariant object
            device: string containing AppMcu or UwbMcu.
            setAssemblyVar: boolean to determine should the Assembly Variant
                            be programmed

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: If any of commands fails.
        """
        _HW_VAR_DELAY = 0.5
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        self._connection.unlockMemory(deviceId, device)
        # Set PcbType
        time.sleep(_HW_VAR_DELAY)
        print("Programming Pcb Type ...")
        self.setHardwarePcbType(deviceId=deviceId,
                                pcbType=hw_variant.pcbType,
                                device=device,
                                unlock=False)
        # Set PcbRevision
        time.sleep(_HW_VAR_DELAY)
        print("Programming Pcb Revision ...")
        self.setHardwarePcbRevision(deviceId=deviceId,
                                    pcbRevision=hw_variant.pcbRevision,
                                    device=device,
                                    unlock=False)
        # Set BomVariant
        time.sleep(_HW_VAR_DELAY)
        print("Programming BOM Variant ...") 
        self.setHardwareBomVariant(deviceId=deviceId,
                                    bomVariant=hw_variant.bomVariant,
                                    device=device,
                                    unlock=False)
        # Set BomRevision
        time.sleep(_HW_VAR_DELAY)
        print("Programming BOM Revision ...")
        self.setHardwareBomRevision(deviceId=deviceId,
                                    bomRevision=hw_variant.bomRevision,
                                    device=device,
                                    unlock=False)
        if setAssemblyVar:
            # Set BomRevision
            time.sleep(_HW_VAR_DELAY)
            print("Programming Assembly Variant ...")
            self.setHardwareAssemblyVariant(deviceId=deviceId,
                                            assemblyVariant=hw_variant.assemblyVariant,
                                            device=device,
                                            unlock=False)
        time.sleep(_HW_VAR_DELAY)
        self._connection.lockMemory(deviceId, device)

    def setHardwarePcbType(self,
                           deviceId: str,
                           pcbType: str,
                           device: str,
                           unlock: bool = True) -> dict:
        """Sets the pcb type usign the TCP protocol.
        
        Params:
            dest: serial number of the device.
            pcbType: string containing pcb type.
            device: string containing AppMcu or UwbMcu.
            unlock: determines should the unlock and lock command be
                    issued

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: If the command fails.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            if unlock:
                self._connection.unlockMemory(deviceId, device)
            retVal = self._connection.setHardwarePcbType(deviceId, pcbType, device)
            if unlock:
                self._connection.lockMemory(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Programming Pcb Type to {device} failed.\n{ex}') from ex
        return retVal

    def setHardwarePcbRevision(self,
                               deviceId: str,
                               pcbRevision: int,
                               device: str,
                               unlock: bool = True) -> dict:
        """Sets the pcb revision usign the TCP protocol.
        
        Params:
            dest: serial number of the device.
            pcbRevision: string containing pcb revision.
            device: string containing AppMcu or UwbMcu.
            unlock: determines should the unlock and lock command be
                    issued

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: If the command fails.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            if unlock:
                self._connection.unlockMemory(deviceId, device)
            retVal = self._connection.setHardwarePcbRevision(deviceId, pcbRevision, device)
            if unlock:
                self._connection.lockMemory(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Programming Pcb Revision to {device} failed.\n{ex}') from ex
        return retVal

    def setHardwareBomVariant(self,
                              deviceId: str,
                              bomVariant: str,
                              device: str,
                              unlock: bool = True) -> dict:
        """Sets the hardware bom variat usign the TCP protocol.
        
        Params:
            dest: serial number of the device.
            bomVariant: string containing hardware bom variant.
            device: string containing AppMcu or UwbMcu.
            unlock: determines should the unlock and lock command be
                    issued

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: If the command fails.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            if unlock:
                self._connection.unlockMemory(deviceId, device)
            retVal = self._connection.setHardwareBomVariant(deviceId, bomVariant, device)
            if unlock:
                self._connection.lockMemory(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(f'Programming Hardware Bom Variant '
                                    f'to {device} failed.\n{ex}') from ex
        return retVal

    def setHardwareBomRevision(self,
                               deviceId: str,
                               bomRevision: str,
                               device: str,
                               unlock: bool = True) -> dict:
        """Sets the hardware bom revision usign the TCP protocol.
        
        Params:
            dest: serial number of the device.
            bomRevision: string containing hardware bom revision.
            device: string containing AppMcu or UwbMcu.
            unlock: determines should the unlock and lock command be
                    issued

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: If the command returns False.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            if unlock:
                self._connection.unlockMemory(deviceId, device)
            retVal = self._connection.setHardwareBomRevision(deviceId, bomRevision, device)
            if unlock:
                self._connection.lockMemory(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(f'Programming Hardware Bom Revision '
                                    f'to {device} failed.\n{ex}') from ex
        return retVal

    def setHardwareAssemblyVariant(self,
                                   deviceId: str,
                                   assemblyVariant:str,
                                   device: str,
                                   unlock: bool = True) -> dict:
        """Sets the hardware assembly variat usign the TCP protocol.
        
        Params:
            deviceId: serial number of the device.
            assemblyVariant: string containing hardware assembly variant.
            device: string containing AppMcu or UwbMcu.
            unlock: determines should the unlock and lock command be
                    issued

        Returns:
            An object containing json response.

        Raises:
            ConnectionError: If the command fails.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            if unlock:
                self._connection.unlockMemory(deviceId, device)
            retVal = self._connection.setHardwareAssemblyVariant(deviceId, assemblyVariant)
            if unlock:
                self._connection.lockMemory(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(f'Programming Hardware Assembly Variant '
                                    f'to {device} failed.\n{ex}') from ex
        return retVal

    def turnOnUwb(self, deviceId: str):
        """Turns on the UWB using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            None.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.turnOnUwb(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to turn on the Uwb.\n{ex}') from ex
    
    def turnOffUwb(self, deviceId: str):
        """Turns off the UWB using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            None.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.turnOffUwb(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to turn off the Uwb.\n{ex}') from ex

    def turnOff(self, deviceId: str):
        """Turns off the DUT using the TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            None.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.turnOff(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to turn off the device.\n{ex}') from ex

    def resetDevice(self, deviceId: str):
        """Resets the DUT using the TCP protocol.
        
        Param:
            deviceId: string containing serial number of the device.

        Return:
            None.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.resetDevice(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to reset the device.\n{ex}') from ex

    def setAsAnchor(self, deviceId: str) -> dict:
        """Sets the DUT as an Anchor using the TCP protocol.

        Params:
            deviceId: string containing serial number of the device.

        Returns:
            None.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.setAsAnchor(deviceId)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to set the device as an anchor.\n{ex}') from ex
    
    def getHardwareID(self,
                      deviceId: str,
                      device: str = "AppMcu") -> str:
        """Gets the hardware ID usign the device context.
        
        Params:
            deviceId: string containing serial number of the device.
            device: string containing AppMcu or UwbMcu.

        Returns:
            hardwareID: string containing the device hardware ID
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            deviceContext = self._connection.getContextDevice(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve the context device.\n{ex}') from ex
        hardwareID = deviceContext["gotContextDevice"]["hardwareID"]
        return str(hardwareID[2:]).lower()
    
    def getRtcRatio(self,
                    deviceId: str,
                    device: str = "AppMcu") -> float:
        """Gets the Real Time Clock ratio usign the device context.
        
        Params:
            deviceId: string containing serial number of the device.
            device: string containing AppMcu or UwbMcu.

        Returns:
            RTC Ratio: float containing the RTC ratio.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            deviceContext = self._connection.getContextDevice(deviceId, device)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to retrieve the context device.\n{ex}') from ex
        rtcRatio = deviceContext["gotContextDevice"]["clocks"]['mainToRtc']
        return float(rtcRatio)
    
    def runLiveTest(self, deviceId: str, testName: str):
        """Runs the live test on the DUT.
            
        Params:
            deviceId: serial number of the device.
            testName: the name of the live test e.g. currentOnlineTest.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            self._connection.runLiveTest(dest=deviceId,
                                         testName=testName)
        except Exception as ex:
            raise dt.TcpServerError(
                f'Failed to send the run live test command.\n{ex}') from ex

class NetworkMetricsClient(DaemonTcpSocket):
    NETWORK_METRICS_TCP_SOCKET = 8699

    def __init__(self,
                 tcpPort: int = NETWORK_METRICS_TCP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(tcpPort=tcpPort, timeout=timeout)
    
    def checkOnline(self, deviceId: str) -> bool:
        """Checks is the DUT connected to the network using TCP protocol.
        
        Params:
            deviceId: string containing serial number of the device.

        Returns:
            True if the DUT synched, False otherwise.

        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            retVal = self._connection.getResponse("sync", deviceId)
        except Exception as ex:
            raise dt.NetworkMetricsServerError(
                f'Failed to retrieve network metrics data.\n{ex}') from ex
        return (retVal['liveNetworkMetrics']['sync'] == 'Synched')
    
    def getPSR(self, deviceId: str) -> int:
        """Gets the Packet Success Rate.
            
        Params:
            deviceId: serial number of the device.
        
        Returns:
            Integer containing PSR.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            jsonResponse = self._connection.getLiveNetworkMetrics(deviceId)
        except Exception as ex:
            raise dt.NetworkMetricsServerError(
                f'Failed to retrieve network '
                f'metrics data to get the PSR.\n{ex}'
            ) from ex
        return jsonResponse['liveNetworkMetrics']['psr']

class LiveTestClient(DaemonTcpSocket):
    TEST_TCP_SOCKET = 8688

    def __init__(self,
                 tcpPort: int = TEST_TCP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(tcpPort = tcpPort, timeout=timeout)
    
    def getLiveTestValue(self, deviceId: str) -> float:
        """Gets the value of the live test.
            
        Params:
            deviceId: serial number of the device.
        
        Returns:
            Value from the live test.
        
        Raises:
            ConnectionError: if sending the command failed.
        """
        time.sleep(DaemonSocket.SEND_COMMAND_DELAY)
        try:
            jsonResponse = self._connection.getLiveTestValue(dest=deviceId)
        except Exception as ex:
            raise dt.LiveTestChannelError(
                f'Failed to retrieve the live test value.\n{ex}') from ex
        return jsonResponse['channelValue']['value']

class RangingClient(DaemonUdpSocket):
    RANGING_UDP_SOCKET = 8797
    
    def __init__(self,
                 udpPort: int = RANGING_UDP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(udpPort=udpPort, timeout=timeout)
    
    def getOnlineDevices(self) -> list:
        """Gets online devices using the UDP protocol.

        Params:
            None.

        Returns:
            A list of devices connected to the network.
        """
        return self._connection.getDevices()
    
    def checkOnline(self, deviceId: str) -> bool:
        """Checks if the device under test is online.

        Params:
            deviceId: string containing serial number of the device.

        Returns:
            Boolean True or False.
        """
        dutOn = False
        devices = self.getOnlineDevices()
        for device in devices:
            if str(device).casefold() == str(deviceId).casefold():
                dutOn = True
                break
        return dutOn

class SlowSensorClient(DaemonUdpSocket):
    SLOW_SENSOR_UDP_SOCKET = 8798

    def __init__(self,
                 udpPort: int = SLOW_SENSOR_UDP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(udpPort=udpPort, timeout=timeout)
    
    def getAvgCurrent(self, deviceId: str) -> float:
        """Gets average current consumption value in mA using the UDP protocol.
        
        Params:
            deviceId: string containing the serial number of the DUT.

        Returns:
            Integer containing the average current consumption value in mA.
        """
        return self._connection.getCurrent(deviceId)

class ExtendedSlowSensorClient(DaemonUdpSocket):
    EXTENDED_SLOW_SENSOR_UDP_SOCKET = 8698

    def __init__(self,
                 udpPort: int = EXTENDED_SLOW_SENSOR_UDP_SOCKET,
                 timeout: float = 20) -> None:
        super().__init__(udpPort=udpPort, timeout=timeout)
    
    def getExtendedBattery(self, deviceId: str) -> dt.ExtendedBattery:
        """Gets extended slow sensor data using the UDP protocol.
        
        Params:
            deviceId: string containing the serial number of the DUT.

        Returns:
            Integer containing the average current consumption value in mA.
        """
        reply = self._connection.getExtendedSlowSensor("extendedBattery", deviceId)
        extendedBattery = dt.ExtendedBattery()
        extendedBattery.averageCurrent = reply['averageCurrent']
        extendedBattery.fullAvailableCapacity = reply['fullAvailableCapacity']
        extendedBattery.fullChargeCapacityFiltered = reply['fullChargeCapacityFiltered']
        extendedBattery.fullChargeCapacityUnfiltered = reply['fullChargeCapacityUnfiltered']
        extendedBattery.remainingCapacityFiltered = reply['remainingCapacityFiltered']
        extendedBattery.remainingCapacityUnfiltered = reply['remainingCapacityUnfiltered']
        extendedBattery.stateOfCharge = reply['stateOfCharge']
        extendedBattery.stateOfChargeUnfiltered = reply['stateOfChargeUnfiltered']
        extendedBattery.voltage = reply['voltage']
        return extendedBattery

    def getPressure(self, deviceId:str) -> dt.PressureSensor:
        """ Gets the pressure and temperature from the pressure sensor.
            (If the specified device has a pressure sensor...)

        Params:
            deviceId: string containing the serial number of the DUT.
        
        Returns:
            A separate float for pressure and temperature in that order.
        """
        reply = self._connection.getExtendedSlowSensor("pressure", deviceId)
        pressureSensor = dt.PressureSensor(pressure=reply['pressure'],
                                           temperature=reply['temperature'])
        return pressureSensor