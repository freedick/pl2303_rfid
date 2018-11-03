#!/usr/bin/env python2
"""
This is just a quick and dirty implementation of the protocol described here:
https://www.triades.net/13-geek/13-serial-protocol-for-a-chinese-rfid-125khz-reader-writer.html
This is probably public domain
No warranty
"""

import serial
from time import sleep
realhex = lambda x: hex(x)[2:] # getting flashbacks to mysqlrealescapestring...

def checksum(data):
    csum = 0
    for char in data:
        csum ^= ord(char)
    return chr(csum)

def createCommand(commandCode, data):
    length = len(data) + 3
    data = chr(commandCode/256) + chr(commandCode%256) + data
    data = data + checksum(data)
    return chr(0xaa) + chr(0xdd) + (chr(length/256) + chr(length%256) + data).replace(chr(0xaa), chr(0xaa)+chr(0x00))


def hexprint(data):
    print " ".join([realhex(ord(x)) for x in data])

def sendCommand(device, commandCode, data):
    device.write(createCommand(commandCode,data))

def readResponse(device):
    assert(ord(device.read(1))==0xaa)
    assert(ord(device.read(1))==0xdd)
    length = 256 * ord(device.read(1))
    length += ord(device.read(1))
    data = device.read(length)
    assert(checksum(data[:-1]) == data[-1])
    responseCode = ord(data[0]) * 256 + ord(data[1])
    return (responseCode, data[2:-1])

def doCommand(device, commandCode, data):
    sendCommand(device, commandCode, data)
    return readResponse(device)

def printResponse(resp):
    print realhex(resp[0]), ":",
    hexprint(resp[1])
    print '"'+resp[1]+'"' 

def beep(device, time):
    # apparently it is supposed to be -1 for endless beep
    return doCommand(device, 0x0103, chr(1+ time))

def led(device, color):
    return doCommand(device, 0x0104, chr(color))

def info(device):
    return doCommand(device, 0x0102, "")

def readTag(device):
    return doCommand(device, 0x010c, "")

def writeTag(device, data):
    packet = chr(0)+data
    response = doCommand(device, 0x020c, packet)
    if ord(response[1][0])==0:
        return response
    return doCommand(device, 0x030c, packet)

if __name__=="__main__":
    device = serial.Serial("/dev/ttyUSB0", 38400)
    printResponse(info(device))

    for i in range(30):
        #test some beeping nd blinking
        beep(device, i%3)
        led(device, i%3)
    for j in range(10):
        print "reading card..."
        response = readTag(device)
        i = 0
        while 0!=ord(response[1][0]):
            #This commented line will write 11 22 33 44 55 to a card
            #response = writeTag(device, "".join([chr(x) for x in [0x11, 0x22, 0x33, 0x44, 0x55]]))
            response = readTag(device)
            led(device, i%3)
            i+=1
        beep(device, 10)
        printResponse(response)
        sleep(0.5)

