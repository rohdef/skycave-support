import serial
import os
import sys
import urllib.request

class CruncherMonster():
    def __init__(self):
        pass

    def crunch(self):
        statsUrl = "http://users-cs.au.dk/baerbak/c/cloud/current-score-operations-socket.txt"

        try:
            with open("lastDiffFile", "r+") as lastDiffFile:
                fileContents = lastDiffFile.read()
                fileContentsList = fileContents.split("\n")
                del fileContents

                lastDiff = int(fileContentsList[0])

                statsResponse = urllib.request.urlopen(statsUrl)
                stats = statsResponse.read().decode("utf-8")
                del statsResponse

                for stat in stats.split("\n"):
                    if stat.startswith("CSS 25"):
                        stat = " ".join(stat.split())
                        statTokens = stat.split(" ")
                        count = int(statTokens[2])
                        success = int(statTokens[3])
                        diff = count-success

                        #ser = serial.Serial('/dev/ttyUSB0', 9600)
                        #if diff > lastDiff:
                        #    ser.write(b'\x01')
                        #else:
                        #    ser.write(b'\x00')
                        #del ser

                        lastDiff = diff

                del stat
                del statTokens
                del count
                del success
                del diff

                #add
                lastDiffFile.seek(0,0)
                lastDiffFile.truncate()
                lastDiffFile.write(str(lastDiff) + "\n" + "\n".join(fileContentsList[:5]))
                del lastDiff
            del lastDiffFile
        except:
            print("Unexpected error:", sys.exc_info()[0])
            pass

if __name__ == "__main__":
    cruncherMonster = CruncherMonster()
    cruncherMonster.crunch()
