#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
ProductionTest.py
    ____                 __           __  _
   / __ \_________  ____/ /_  _______/ /_(_)___  ____
  / /_/ / ___/ __ \/ __  / / / / ___/ __/ / __ \/ __ \
 / ____/ /  / /_/ / /_/ / /_/ / /__/ /_/ / /_/ / / / /
/_/___/_/   \____/\__,_/\__,_/\___/\__/_/\____/_/ /_/
 /_  __/__  _____/ /_
  / / / _ \/ ___/ __/
 / / /  __(__  ) /_
/_/  \___/____/\__/

@author: sportable
"""


import datetime
import sys
import copy
import numpy as np
import pandas as pd


class productionTest():
    """
    A class which handles the runs the tests on devices
    """

    def __init__(self, **kwargs):

        self.udp = kwargs['udpConnection']
        self.tcp = kwargs['tcpConnection']
        self.config = kwargs['config']
        self.devices = kwargs['devices']

        # Set power levels used for range test
        self.maxPower = 67
        self.midPower = 22
        self.minPower = 0

        # Set intermediate power level for tx test
        self.txTestPowerLevel = 40

        # Set pass/fail criteria
        # If power where meas rate goes below 10Hz is greater than 30, fail it
        self.rangeTestCutOffPower = 30
        self.txTestCutOffRssi = -85   # If it's less than -85dB then fail
        self.imuTestCutOffRate = 45    # If it's less than 45Hz then fail

        # Set range test power steps
        self.coursePowerStepSize = -5
        self.finePowerStepSize = -2

        # This is the buffer size for the stats we get from udp.getStatistics
        self.measBufferLength = 100
        self.imuBufferLength = int(
            np.floor((52.0 / 20.0) * self.measBufferLength))

        # Create filename for tag pass/fail results
        self.passFailResultsFile = 'Results/' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + \
            '_Tag_Pass_Fail_Results' + '.txt'

    def imuTest(self):
        """Looks at the IMU rate from each tag with the master at full power"""

        print('\n\n---------- BEGIN IMU TEST ----------\n\n')
        # Set master to full power
        self.tcp.setTxPower(anchorID=self.devices.master, txPower=67)

        # Get IMU statistics
        imuStats = self.udp.getImuStatistics(
            devices=self.devices.duts,
            bufferLength=self.imuBufferLength)
        print('\nIMU test finished')
        return imuStats

    def publishDataToExcel(self, **kwargs):
        """ Publish reports for each device as excel files"""

        rangeTestData = kwargs['rangeTestData']
        txTestData = kwargs['txTestData']
        imuTestData = kwargs['imuTestData']
        for j, deviceName in enumerate(self.devices.duts):
            # Shape the data correctly for export to Excel
            currentRangeTestData = np.squeeze(rangeTestData[j, :, :]).T
            currentTxTestData = txTestData[j, :].reshape(1, 8)
            currentImuTestData = imuTestData[j, :].reshape(1, 7)

            # Here I'm converting the arrays into Pandas dataframes, because
            # the export to Excel is so much easier
            pdRangeTest = pd.DataFrame(
                currentRangeTestData,
                columns=[
                    'Master Tx Power',
                    '% Meas',
                    'Mean Range',
                    'Stdev Range',
                    'Mean Rssi',
                    'Stdev RSSI',
                    'Mean Rate',
                    'Stdev Rate'])
            pdTxTest = pd.DataFrame(
                currentTxTestData,
                columns=[
                    'Master Tx Power',
                    '% Meas',
                    'Mean Range',
                    'Stdev Range',
                    'Mean Rssi',
                    'Stdev RSSI',
                    'Mean Rate',
                    'Stdev Rate'])
            pdImuTest = pd.DataFrame(
                currentImuTestData,
                columns=[
                    '% Meas',
                    'Mean Acc',
                    'Stdev Acc',
                    'Mean Gyro',
                    'Stdev Gyro',
                    'Mean Rate',
                    'Stdev Rate'])

            fileName = 'Results/' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + \
                '_' + deviceName + '.xlsx'
            writer = pd.ExcelWriter(fileName, engine='xlsxwriter')

            # Export all data into three separate sheets
            pdRangeTest.to_excel(writer, sheet_name='Range Test Results')
            pdTxTest.to_excel(writer, sheet_name='TX Test Results')
            pdImuTest.to_excel(writer, sheet_name='IMU Test Results')
            writer.save()

        return

    def rangeTest(self):
        """
        Performs a range test by looking at the effective PER for each device as the master's TX power is stepped down.
        The effective PER is determined in udp.getStatistics by filling a buffer with measurements from each device
        under test (DUT) and comparing the number received to the number that should have been received at 20Hz
        """
        print('\n\n---------- BEGIN RANGE TEST ----------\n\n')
        courseRange = np.arange(
            self.maxPower,
            self.midPower,
            self.coursePowerStepSize,
            dtype=int)
        fineRange = np.arange(
            self.midPower,
            self.minPower,
            self.finePowerStepSize,
            dtype=int)

        # The power levels that we'll investigate during the experiment are
        powerLevels = np.concatenate(
            (courseRange.reshape(
                len(courseRange), 1), fineRange.reshape(
                len(fineRange), 1)), axis=0)
        numPowers = len(powerLevels)

        # Initialise all device TX power levels to max power
        self.tcp.setAllTxPowersTo(
            devices=self.devices.devices,
            txPower=self.maxPower)

        # Begin stepping through the power levels
        for iteration, currentPowerLevel in enumerate(powerLevels):
            print(f"Currently on iteration {iteration} of {numPowers}")

            # Set master power level to currentPowerLevel
            self.tcp.setTxPower(
                anchorID=self.devices.master,
                txPower=int(currentPowerLevel))

            # Get statistics
            stats = self.udp.getStatistics(
                devices=self.devices.duts,
                bufferLength=self.measBufferLength,
                master=self.devices.master,
                power=currentPowerLevel,
                sideOfLink='device')

            # Verify we are on the correct power
            if currentPowerLevel != self.tcp.getTxPower(
                    self.devices.master)[0]:
                print(
                    "Experiment corrupted, Master power level not equal to what was set")
                raise Exception('Experiment corrupted')

            # Record the experimental results
            if iteration == 0:
                resultsArray = stats.reshape(self.devices.numDuts, 8, 1)
            else:
                resultsArray = np.concatenate(
                    (resultsArray, stats.reshape(
                        self.devices.numDuts, 8, 1)), axis=2)

        # Set master back to max power
        self.tcp.setTxPower(
            anchorID=self.devices.master,
            txPower=self.maxPower)

        print('\nRange test finished')
        return resultsArray

    def rangeTestPassFail(self, **kwargs):
        """
        Uses linear interpolation to determine a pass, fail or indeterminate
        Pass            =  1
        Fail            = -1
        Indeterminate   =  0
        """

        x = kwargs['x']
        y = kwargs['y']
        ym = kwargs['interpolateAtY']

        # Check if ym is contained in y
        if y.min() < ym < y.max():
            # Can interpolate

            # Rescale y in terms of ym
            yRescale = y - ym

            # Set negative entries to nan
            yNegative = copy.deepcopy(yRescale)
            yNegative[yRescale < 0] = np.nan

            # Set positive entries to nan
            yPositive = copy.deepcopy(yRescale)
            yPositive[yRescale > 0] = np.nan

            # Find the data points which bound ym
            upperIndex = np.nanargmin(yNegative)
            lowerIndex = np.nanargmax(yPositive)

            yUpper = y[upperIndex]
            yLower = y[lowerIndex]
            xUpper = x[upperIndex]
            xLower = x[lowerIndex]

            xInterpolated = xLower + \
                ((xUpper - xLower) / (yUpper - yLower)) * (ym - yLower)

            if xInterpolated > self.rangeTestCutOffPower:
                # Device passed
                return 1
            else:
                # Device failed
                return -1

        if ym < y.min():
            # This could be a subtle failure if device failed early and y.min() is at a high power
            # This warrants further investigation, therefore indeterminate
            return 0

        if np.sum(np.isnan(y)) >= (len(y) - 1):
            # Device may have turned off - therfore indeterminate
            return 0

    def tagPassOrFail(self, **kwargs):
        """
        Classify the DUTs as pass or fail for various test data
        """
        rangeTestData = kwargs['rangeTestData']
        txReport = kwargs['txTestData']
        imuReport = kwargs['imuTestData']
        dash = '-' * 64  # Used for formatting

        with open(self.passFailResultsFile, "a") as resultFile:
            resultFile.write(dash)
            resultFile.write('\n')
            resultFile.write(
                '{:<10s}{:>18s}{:>18s}{:>18s}'.format(
                    'Device',
                    'Range Result',
                    'TX Result',
                    'IMU Result'))
            resultFile.write('\n')
            resultFile.write(dash)
            resultFile.write('\n')

        for j, device in enumerate(self.devices.duts):
            powerLevels = rangeTestData[j, 0, :]
            meanMeasRate = rangeTestData[j, 6, :]
            txRssiAsMeasuredByMaster = txReport[j, 4]
            imuRate = imuReport[j, 5]

            # Did the device pass the range test?
            rangePass = self.rangeTestPassFail(
                x=powerLevels, y=meanMeasRate, interpolateAtY=10)

            # Did the device pass the tx test?
            if txRssiAsMeasuredByMaster < self.txTestCutOffRssi:
                txPass = -1  # FAIL
            else:
                txPass = 1  # PASS

            # Did the device pass the IMU test
            if imuRate < self.imuTestCutOffRate:
                imuPass = -1  # FAIL
            else:
                imuPass = 1  # PASS

            resultList = (device + ': ' + str(rangePass) + ' ' +
                          str(txPass) + ' ' + str(imuPass)).split()
            with open(self.passFailResultsFile, "a") as resultFile:
                resultFile.write(
                    '{:<10s}{:>18s}{:>18s}{:>18s}'.format(
                        resultList[0],
                        resultList[1],
                        resultList[2],
                        resultList[3]))
                resultFile.write('\n')

    def txTest(self):
        """
        This test sets the DUTs tx powers to an intermediate power - self.txTestPowerLevel
        The udp.getStatistics function is then called, but using sideOfLink = Master
        """

        print('\n\n---------- BEGIN TX TEST ----------\n\n')
        numAttempts = 5
        attemptCounter = 0

        while attemptCounter <= numAttempts:
            # Initialise all DUT TX power levels to self.txTestPowerLevel
            self.tcp.setAllTxPowersTo(
                devices=self.devices.duts,
                txPower=self.txTestPowerLevel)

            # Get statistics
            stats = self.udp.getStatistics(
                devices=self.devices.duts,
                bufferLength=self.measBufferLength,
                master=self.devices.master,
                power=self.txTestPowerLevel,
                sideOfLink='master')

            # Check that all the DUTs have the correct power level
            for device in self.devices.duts:
                if self.tcp.getTxPower(device)[0] != self.txTestPowerLevel:
                    print(
                        f'Device {device} has incorrect power level, restarting the experiment')
                    attemptCounter += 1
                    continue

            # Every device is at the correct power level, reset the powers and
            # return
            self.tcp.setAllTxPowersTo(
                devices=self.devices.duts,
                txPower=self.maxPower)
            print('\nTX test finished')
            return stats

        # Left the while loop without successfully executing the experiment
        # Reset power levels to max and exit with error
        self.tcp.setAllTxPowersTo(
            devices=self.devices.duts,
            txPower=self.maxPower)
        raise Exception('TX test failed')

    def userSpecifyIfProceed(self):
        """
        Parse user input
        """
        userAcceptableAnswers = ['a', 'c', 'r', 'abort', 'continue', 'rescan']
        while True:
            if len(self.devices.duts) == 0:
                print('No devices were found: Abort or Rescan?\n\nUser Input (A,R): ')
            else:
                print('These devices were found: Abort, Continue or Rescan?')
                for j, device in enumerate(self.devices.duts):
                    print(f"{str(j).zfill(2)}: {device}")
                print('\n\nUser Input (A,C,R): ')

            userInput = input()
            if userInput.lower() not in userAcceptableAnswers:
                # If it's not a recognisable answer, then just rescan
                userInput = 'r'

            if (userInput.lower() == 'a') or (userInput.lower == 'abort'):
                # Abort execution of script and close TCP connection
                self.tcp.close()
                raise Exception('User aborted operation: closing TCP connection')

            if (userInput.lower() == 'r') or (userInput.lower() == 'rescan'):
                # Rescan for new devices and retry
                self.devices.devices = self.udp.getDevices()
                self.devices.duts = [
                    device for device in self.devices.devices if device != self.devices.master]
                # Clear terminal hack
                print(chr(27) + "[2J")
                continue

            if ((userInput.lower() == 'c') or (userInput.lower() == 'continue')) and (
                    len(self.devices.duts) != 0):
                return
