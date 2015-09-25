import serial
import logging

class LedHandler():
    def __init__(self, logger):
        self.errorCode = b'\x01'

        self.logger = logger
        self.ser = serial.Serial('/dev/ttyUSB0', 9600)
        self.ser.close()

    def cruncherMonster(self, wasSuccess=True):
        self.ser.open()
        if wasSuccess:
            self.logger.info("CrunchMoster was successful")
            self.ser.write(b'\x00')
        else:
            self.ser.write(self.errorCode)
            self.logger.error("CrunchMonster failed")
        self.ser.close()

    def rfcrunchStatus(self, testTotal, success, fails, errors):
        self.ser.open()
        self.ser.write(bytes([42]));
        self.ser.write(bytes([testTotal]));
        self.ser.write(bytes([success]));
        self.ser.write(bytes([fails]));
        self.ser.write(bytes([errors]));
        self.logger.info(" *** We ran {0} tests, {1} of them was successes, {2} was failures and {3} made errors. *** ".format(testTotal, success, fails, errors))
        self.ser.close()

    def criticalFail(self, message):
        self.ser.open()
        self.ser.write(self.errorCode)
        self.logger.error("Critical failure occured with message: {0}".format(message))
        self.ser.close()
