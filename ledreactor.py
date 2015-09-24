import serial

class LedHandler():
    def __init__(self, logger):
        self.errorCode = b'\x01'

        self.logger = logger
        self.ser = serial.Serial('/dev/ttyUSB0', 9600)

    def cruncherMonster(self, wasSuccess=True):
        if wasSuccess:
            self.logger.info("CrunchMoster was successful")
            self.ser.write(b'\x00')
        else:
            self.ser.write(self.errorCode)
            self.logger.error("CrunchMonster failed")

    def rfcrunchStatus(self, testTotal, success, fails, errors):
        #self.ser.write(b'\x?')
        self.logger.info(" *** We ran {0} tests, {1} of them was successes, {2} was failures and {3} made errors. *** ".format(testTotal, success, fails, errors))

    def criticalFail(self, message):
        self.ser.write(self.errorCode)
        self.logger.error("Critical failure occured with message: {0}".format(message))
