# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 11:40:21 2022

@author: ryan.robinson
"""

# from typing_extensions import Self
import typing_extensions
import serial
import time
from zaber_motion import Units, Library
from zaber_motion.ascii import Connection

Library.enable_device_db_store()

def main():
    """ For unit testing. """
    
    comport = 'COM10'
    S = Stage(comport)

    try:
        S.relmove(2000)
        time.sleep(1)
        S.move(10000)
        time.sleep(1)
        S.zero()
        print("test")
    finally:
        S.close()
    return
    
class Stage(serial.Serial):
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
    
    def move(self, pos):
        """ Sends a command to move the stage to a coordinate """
        print("Moving stage to coordinate: {}".format(pos))
        self.write('<MOVEABS {}>'.format(pos).encode()) # Write serial command
        return self.readline()
    
    def relmove(self, relpos):
        """ Sends a command to move the stage by a relative movement """
        print("Moving stage by relative amount: {}".format(relpos))
        self.write('<MOVEREL {}>'.format(relpos).encode()) # Write serial command
        return self.readline()
    
    def zero(self):
        """ Sends a command to zero the stage """
        print("Zero'ing the stage.")
        self.write('<ZERO>'.encode()) # Write serial command
        return self.readline()
    
    def close(self):
        """ Close the com port. """
        try:
            super().close()
        except Exception as e:
            self.setError("error closing port: {0}".format(e))
        except:
            self.setError("error closing port")
        return
    def Zaber_init(self, comport):
        with Connection.open_serial_port(comport) as connection:
            device_list = connection.detect_devices()
            device = device_list[0]
            self.axis = device.get_axis(1)
            if not self.axis.is_homed():
                self.axis.home()
        return

    def zaber_move(self, pos):
        # send command to move on absolute position
        self.axis.move_absolute(pos, Units.LENGTH_MILLIMETRES)

    def zaber_relmove(self, pos):
        # send command to move on relative position
        self.axis.move_relative(pos, Units.LENGTH_MILLIMETRES)
        return
    
if __name__=="__main__":
    main()