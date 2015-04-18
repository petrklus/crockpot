# coding=utf-8

import serial
import json
import random
import time
import datetime
import threading, Queue
import logging
import struct

import time
import sys
import glob
"""
logging.basicConfig(filename=__file__.replace('.py','.log'),level=logging.DEBUG,format='%(asctime)s [%(name)s.%(funcName)s] %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filemode='a')
"""

# from http://stackoverflow.com/questions/18752980/reading-serial-data-from-arduino-with-python
class SerialCommunicator(threading.Thread):
    def __init__(self, dataQ, errQ, port, baudrate=19200):
        self.logger = logging.getLogger('SerialCommunicator')
        self.logger.debug('initializing')
        threading.Thread.__init__(self)
        self.port = port
        self.baudrate = baudrate
        self.init_serial()
        #self.ser.flushInput()
        self.readCount = 0
        self.sleepDurSec = 5
        self.waitMaxSec = self.sleepDurSec * self.ser.baudrate / 10
        self.dataQ = dataQ
        self.errQ = errQ
        self.keepAlive = True
        self.stoprequest = threading.Event()
        self.setDaemon(True)
        self.dat = None
        self.inputStarted = False
        self.ver = 0.1

    def init_serial(self):
        # allows use of the port as a prefix!
        list_ports = glob.glob("{}*".format(self.port))
        if not list_ports:
            raise Exception("Init failed - no valid port prefixes found") 
        port = list_ports[0]        
        logging.warn("Starting comms on port: {}".format(port))  
        self.ser = serial.Serial(port, self.baudrate)
        self.ser.timeout = 1

    def run(self):
        self.logger.debug('Serial reader running')
        dataIn = False
        while not self.stoprequest.isSet():
            try:
                
                if not self.isOpen():
                    self.connectForStream()

                while self.keepAlive:
                    dat = self.ser.readline()
                    # some data validation goes here before adding to Queue...
                    if len(dat) > 2:
                        self.dataQ.put([time.time(), dat])
                    if not self.inputStarted:
                        self.logger.debug('reading')
                    self.inputStarted = True
                    
            except serial.serialutil.SerialException, se:                       
                msg = 'Comms error, retrying..{}'.format(se)
                time.sleep(2)
                logging.warn(msg)
                try:
                    self.ser.close()
                except Exception, e:
                    logging.warn(e)                
                try:
                    self.init_serial()                    
                except Exception, e:
                    logging.warn(e)
                  
                
            # wait between retries
            time.sleep(4)
  
        self.dat.close()
        self.close()
        self.join_fin()

    def join_fin(self):
        self.logger.debug('stopping')
        self.stoprequest.set()

    def isOpen(self):
        self.logger.debug('Open? ' + str(self.ser.isOpen()))
        return self.ser.isOpen()

    def open(self):
          self.ser.open()

    def stopDataAquisition(self):
        self.logger.debug('Setting keepAlive to False')
        self.keepAlive = False

    def close(self):
        self.logger.debug('closing')
        self.stopDataAquisition()
        self.ser.close()

    def write(self, msg):
        self.ser.write(msg)

    def readline(self):
        return self.ser.readline()

    def connectForStream(self, debug=True):
        '''Attempt to connect to the serial port and fail after waitMaxSec seconds'''
        self.logger.debug('connecting')
        if not self.isOpen():
          self.logger.debug('not open, trying to open')
          try:
            self.open()
          except serial.serialutil.SerialException:
            self.logger.debug('Unable to use port ' + str(self.ser.port) + ', please verify and try again')
            return
        while self.readline() == '' and self.readCount < self.waitMaxSec and self.keepAlive:
            self.logger.debug('reading initial')
            self.readCount += self.sleepDurSec
            if not self.readCount % (self.ser.baudrate / 100):
              self.logger.debug("Verifying MaxSonar data..")
              #//some sanity check

        if self.readCount >= self.waitMaxSec:
            self.logger.debug('Unable to read from serial port...')
            self.close()
            return False
        else:
          self.logger.debug('serial data is streaming...')

        return True

