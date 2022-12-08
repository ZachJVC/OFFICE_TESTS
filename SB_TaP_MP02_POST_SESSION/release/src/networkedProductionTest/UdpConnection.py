#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
UdpConnection.py
   __  __    __         ______                            __  _
  / / / /___/ /___     / ____/___  ____  ____  ___  _____/ /_(_)___  ____
 / / / / __  / __ \   / /   / __ \/ __ \/ __ \/ _ \/ ___/ __/ / __ \/ __ \
/ /_/ / /_/ / /_/ /  / /___/ /_/ / / / / / / /  __/ /__/ /_/ / /_/ / / / /
\____/\__,_/ .___/   \____/\____/_/ /_/_/ /_/\___/\___/\__/_/\____/_/ /_/
          /_/

@author: sportable
"""
import socket
import select
import json
import warnings
import time
import numpy as np
from src.datatypes import (RangingServerError,
                           NetworkMetricsServerError,
                           SlowSensorServerError,
                           ExtendedSlowSensorServerError)


class udpConnection():
    _udpSock = None
    def __init__(self, udpIp: str, udpPort: int, maxWait = 5):
        self.udpIP = udpIp
        self.udpPort = udpPort
        self.maxWait = maxWait
        self.measBufferLength = 50

    def base32encode(
            self,
            number,
            alphabet='0123456789ABCDEFGHJKMNPQRSTVWXYZ'):
        """Converts an integer to a base32 Crockford string."""
        if not isinstance(number, (int)):
            raise TypeError('Crockford ID number must be an integer')
        base32 = ''
        if number < 0:
            raise ValueError(
                'Negative number encountered. All numbers must be positive')
        while number != 0:
            number, i = divmod(number, len(alphabet))
            base32 = alphabet[i] + base32
        return base32

    def close(self):
        if self._udpSock is None:
            return
        self._udpSock.close()

    def open(self):
        if self._udpSock is not None:
            return
        # Open a UDP socket and get some measurements
        self._udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udpSock.settimeout(self.maxWait)
        self._udpSock.bind((self.udpIP, self.udpPort))
    
    def restart(self):
        self.close()
        self.open()

    def getDevices(self):
        self.open()
        deviceList = []
        ready = select.select([self._udpSock], [], [], self.maxWait)
        if ready[0]:
            try:
                while True:
                    data = self._udpSock.recv(4096)
                    msg = data.decode('utf8').split('\n')[0]
                    jsonMsg = json.loads(msg)
                    currentID = jsonMsg['id']

                    # Conditionally add measuring device to list
                    if currentID not in deviceList:
                        deviceList.append(currentID)
                        counter = 0

                    # Loop over the sources and conditionally add them to the
                    # list
                    for meas in jsonMsg['ranges']:
                        currentID = meas['source']
                        if currentID not in deviceList:
                            deviceList.append(currentID)
                            counter = 0
                    counter += 1

                    # If we've had > 20 packets without adding a new device -
                    # break
                    if counter >= 20:
                        break
            except Exception as error:
                self.close()
                raise RangingServerError(
                    f'Getting devices failed.\n{error}') from error

        # Sort device list ascending
        deviceList.sort()
        deviceNames = [self.base32encode(int(deviceList[i])) for i in range(
            len(deviceList))]  # TODO: make readable
        self.close()
        return deviceNames

    def getLiveImuDataFromTag(self, tagName):
        self.open()
        ready = select.select([self._udpSock], [], [], self.maxWait)
        if ready[0]:
            while True:
                try:
                    data = self._udpSock.recv(4096)
                    msg = data.decode('utf8').split('\n')[0]
                    jsonMsg = json.loads(msg)
                    currentTime = time.time()
                    if self.base32encode(int(jsonMsg['id'])) == tagName:
                        self.close()
                        return jsonMsg['imu']
                    else:
                        continue
                except Exception:
                    return []

    def getInterDeviceMeasHistories(self, **kwargs):
        """
        Fills a 3D array of inter-device measurements

        Parameters
        ----------
        deviceList  : list
        bufferLength: int
        dataType    : string {'range' / 'rssi'}

        Returns
        -------
        measBuffer  : np.array
            DESCRIPTION.

        """

        deviceList = kwargs['devices']
        bufferLength = kwargs['bufferLength']
        dataType = kwargs['dataType']

        self.open()
        self.frameCounter = -1
        previousTime = 0

        numDevices = len(deviceList)
        self.measBuffer = np.nan * \
            np.zeros((numDevices, numDevices, bufferLength))
        self.numMeasArray = np.zeros((numDevices, numDevices))

        ready = select.select([self._udpSock], [], [], self.maxWait)
        if ready[0]:
            try:
                while True:
                    data = self._udpSock.recv(4096)
                    msg = data.decode('utf8').split('\n')[0]
                    jsonMsg = json.loads(msg)

                    # Fill the data buffers
                    ancA = self.base32encode(jsonMsg['id'])
                    try:  # It might not be in the list!
                        ancAInd = deviceList.index(ancA)
                    except Exception:
                        # If it's not in the list we don't want its data
                        continue

                    currentTime = jsonMsg['time']
                    if currentTime > previousTime:
                        previousTime = currentTime
                        self.frameCounter += 1
                        if self.frameCounter == bufferLength:
                            break
                    elif currentTime < previousTime:
                        # Packets out of order
                        continue
                    else:
                        # CurrentTime = previousTime
                        # Do not increment frameCounter
                        None

                    for meas in jsonMsg['ranges']:
                        ancB = self.base32encode(meas['source'])
                        try:  # It might not be in the list!
                            ancBInd = deviceList.index(ancB)
                        except Exception:
                            # If it's not in the list we don't want its data
                            continue

                        meas = meas[dataType]
                        self.measBuffer[ancAInd, ancBInd,
                                        self.frameCounter] = meas
                        self.numMeasArray[ancAInd, ancBInd] += 1
            except Exception:
                self.close()
                return []

        self.close()
        return self.measBuffer

    def getImuDataFromAllTags(self, **kwargs):
        """
        Fills a 3D array of IMU measurements

        Parameters
        ----------
        devices  : list
        bufferLength: int

        Returns
        -------
        accBuffer  : np.array - containing vector sum of accelerations
        gyrBuffer  : np.array - containing vector sum of angular velocities
        """

        deviceList = kwargs['devices']
        bufferLength = kwargs['bufferLength']
        bufferFillTimeAt52Hz = bufferLength / 52.0

        self.open()
        self.frameCounter = -1
        previousTime = 0

        numDevices = len(deviceList)

        # These arrays are shaped differently to the arrays in
        # getInterDeviceMeasHistories and getMeasRssiTime
        self.accBuffer = np.nan * np.zeros((bufferLength, numDevices))
        self.gyrBuffer = np.nan * np.zeros((bufferLength, numDevices))
        self.timeVector = np.nan * np.zeros((bufferLength, 1))
        self.numMeasArray = np.zeros((numDevices, 1))

        ready = select.select([self._udpSock], [], [], self.maxWait)
        if ready[0]:
            try:
                bufferStartTime = time.time()
                while True:
                    data = self._udpSock.recv(4096)
                    msg = data.decode('utf8').split('\n')[0]
                    jsonMsg = json.loads(msg)
                    if 'imu' not in jsonMsg.keys():
                        continue

                    # Fill the data buffers
                    ancA = self.base32encode(jsonMsg['id'])
                    try:  # It might not be in the list!
                        ancAInd = deviceList.index(ancA)
                    except Exception:
                        # If it's not in the list we don't want its data
                        continue

                    currentTime = jsonMsg['time']
                    if currentTime > previousTime:
                        previousTime = currentTime
                        self.frameCounter += 1
                        if self.frameCounter == bufferLength:
                            break
                    elif currentTime < previousTime:
                        # Packets out of order
                        continue
                    else:
                        # CurrentTime = previousTime
                        # Do not increment frameCounter
                        None

                    for imuMeas in jsonMsg['imu']:
                        # Label the IMU components for readability
                        aXYZ = np.array(
                            [imuMeas['accel']['x'], imuMeas['accel']['y'], imuMeas['accel']['z']])
                        gXYZ = np.array(
                            [imuMeas['gyro']['x'], imuMeas['gyro']['y'], imuMeas['gyro']['z']])

                        self.accBuffer[self.frameCounter,
                                       ancAInd] = np.linalg.norm(Axyz)
                        self.gyrBuffer[self.frameCounter,
                                       ancAInd] = np.linalg.norm(Gxyz)
                        self.timeVector[self.frameCounter] = currentTime
                        self.numMeasArray[ancAInd] += 1

                        bufferCurrentTime = time.time()
                        if bufferCurrentTime - bufferStartTime > bufferFillTimeAt52Hz:
                            # Timer expired - ending capture of IMU packets
                            return self.accBuffer, self.gyrBuffer, self.timeVector, self.numMeasArray
            except Exception as error:
                self.close()
                raise ConnectionError(
                    f'Retrieving IMU data failed.\n{error}') from error

        self.close()
        return self.accBuffer, self.gyrBuffer, self.timeVector, self.numMeasArray

    def getMeasRssiTime(self, **kwargs):
        """
        Fills a 3D array of inter-device measurements

        Parameters
        ----------
        deviceList  : list
        bufferLength: int

        Returns
        -------
        measBuffer  : np.array
        rssiBuffer  : np.array
        timeVector  : np.array
        """

        deviceList = kwargs['devices']
        bufferLength = kwargs['bufferLength']
        bufferFillTimeAt20Hz = bufferLength / 20.0

        self.open()
        self.frameCounter = -1
        previousTime = 0

        numDevices = len(deviceList)
        self.measBuffer = np.nan * \
            np.zeros((numDevices, numDevices, bufferLength))
        self.rssiBuffer = np.nan * \
            np.zeros((numDevices, numDevices, bufferLength))
        self.timeVector = np.nan * np.zeros((bufferLength, 1))
        self.numMeasArray = np.zeros((numDevices, numDevices))

        ready = select.select([self._udpSock], [], [], self.maxWait)
        if ready[0]:
            try:
                bufferStartTime = time.time()
                while True:
                    data = self._udpSock.recv(4096)
                    msg = data.decode('utf8').split('\n')[0]
                    jsonMsg = json.loads(msg)

                    # Fill the data buffers
                    ancA = self.base32encode(jsonMsg['id'])
                    try:  # It might not be in the list!
                        ancAInd = deviceList.index(ancA)
                    except Exception:
                        # If it's not in the list we don't want its data
                        continue

                    currentTime = jsonMsg['time']
                    if currentTime > previousTime:
                        previousTime = currentTime
                        self.frameCounter += 1
                        if self.frameCounter == bufferLength:
                            break
                    elif currentTime < previousTime:
                        # Packets out of order
                        continue
                    else:
                        # CurrentTime = previousTime
                        # Do not increment frameCounter
                        None
                    for meas in jsonMsg['ranges']:
                        ancB = self.base32encode(meas['source'])
                        try:  # It might not be in the list!
                            ancBInd = deviceList.index(ancB)
                        except Exception:
                            # If it's not in the list we don't want its data
                            continue

                        self.measBuffer[ancAInd, ancBInd,
                                        self.frameCounter] = meas['range']
                        self.rssiBuffer[ancAInd, ancBInd,
                                        self.frameCounter] = meas['rssi']
                        self.timeVector[self.frameCounter] = currentTime
                        self.numMeasArray[ancAInd, ancBInd] += 1

                        bufferCurrentTime = time.time()
                        if bufferCurrentTime - bufferStartTime > bufferFillTimeAt20Hz:
                            # Timer expired next power
                            return self.measBuffer, self.rssiBuffer, self.timeVector, self.numMeasArray
            except Exception:
                self.close()
                return []

        self.close()
        return self.measBuffer, self.rssiBuffer, self.timeVector, self.numMeasArray

    def getMedianInterDeviceDistances(self, deviceList):
        """ Calculates medianMeas; a matrix of median inter-device distances """

        self.measBuffer = self.getInterDeviceMeasHistories(
            devices=deviceList, bufferLength=self.measBufferLength, dataType='range')

        # Filter out the annoying runtime warning for "Mean of empty slice"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            medianMeas = np.nanmean(self.measBuffer, axis=2)
        return medianMeas

    def getMedianInterDeviceRssi(self, deviceList):
        """ Calculates medianRssi; a matrix of median inter-device rssi values"""

        self.measBuffer = self.getInterDeviceMeasHistories(
            devices=deviceList, bufferLength=self.measBufferLength, dataType='rssi')

        # Filter out the annoying runtime warning for "Mean of empty slice"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            medianRssi = np.nanmean(self.measBuffer, axis=2)
        return medianRssi

    def printPacketsToTerminal(self):
        self.open()
        ready = select.select([self._udpSock], [], [], self.maxWait)
        if ready[0]:
            try:
                while True:
                    data = self._udpSock.recv(4096)
                    print(data.decode())
            except Exception:
                self.close()

    def getImuStatistics(self, **kwargs):
        """
        returns an array statsMat, each row contains data for a device. The columns are:
        # 0) % Measurements received
        # 1) Mean Acc
        # 2) Stdev Acc
        # 3) Mean Gyr
        # 4) Stdev Gyr
        # 5) Mean Rate
        # 6) Stdev Rate
        """

        duts = kwargs['devices']  # Devices Under Test
        bufferLength = kwargs['bufferLength']
        bufferFillTimeAt52Hz = bufferLength / 52.0
        acc, gyro, time, numMeas = self.getImuDataFromAllTags(
            devices=duts, bufferLength=bufferLength)
        statsMat = np.zeros((len(duts), 7))

        for j, device in enumerate(duts):
            deviceInd = duts.index(device)
            numMeasReceived = numMeas[deviceInd]
            meanAcc = np.nanmean(acc[:, deviceInd])
            stdDevAcc = np.nanstd(acc[:, deviceInd])
            meanGyro = np.nanmean(gyro[:, deviceInd])
            stdDevGyro = np.nanstd(gyro[:, deviceInd])
            updateRate = self.calculateUpdateRate(time, acc[:, deviceInd])
            meanUpdateRate = numMeas[deviceInd] / bufferFillTimeAt52Hz
            stdDevUpdateRate = np.nanstd(updateRate)
            statsMat[j,
                     :] = np.array([100 * numMeasReceived / bufferLength,
                                    meanAcc,
                                    stdDevAcc,
                                    meanGyro,
                                    stdDevGyro,
                                    meanUpdateRate,
                                    stdDevUpdateRate])
        return statsMat

    def getStatistics(self, **kwargs):
        """
        returns an array statsMat, each row contains data for a device. The columns are:
        # 0) Master TX Power
        # 1) % Measurements received
        # 2) Mean Range
        # 3) Stdev Range
        # 4) Mean Rssi
        # 5) Stdev Rssi
        # 6) Mean Rate
        # 7) Stdev Rate
        """

        duts = kwargs['devices']  # Devices Under Test
        bufferLength = kwargs['bufferLength']
        master = kwargs['master']
        masterTxPower = kwargs['power']
        sideOfLink = kwargs['sideOfLink']

        bufferFillTimeAt20Hz = bufferLength / 20.0
        devices = duts + [master]
        masterInd = devices.index(master)

        meas, rssi, time, numMeas = self.getMeasRssiTime(
            devices=devices, bufferLength=bufferLength)
        statsMat = np.zeros((len(duts), 8))
        for j, device in enumerate(duts):
            deviceInd = devices.index(device)
            if sideOfLink.lower() == 'master':
                numMeasToMaster = numMeas[masterInd, deviceInd]
                meanRangeToMaster = np.nanmean(meas[masterInd, deviceInd, :])
                stdDevRangeToMaster = np.nanstd(meas[masterInd, deviceInd, :])
                meanRssiToMaster = np.nanmean(rssi[masterInd, deviceInd, :])
                stdDevRangeToMaster = np.nanstd(rssi[masterInd, deviceInd, :])
                updateRate = self.calculateUpdateRate(
                    time, meas[masterInd, deviceInd, :])
                meanUpdateRate = numMeas[masterInd,
                                         deviceInd] / bufferFillTimeAt20Hz
                stdDevUpdateRate = np.nanstd(updateRate)
                statsMat[j,
                         :] = np.array([masterTxPower,
                                        100 * numMeasToMaster / bufferLength,
                                        meanRangeToMaster,
                                        stdDevRangeToMaster,
                                        meanRssiToMaster,
                                        stdDevRangeToMaster,
                                        meanUpdateRate,
                                        stdDevUpdateRate])
            elif sideOfLink.lower() == 'device':
                numMeasToDevice = numMeas[deviceInd, masterInd]
                meanRangeToDevice = np.nanmean(meas[deviceInd, masterInd, :])
                stdDevRangeToDevice = np.nanstd(meas[deviceInd, masterInd, :])
                meanRssiToDevice = np.nanmean(rssi[deviceInd, masterInd, :])
                stdDevRangeToDevice = np.nanstd(rssi[deviceInd, masterInd, :])
                updateRate = self.calculateUpdateRate(
                    time, meas[deviceInd, masterInd, :])
                meanUpdateRate = numMeas[deviceInd,
                                         masterInd] / bufferFillTimeAt20Hz
                stdDevUpdateRate = np.nanstd(updateRate)
                statsMat[j,
                         :] = np.array([masterTxPower,
                                        100 * numMeasToDevice / bufferLength,
                                        meanRangeToDevice,
                                        stdDevRangeToDevice,
                                        meanRssiToDevice,
                                        stdDevRangeToDevice,
                                        meanUpdateRate,
                                        stdDevUpdateRate])
        return statsMat

    def calculateUpdateRate(self, time, meas):
        """ A quick function taking in a time vector and a measurement vector
        to calculate the update rate in Hz"""

        updateRate = []
        startBool = True
        for j in range(len(meas)):
            if np.isnan(meas[j]):
                continue
            else:
                if startBool:
                    initialTime = time[j][0]
                    startBool = False
                else:
                    finalTime = time[j][0]
                    freq = 1 / (finalTime - initialTime)
                    updateRate.append(freq)
                    initialTime = time[j][0]
        return np.asarray(updateRate)

    def getCurrent(self, serialNumber):
        self.open()
        avr_current = None
        startTime = time.time()
        while True:
            time.sleep(0.05)
            currentTime = time.time() - startTime
            if currentTime > self.maxWait:
                # We've waited too long for the response
                self.close()
                raise TimeoutError('Connection timed out')
            try:
                data = self._udpSock.recv(4096)
                msg = data.decode('utf8').split('\n')[0]
                jsonMsg = json.loads(msg)
                deviceId = jsonMsg['deviceId']
                if deviceId == 0:
                    continue
                if self.base32encode(deviceId) == str(serialNumber):
                    avr_current = jsonMsg['avgCurrent']
                    if avr_current != None:
                        break
            except Exception as error:
                self.close()
                raise SlowSensorServerError(
                    f'Getting current failed.\n{error}') from error
        self.close()
        return avr_current

    def getExtendedSlowSensor(self, section: str, serialNumber: str) -> dict:
        self.open()
        jsonMsg = None
        startTime = time.time()
        while True:
            time.sleep(0.05)
            currentTime = time.time() - startTime
            if currentTime > self.maxWait:
                # We've waited too long for the response
                self.close()
                raise TimeoutError('Connection timed out')
            try:
                data = self._udpSock.recv(4096)
                msg = data.decode('utf8').split('\n')[0]
                jsonMsg = json.loads(msg)
                if ((serialNumber in str(jsonMsg)) and
                    (section in str(jsonMsg))):
                    break
            except Exception as error:
                self.close()
                raise ExtendedSlowSensorServerError(
                    f'Getting extended slow '
                    f'sensor data failed.\n{error}'
                ) from error
        self.close()
        return jsonMsg['liveSlowSensor'][section]

    def getDeviceId(self):
        self.open()
        ready = select.select([self._udpSock], [], [], self.maxWait)
        deviceId = None
        if ready[0]:
            try:
                while True:
                    data = self._udpSock.recv(4096)
                    msg = data.decode('utf8').split('\n')[0]
                    jsonMsg = json.loads(msg)
                    
                    deviceId = jsonMsg['deviceId']
                    if deviceId != None:
                        break

            except Exception as error:
                self.close()
                raise NetworkMetricsServerError(
                    f'Getting device ID failed.\n{error}') from error
        self.close()
        return deviceId