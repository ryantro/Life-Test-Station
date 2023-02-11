# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 11:40:21 2022

@author: ryan.robinson
"""

import serial
import time

def main():
    """ For unit testing. """
    
    comport = 'COM12'
    S = Relay(comport)
    E = [False, True, True, False, True, True]
    try:
        S.rOpen(1)
        time.sleep(4)
        for i in range(0,6):
            S.rOpenOnly(i+1)
            time.sleep(3)
            
            S.rOpenBool(E)
            time.sleep(1)
            
    finally:
        S.close()
    return
    
class Relay(serial.Serial):
    """ Class for controlling an arduino running the SETS firmware. """
    def __init__(self, comport):
        """ Initialization for the class, requires the comport. """
        super().__init__(comport)
        self.baudrate = 9600  # Set Baud rate to 9600
        self.bytesize = 8     # Number of data bits = 8
        self.parity   ='N'    # No parity
        self.stopbits = 1     # Number of Stop bits = 1
        time.sleep(3)         # Sleep 3 seconds for serial initilization
        return
    
    def rOpenBool(self, E):
        if(len(E) != 6):
            print("ERROR")
            return
        for i in range(0,len(E)):
            if(E[i] == True):
                self.rOpen(i+1)
            else:
                self.rClose(i+1)
    
    def rOpenOnly(self, i):
        self.write('<CLOSE 0>'.encode())
        self.write('<OPEN {}>'.format(i).encode())
        return
    
    
    def rClose(self, i):
        #print("Shorting emitter {}".format(i))
        self.write('<CLOSE {}>'.format(i).encode())
        return
    
    def rOpen(self, i):
        #print("Shorting emitter {}".format(i))
        self.write('<OPEN {}>'.format(i).encode())
        return
    
    def close(self):
        """ Close the com port. """
        try:
            super().close()
        except Exception as e:
            self.setError("error closing port: {0}".format(e))
        except:
            self.setError("error closing port")
        return
    
if __name__=="__main__":
    main()