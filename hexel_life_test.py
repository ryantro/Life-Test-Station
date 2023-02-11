# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 13:30:47 2022

@author: ryan.robinson
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 11:05:00 2022

@author: ryan.robinson
"""
# IMPORTS
import tkinter as tk
from tkinter import ttk
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import os
import stat
import pyodbc

# FOR READING CONFIG FILE
import configparser

# FOR UNIT TESTING
import random

# POWER METER
import power_meter

# SPECTRUM ANALYZER
import spectrum_analyzer

# STAGE CONTROL
import arduino

# Laser drivers
import current_supply

# RELAY CONTROL
import relay_control

# Constants
HEXELS = 3
MODULES = 2

"""
TODO:
    - Config file parsing
    - Connect to stage
    - Connect to laser driver
    - Save data structure
    - Connect to DAQ

"""

class DeviceAddrs:
     cs1 = 'COM3'
     cs2 = 'COM5'
     cs3 = 'COM8'
     cs4 = 'COM6'
     cs5 = 'COM7'
     
     osa = 'HR4D3341'
     ard = 'COM4'
     pm  = 'USB0::0x1313::0x8076::M00808684'
     
     r1 = 'COM12'
     r2 = 'COM11'
     r3 = 'COM10'
     r4 = 'COM9'
     r5 = 'COM13'
     
"""
Object to hold config file information for an individual hexel.
"""
class HexelVars:
    def __init__(self):
        # Serial number for hexel
        self.ser = None
        
        # Stage position for hexel
        self.pos = None
        
        # Integration time for hexel
        self.dur = None    
        return

"""
Object to hold config file information for a module.

For the HLT, each module holds 3 hexels.
"""
class ModuleVars:
    def __init__(self):
        self.n = None
        
        # Create an empty list to hold an arbitrary number of hexel objects
        self.hexels = []
        for i in range(0,HEXELS):
            self.hexels.append(HexelVars())
        return

"""
Object to hold config file information for the station.

For Dallens setup, each station holds 2 modules.
"""
class HltVars:
    def __init__(self):
        """
        Data get loaded in on initilization of object.
        """
        # Create an empty list to hold arbitrary number of hexel  module objects
        self.modules = []
        for i in range(0,MODULES):
            self.modules.append(ModuleVars())
        
        # Load the config file
        self.loadConfigFile()
        
        return
    
    def loadConfigFile(self):
        """
        Load the config file with all the data 
        """
        self.filename = 'hexel_settings.cfg'
        
        # Creat the config parser object
        self.config = configparser.ConfigParser()
        
        # Load the object with the config file
        self.config.read(self.filename)
        
        # Fill out the empty objects
        for i in range(0,MODULES):
            
            for j in range(0,HEXELS):
                
                # Load data from config file to temp variables
                ser = self.config['MODULE {}'.format(i)]['hexel {}'.format(j)]
                pos = self.config['MODULE {}'.format(i)]['hexel {} position'.format(j)]
                dur = self.config['MODULE {}'.format(i)]['hexel {} integration time'.format(j)]
                
                # Convert strings to integers and fillout objects
                self.modules[i].hexels[j].ser = int(ser)
                self.modules[i].hexels[j].pos = int(pos)
                self.modules[i].hexels[j].dur = int(dur)
        
        return
    
    def saveConfigFile(self):
        """
        Save the values into the config file.
        """
        for i in range(0,MODULES):
            
            for j in range(0,HEXELS):
                
                # Load data from config file to temp variables
                self.config.set('MODULE {}'.format(i), 'hexel {}'.format(j),                  str(self.modules[i].hexels[j].ser))
                self.config.set('MODULE {}'.format(i), 'hexel {} position'.format(j),         str(self.modules[i].hexels[j].pos))
                self.config.set('MODULE {}'.format(i), 'hexel {} integration time'.format(j), str(self.modules[i].hexels[j].dur))
        
        f = open(self.filename, 'w')
        self.config.write(f)
        
        return
        
class Status:
    devices = True
    interlock = True
    flow = True

"""
The device manager class handles connecting and closing all devices used
in the station!
"""
class DeviceManager:
    
    stage = None
    stageConnect = False
    
    pm = None
    pmConnect = False
    
    osa = None
    osaConnect = False
    
    ld1 = None
    ld1Connect = False
    
    ld2 = None
    ld2Connect = False
    
    lds = [ld1, ld2]
    ldsConnect = [ld1Connect, ld2Connect]
    
    addrs = DeviceAddrs()
    
    def connectDevices(self):
        """
        Method to connect all devices
        """
        # Try to connect to the stage
        print("Trying to connect to stage...")
        if(self.stageConnect == False):
            try:
                self.stage = arduino.Stage(self.devices.ard)
                self.stageConnect = True
                print("...Stage connection established!")
                # TODO: should stage be zero'd here?
                
            except:
                self.stageConnect = False
                print("...Stage connection failed :(")
        
        # Try to connect to the power meter
        print("Trying to connect to powermeter...")
        if(self.pmConnect == False):
            try:
                self.pm = power_meter.PowerMeter(usbaddr = self.devices.pm)
                self.pmConnect = True
                print("...Powermeter connection established!")
                
            except:
                self.pmConnect = False
                print("...Powermeter connection failed :(")
            
        # Try to connect to the OSA
        print("Trying to connect to the OSA...")
        if(self.osaConnect == False):
            try:
                self.osa = spectrum_analyzer.SpectrumAnalyzer() # Create OSA object
                self.osa.connect(integration_time = 1500)       # Connect OSA object to OSA
                self.osaConnect = True
                print("...OSA connection established!")
                
            except:
                self.osaConnect = False
                print("...OSA connection failed :(")
        
        # Try to connect to the laser drivers
        i = 0
        for ld in self.lds:
            print("Trying to connect to laser driver {}".format(i+1))
            
            try:
                ld = current_supply.PS2000B(self.devices.cs[i])
                self.ldsConnect[i] = True
                print("...Connection to laser driver {} established!".format(i+1))
                
                # Configure laser drivers
                ld.enable_remote_control()
                ld.disable_output()
                ld.set_voltage(100)
                ld.set_current(0)
                ld.enable_output()
                
            except:
                self.ldsConnect[i] = False
                print("...Laser driver {} connection failed :(".format(i+1))
            
            i = i + 1
        
        return
    
    def closeDevices(self):
        """
        Method to close all devices
        """
        # Close the laser drivers
        # print("Trying to close laser drivers...")
        i = 0
        for ld in self.lds:
            if(self.ldsConnect[i] == True):
                print("Trying to close laser driver {}".format(i+1))
                
                try:
                    ld.set_current(0)
                    ld.disable_output()
                    ld.close()
                    self.ldsConnect[i] = False
                    print("...Laser driver {} closed!".format(i+1))
                    
                except:
                    print("...Laser driver {} failed to close :(".format(i+1))
            i = i + 1
        
        # Close the stage
        if(self.stageConnect == True):
            print("Trying to close stage...")
            try:
                self.stage.close()
                self.stageConnect = False
                print("...Stage closed!")
            except:
                print("...Failed to close stage :(")
        
        # Close the powermeter
        if(self.pmConnect == True):
            print("Trying to close powermeter")
            try:
                self.pm.close()
                self.pmConnect = False
                print("...Powermeter closed!")
                
            except:
                print("...Failed to close powermeter :(")
        
        # Close the OSA
        if(self.osaConnect == True):
            print("Trying to close the OSA...")
            try:
                self.osa.close()
                self.osaConnect = False
                print("...OSA closed!")
                
            except:
                print("...Failed to close OSA")
        
        return
    
    def allConnected(self):
        """
        Method used to verify that all devices are connected
        """
    
        self.stageConnect
        
        self.pmConnect
        
        self.osaConnect
   
        self.ldsConnect

        
        return True




"""
This class just links the devices to the lower level classes.

Each module has a unique laser driver but shares the same stage, powermeter,
and osa
"""
class Devices:
    stage = None
    stageConnect = False
    
    pm = None
    pmConnect = False
    
    osa = None
    osaConnect = False
    
    ld = None
    ldConnect = False
    
    def connectDevices(self, deviceManager, n):
        """
        Link deviceManager object to device object
        """
        
        self.stage = deviceManager.stage
        self.stageConnect = deviceManager.stageConnect
        
        self.pm = deviceManager.pm
        self.pmConnect = deviceManager.pmConnect
        
        self.osa = deviceManager.osa
        self.osaConnect = deviceManager.osaConnect
        
        self.ld = deviceManager.ld[n]
        self.ldConnect = deviceManager.ldConnect[n]
          
        return



"""
Class to handle storing and saving important values

Should methods to read powermeter be called in here?

"""
class Values:
    power = 0   # power
    wl = 0      # wavelength
    lw = 0      # linewidth
    sk = 0      # skew
    kt = 0      # kurtosis
    c  = 0      # current
    es = [True, True, True, True, True, True]
    vt = 0      # voltage drop
    text = ""
    firstSave = True
    
    def reset(self):
        """
        Reset all the values
        """
        self.power = 0
        self.wl = 0
        self.lw = 0
        self.sk = 0
        self.kt = 0
        self.c  = 0
        self.es = [True, True, True, True, True, True]
        self.vt = 0
        self.text = ""
        self.firstSave = True
        return
    
    def genEsStr(self):
        a = []
        for i in range(0,len(self.es)):
            if(self.es[i] == True):
                a.append("e{}".format(i+1))
        
        b = ":".join(a)
        c = "({})".format(b)
        return c
                
    def sqlsave(self):
        # save data to sql server
        cnxn = pyodbc.connect('Driver={SQL Server Native Client 11.0};Server=NSQL\LASERPRODUCTION;Database=CosModules;Trusted_Connection=yes;')
        #cnxn = pyodbc.connect('DSN=test;PWD=password')
        cursor = cnxn.cursor()
        cursor.execute("INSERT INTO ([CosModules].[dbo].[SETS] ([Operator], [hexelSN], [Step], [CentralWL],  [Dt])) VALUES( 'self.power ','self.wl','self.lw','self.sk','self.kt','self.c','esstr','self.vt')")
        cnxn.commit()
        cnxn.close()
        return
    
    def save(self, title):
        """ Save file """
        t = time.time()
        esstr = self.genEsStr()
        saveline = "{}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(t, self.power, self.wl, self.lw, self.sk, self.kt, self.c, esstr, self.vt)
        os.makedirs(os.path.dirname(title), exist_ok=True)
        
        if(os.path.exists(title)):
            os.chmod(title, stat.S_IWRITE) # Make read/write
            
        with open(title, 'a') as file_obj:
            file_obj.write(saveline)
            
        os.chmod(title, stat.S_IREAD) # Make read only
        
        return

"""
Hexel Life Test class. Backend class for Life Test Station.

Holds objects for HLT modules and station status.
"""
class HexelLifeTest:
    def __init__(self):
        
        # Open config file for hexel settings
        self.hltVars = HltVars()
        
        # Create object to handle connecting and disconnecting the devices
        self.deviceManager = DeviceManager()
        
        # Create object for modules
        # TODO: Make the abstract for N-number of modules

        
        self.MS = []
        for i in range(0,MODULES):
            self.MS.append(Module(self.hltVars.modules[i]))
        
        # Create an event for stopping the program
        self.event = threading.Event()
        
        self.thread = threading.Thread(target = self.run, daemon = True)
        
        return
    
    def start(self):
        """
        Create the thread and run it if it isn't currently being ran.
        """
        if(self.thread.is_alive() == False and self.event.is_set() == False):
            
            self.thread = threading.Thread(target = self.run, daemon = True)
            
            self.thread.start()
            
            return True
        
        return False
    
    def run(self):
        """
        Run the Hexel Life Test.
        """
        # Time to wait between measurements
        t_wait = 5
        
        while(self.event.is_set() == False):
            
            # Scan through HLT modules
            for M in self.MS:
                
                # Check for stop flag
                if(self.event.is_set()):
                    break
                
                # Scan through HLT hexels
                for H in M.HS:
                    
                    # Delay block
                    tstart = time.time()                
                    while(time.time() - tstart < t_wait):
                        # print("Waiting...")
                        time.sleep(0.5)
                        
                        # Check for stop flag
                        if(self.event.is_set()):
                            break
                    
                    # Move to and measure the hexel
                    H.moveAndMeasure()
                    
                    # Save here
                    
                    # Check for stop flag
                    if(self.event.is_set()):
                        break
        
        self.event.clear()
        
        return
    
    def stop(self):
        """
        Method to stop the HLT
        """
        # Raise event flag to kill thread
        self.event.set()
        
        # Wait till thread dies
        while(self.thread.is_alive() == True):
            print('Waiting for thread to die....')
            time.sleep(1)
        
        print('Thread dead')
        return True
    
    def on_closing(self):
        """
        Define things to do on application closing
        """
        self.hltVars.saveConfigFile()
        
        return

"""
Class to represent a Hexel Life Test module. Each module consists of 3 hexels
"""
class Module:
    def __init__(self, mVars):
        
        self.mVars = mVars
        
        self.HS = []
        for i in range(0,HEXELS):
            self.HS.append(Hexel(self.mVars.hexels[i]))
            
        # self.H1 = Hexel()
        # self.H2 = Hexel()
        # self.H3 = Hexel()
        # self.HS = [self.H1, self.H2, self.H3]
        self.cycled = False
        self.enabled = True
        return
    
    def turnOn(self):
        # TODO: turn on laser driver
        return
    
    def turnOff(self):
        # TODO: turn off the laser
        return
    
    def measure(self):
        # TODO: measure all 3 hexels in a module
        # Move and measure all devices
        """
        Measurement needs to be managed by higher level class for timing
        """
        for H in self.HS:    
            H.moveAndMeasure()
        return

class Hexel:
    def __init__(self, hVars):
        self.pos = 0                # Hexel position
        self.val = Values()         # Create values object, holds all recorded data
        self.devices = Devices()    # Devices object
        self.hVars = hVars
        
        return
    
    def attachDevices(self, stage, pm, osa, ld):
        """
        Link devices to hexel object.
        """
        self.devices.connectStage(stage)    # Link stage
        self.devices.connectPM(pm)          # Link powermeter
        self.devices.connectOSA(osa)        # Link OSA
        self.devices.connectLD(ld)          # Link laser driver
        
        return
    
    def moveAndMeasure(self):
        """
        Move the stage and measure spectrum/power.
        """
        """
        self.moveTo()           # Move stage to hexel positon
        self.measureSpectrum()  # Measure spectrum of hexel
        self.measurePower()     # Measure power of hexel
        """
        print("moveAndMeasure()")
        return
    
    def measurePower(self):
        """
        Measure power and update values object.
        """
        self.val.power = self.devices.pm.getPower2() # Get the power
        return
    
    def measureSpectrum(self):
        """
        Measure spectrum and update values object.
        """
        # Measure the spectrum
        self.devices.osa.measureSpectrum()
    
        # Find statistics from the spectrum
        results = self.devices.osa.findStatistics()
        self.val.wl = results[0] # mean wavelength
        self.val.lw = results[1] # line width
        self.val.sk = results[2] # skew
        self.val.kt = results[3] # kurtosis

        return
    
    def moveTo(self):
        """
        Move the stage to the hexel position
        """
        # self.devices.stage.moveAbs(self.pos)
        print("Moving stage to ...")
        return


"""
Hexel Life Test Station Box class. The GUI for the Hexel Lift Test Station.
"""
class HexelLifeTestBox:
    def __init__(self, top):
        
        self.top = top
        
        # Configure title
        self.top.title('H.L.T. - Hexel Life Test')
        
        # ON APPLICAITON CLOSING
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create module frame and define grid structure
        self.master = tk.Frame(top)
        self.master.rowconfigure([0], minsize=5, weight=1)
        self.master.columnconfigure([0, 1], minsize=5, weight=1)
        self.master.grid(row = 0, column = 0)        
        
        # LASER MODULES
        self.mFrames = tk.Frame(self.master)
        self.mFrames.columnconfigure([0], minsize=10, weight=1)
        self.mFrames.grid(row = 0, column = 0, padx = 5, pady = (5,0), sticky = "EW")
        
        # Create HLT backend object
        self.HLT = HexelLifeTest()
        
        # Create module boxes
        self.Ms = []
        # i = 0
        # for M in self.HLT.MS:
        #     self.Ms.append(ModuleBox(self.mFrames, i, Module()))
        #     i = i + 1
        
        for i in range(0, MODULES):
            self.Ms.append(ModuleBox(self.mFrames, i, self.HLT.MS[i]))
            
        
        # Generate frame for enable/disable box
        self.stateframe = tk.Frame(self.master, borderwidth = 2,relief="groove")
        self.stateframe.columnconfigure([0, 1], minsize=50, weight=1)
        self.stateframe.rowconfigure([0], minsize=50, weight=1)
        self.stateframe.grid(row = 1, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "EW")
        
        # Create enable/disable label
        self.statelabel = tk.Label(self.stateframe, text=" RECORDING OFF ", bg = '#84e47e', font = ('Ariel 15'))
        self.statelabel.grid(row = 0, column = 1, padx = 0, pady = 0, sticky = "NSEW")
        
        # Create enable/disable button
        self.stateButton = tk.Button(self.stateframe, text="START", command=self.stateEnable, font = ('Ariel 15'))
        self.stateButton.grid(row = 0, column = 0, padx = 0, pady = 0, sticky = "NSEW")
        
        # Create options block
        self.rFrame = tk.Frame(self.master, borderwidth = 2, relief = "groove")
        self.rFrame.grid(row = 0, column = 1, padx = (0,5), pady = 5, sticky = "EWN")
        
        # Create GUI object for managing devices
        self.dmBox = DeviceManagerBox(self.rFrame, self.HLT.deviceManager)
        
        return

    def updateVars(self):
        for i in range(0, MODULES):
            for j in range(0, HEXELS):
                self.Ms[i].HBS[j].updateVars()
                

    def stateEnable(self):
        """ ENABLE THE STATE """
        
        # Start thread and check that it's started
        started = self.HLT.start()
        if(started == False):
            return
        
        # CONFIGURE LABEL
        self.statelabel = tk.Label(self.stateframe, text = "CURRENTLY RECORDING", bg = '#F55e65', font = ('Ariel 15'))
        self.statelabel.grid(row = 0, column = 0, padx = 0, pady = 0, sticky = "NSEW")    
        
        # CONFIGURE BUTTON
        self.stateButton = tk.Button(self.stateframe, text="STOP", command=self.stateDisable, font = ('Ariel 15'))
        self.stateButton.grid(row = 0, column = 1, padx = 0, pady = 0, sticky = "NSEW")
        
        return
        
    def stateDisable(self):
        """ DISABLE THE STATE """
        
        # Stop the thread and check that it's stopped
        stopped = self.HLT.stop()
        if(stopped == False):
            return
        
        # CONFIGURE STATE LABEL
        self.statelabel = tk.Label(self.stateframe, text=" RECORDING OFF ", bg = '#84e47e', font = ('Ariel 15'))
        self.statelabel.grid(row = 0, column = 1, padx = 0, pady = 0, sticky = "NSEW")
        
        # CONFIGURE STATE BUTTON
        self.stateButton = tk.Button(self.stateframe, text="START", command=self.stateEnable, font = ('Ariel 15'))
        self.stateButton.grid(row = 0, column = 0, padx = 0, pady = 0, sticky = "NSEW")
        
        return

    def on_closing(self):
        """ EXIT THE APPLICATION """
        
        # PROMPT DIALOG BOX
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
                        
            # self.closeDevices()
            self.stateDisable()
            
            # Close all devices
            self.dmBox.disconnect()
            
            # Save entry box values in config file
            self.updateVars()
            
            # Call backend closing method
            self.HLT.on_closing()
            
            # DESTROY APPLICATION
            self.top.destroy()
            
        return

"""
Class to handle the GUI for connecting devices
"""
class DeviceManagerBox:
    def __init__(self, master, deviceManager):
        
        # Save parent frame to object and configure rows/cols
        self.master = master
        self.master.rowconfigure([0], minsize=5, weight=1)
        self.master.columnconfigure([0], minsize=5, weight=1)
    
        # Frame to show device status and connect/disconnect buttons
        self.deviceFrame = tk.Frame(self.master, borderwidth = 2, relief = "groove")
        self.deviceFrame.grid(row = 0, column = 0, padx = 1, pady = 1, sticky = "EWN")
    
        # Link devices object to current object
        self.deviceManager = deviceManager
    
        # Button to connect all devices
        self.connectButton = tk.Button(self.deviceFrame, text = 'Connect All Devices', command = self.connect, font = ('Ariel 8'))
        self.connectButton.grid(row = 0, column = 0, sticky = "EW")
    
        # Generate str list for all devices
        self.devicesStr = ['Stage', 'Power Meter', 'OSA']
        laserDrivers = 2
        for i in range(0,laserDrivers):
            self.devicesStr.append('Laser Driver {}'.format(i+1))
    
        # Labels for device connection status
        self.deviceLabels = []
        for i in range(0, len(self.devicesStr)):
            self.deviceLabels.append(tk.Label(self.deviceFrame, text = self.devicesStr[i], bg = '#F55e65', borderwidth = 2,relief="groove"))
            self.deviceLabels[-1].grid(row = i+1, sticky = "EW")
    
        # Button to connect all devices
        self.disconnectButton = tk.Button(self.deviceFrame, text = 'Disconnect All Devices', command = self.disconnect, font = ('Ariel 8'))
        self.disconnectButton.grid(row = len(self.deviceLabels)+1, column = 0, sticky = "EW")    
        self.disconnectButton.configure(state = 'disabled')
    
        # Frame to operate devices
        self.instrumentFrame = tk.Frame(self.master, borderwidth = 2, relief = "groove")
        self.instrumentFrame.grid(row = 1, column = 0, padx = 1, pady = 1, sticky = "EWN")
        
        # Button to view spetrometer
        self.specViewButton = tk.Button(self.instrumentFrame, text = 'View OSA', command = self.viewSpec, font = ('Ariel 8'))
        self.specViewButton.grid(row = 0, column = 0, sticky = "EW")
        
        # Popup window for spetrometer
        self.specWindow = None
        
        # Create the event to stop the plotting
        self.event = threading.Event()
        
        return
    
    def connect(self):
        """
        Method to connect all devices
        """
        # Color to indicate connected device
        bg = '#84e47e'
        
        # Call device manager to open all devices
        self.deviceManager.connectDevices()
        
        # Allow the disconnect button to be pressed
        self.disconnectButton.configure(state = 'normal')
        
        # Report if connected has been connected in GUI
        if(self.deviceManager.stageConnect == True):
            self.deviceLabels[0].configure(bg = bg)
        
        # Report if powermeter has been connected in GUI
        if(self.deviceManager.pmConnect == True):
            self.deviceLabels[1].configure(bg = bg)
        
        # Report if osa has been connected in GUI
        if(self.deviceManager.osaConnect == True):
            self.deviceLabels[2].configure(bg = bg)
            
        # Report if laser drives have been connected in GUI
        for i in range(0, len(self.deviceManager.lds)):
            if(self.deviceManager.ldsConnect[i] == True):
                self.deviceLabels[3+i].configure(bg = bg) # 3 + i may cause issues later?
            
        return

    def disconnect(self):
        """
        Method to disconnect all devices
        """
        # Color to indicate disconnected device
        bg = '#F55e65'
        
        # Stop the measurements
        self.event = threading.Event()
        
        # Call device manager to close all devices
        self.deviceManager.closeDevices()
        
        # Allow the disconnect button to be pressed
        self.disconnectButton.configure(state = 'disabled')
        
        # Report if stage has been disconnected in GUI
        if(self.deviceManager.stageConnect == False):
            self.deviceLabels[0].configure(bg = bg)
            
        # Report if powermeter has been disconnected in GUI
        if(self.deviceManager.pmConnect == False):
            self.deviceLabels[1].configure(bg = bg)
        
        # Report if osa has been disconnected in GUI
        if(self.deviceManager.osaConnect == False):
            self.deviceLabels[2].configure(bg = bg)
            
        # Report if laser drives have been disconnected in GUI
        for i in range(0, len(self.deviceManager.lds)):
            if(self.deviceManager.ldsConnect[i] == False):
                self.deviceLabels[3+i].configure(bg = bg) # 3 + i may cause issues later?
    
        return

    def viewSpec(self):
        """
        Method to open and view the spectrometer
        """
        # Check if osa is connected
        if(self.deviceManager.osaConnect == True):
            # Open a window if there isn't already a window opened
            if(self.specWindow == None or not self.specWindow.winfo_exists()):
                self.specWindow = tk.Toplevel(self.master)
                self.specWindow.rowconfigure([0], minsize=5, weight=1)
                self.specWindow.columnconfigure([0], minsize=5, weight=1)
                self.specWindow.title("Optical Spectrum Analyzer")
                
                # Create spectrometer window object
                A = SpecWindow(self.specWindow, self.deviceManager.osa, self.event)
                
        else:
            print("OSA is not connected!")
            
        
        return

# TODO: Program breaks if it is closed while looping methods are running.
# Program needs to check that threads are finished before closing devices

"""
Class for the spetrometer window
"""
class SpecWindow:
    def __init__(self, master, spec, event):
        
        # Link to the master window
        self.master = master
        
        # On window closing
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Link the osa
        self.osa = spec
        
        # Event
        self.event = event
        
        # Frame for spectrometer plot        
        self.specPlot = tk.Frame(self.master)
        self.specPlot.grid(row = 0, column = 0, sticky = "EWNS")
        
        # Frame for buttons
        self.buttonFrame = tk.Frame(self.master)
        self.buttonFrame.grid(row = 1, column = 0, sticky = "EW")
        
        # Create measure button
        self.measureButton = tk.Button(self.buttonFrame, text="Measure", command=self.measureAndPlot, font = ('Ariel 15'))
        self.measureButton.grid(row = 0, column = 0, sticky = "EW")
        
        # Creat continuous run button
        self.contRunButton = tk.Button(self.buttonFrame, text = "Start Realtime Plotting", command = self.contRun, font = ('Ariel 15'))
        self.contRunButton.grid(row = 0, column = 1, sticky = "EW")
        
        self.stopButton = tk.Button(self.buttonFrame, text = "Stop Realtime Plotting", command = self.stopRun, font = ('Ariel 15'))
        self.stopButton.grid(row = 0, column = 2, sticky = "EW")
        
        # Measure the spectrum
        self.osa.measureSpectrum()
        
        # Take a single measurement
        X, Y = self.osa.getData()
        
        # Create a figure
        self.fig = Figure(figsize = (5, 5), dpi = 100)
        
        # Create a plot
        self.plot1 = self.fig.add_subplot(111)
        
        # Plot the spetrometer data
        self.plot1.plot(X, Y)
        
        # Plot formatting
        self.plot1.axis(ymin = 0, ymax = 16500)
        self.plot1.grid('on')
        self.plot1.set_title("Runtime Plots", fontsize = 20)
        self.plot1.set_xlabel("Wavelength (nm)", fontsize = 15)
        
        # Create the canvas and insert the figure into it
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.specPlot)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
        
        # Create the thread for the plot loop
        self.thread = threading.Thread(target = self.plotLoop, daemon = True)
        
        return

    def measureAndPlot(self):
        """
        Measure the current spectrum and plot the results
        """
        # CLEAR PLOT
        self.plot1.clear()
        
        # Measure the spectrum
        self.osa.measureSpectrum()
        
        # Take a single measurement
        x, y = self.osa.getData()
        
        # Plot the spetrometer data
        self.plot1.plot(x, y)
        
        # Plot formatting
        self.plot1.axis(ymin = 0, ymax = 16500)
        self.plot1.set_title("Runtime Plots", fontsize = 20)
        self.plot1.set_xlabel("Wavelength (nm)", fontsize = 15)
        self.plot1.grid("on")
        
        # Draw the plot
        self.canvas.draw()
        
        # Close the figure
        plt.close(self.fig)
        
        return
    
    def contRun(self):
        """
        Method to create and start the thread for realtime plotting
        """
        # Create an event for stopping the program
        self.event.clear()
        
        # Create the thread for the plot loop
        if(self.thread.is_alive() == False):
            self.thread = threading.Thread(target = self.plotLoop, daemon = True)
            self.thread.start()
        
        return

    def stopRun(self):
        """
        Stop the realtime plotting
        """
        # Set the event to stop the thread
        self.event.set()
        
        return

    def plotLoop(self):
        """
        Method for realtime plotting
        """
        while(self.event.is_set() == False):
            self.measureAndPlot()
        
        return
    
    def on_closing(self):
        """
        When closing the window
        """
        # Set event to stop thread
        self.event.set()
        
        # Wait for thread to close
        if(self.thread.is_alive()):
            self.thread.join()

        
        # Destroy window
        self.master.destroy()
        
        return

class ModuleBox:
    def __init__(self, master, g, Module):
        
        # Link the Module object to this ModuleBox object
        self.Module = Module
        
        # Create module frame and define grid structure
        self.master = tk.Frame(master, borderwidth = 2, relief = "groove")
        self.master.rowconfigure([0, 1, 2], minsize=5, weight=1)
        self.master.columnconfigure([0], minsize=5, weight=1)
        self.master.grid(row = 0, column = g)
        
        # Module label
        self.moduleLabel = tk.Label(self.master, text = "Hexel Life Test Module {}".format(g+1), font = ('Ariel 15'))
        self.moduleLabel.grid(row = 0, column = 0, sticky = "W", padx = 5)
        
        # Create a frame for the HexelBox objects
        self.hbFrame = tk.Frame(self.master)
        self.hbFrame.rowconfigure([0], minsize=5, weight=1)
        self.hbFrame.columnconfigure([0, 1, 2], minsize=5, weight=1)
        self.hbFrame.grid(row = 1, column = 0)
        
        # Create the HexelBox GUI objects and link them with the Hexel objects
        self.HBS = []
        for i in range(0,len(self.Module.HS)):
            self.HBS.append(HexelBox(self.hbFrame, i, self.Module.HS[i]))
        
        # Label variable for module run time. 
        self.runTimeVar = tk.StringVar(self.master, value = "Runtime: Not started")
        self.runTimeLabel = tk.Label(self.master, textvariable = self.runTimeVar, font = ('Ariel 8'))
        self.runTimeLabel.grid(row = 2, column = 0, sticky = "W", padx = 5)
        
        # Set current label
        self.currentLabel = tk.Label(self.master, text = "Set Current (A):", font = ('Ariel 12'))
        self.currentLabel.grid(row = 3, column = 0, sticky = "W", padx = 5)
        
        # Set current entry box
        self.currentEntry = tk.Entry(self.master, width = 10, font = ('Ariel 12'))
        self.currentEntry.grid(row = 4, column = 0, sticky = "EW", padx = 5)
        self.currentEntry.insert(0, 3.3)
         
        # Set current label
        self.notesLabel = tk.Label(self.master, text = "Notes:", font = ('Ariel 12'))
        self.notesLabel.grid(row = 5, column = 0, sticky = "W", padx = 5)
        
        # Set current entry box
        self.notesEntry = tk.Text(self.master, width = 10, height = 5, font = ('Ariel 12'))
        self.notesEntry.grid(row = 6, column = 0, sticky = "EW", padx = 5, pady = (0,5))
        # self.notesEntry.insert(0, "Put some notes here\ni.e. Hexel 1 sucks")
        
        # Button to find stage positions and OSA integration times
        self.calButton = tk.Button(self.master, text = 'Try to find each hexels stage position and osa integration time', command = self.calModule, font = ('Ariel 8'))
        self.calButton.grid(row = 7, column = 0, padx = 1, sticky = "EW")
        
        # Enable/disable box
        self.stateframe = tk.Frame(self.master, borderwidth = 2,relief="groove")
        self.stateframe.columnconfigure([0, 1], minsize=120, weight=1)
        self.stateframe.rowconfigure([0], minsize=5, weight=1)
        self.stateframe.grid(row = 8, column = 0, padx = 1, sticky = "EW")
        
        # state enable
        self.enabled = False
        self.disable()
        
        return 

    def calModule(self):
        print("This needs to be filled in")
        return

    def enable(self):
        """
        SET ENABLED STATE TO TRUE
        """
        # SET ENABLED STATE TO TRUE
        self.enabled = True
        
        # GENERATE ENABLE/DISABLE BUTTON
        self.stateButton = tk.Button(self.stateframe, text="DISABLE", command=self.disable, font = ('Ariel 8'))
        self.stateButton.grid(row = 0, column = 1, padx = 0, pady = 0, sticky = "NSEW")
        
        # GENERATE STATION STATUS BOX
        self.statelabel = tk.Label(self.stateframe, text=" MODULE ENABLED ", bg = '#F55e65', font = ('Ariel 8'))
        self.statelabel.grid(row = 0, column = 0, padx = 0, pady = 0, sticky = "NSEW")
        
        # Disable or enable entry boxes
        for H in self.HBS:
            H.enable()
        
        self.currentEntry.configure(state = 'disabled')
        self.notesEntry.configure(state = 'disabled')
        self.calButton.configure(state = 'normal')
        
        return
    
    def disable(self):
        """
        SET ENABLED STATE TO FALSE
        """
        # self.turnOff()
        
        # SET ENABLED STATE TO FALSE
        self.enabled = False
        
        # GENERATE ENABLE/DISABLE BUTTON
        self.stateButton = tk.Button(self.stateframe, text="ENABLE", command=self.enable, font = ('Ariel 8'))
        self.stateButton.grid(row = 0, column = 0, padx = 0, pady = 0, sticky = "NSEW")
        
        # GENERATE STATION STATUS BOX
        self.statelabel = tk.Label(self.stateframe, text=" MODULE DISABLED ", bg = '#84e47e', font = ('Ariel 8'))
        self.statelabel.grid(row = 0, column = 1, padx = 0, pady = 0, sticky = "NSEW")
        
        # Disable or enable entry boxes
        for H in self.HBS:
            H.disable()
        self.currentEntry.configure(state = 'normal')
        self.notesEntry.configure(state = 'normal')
        self.calButton.configure(state = 'disabled')
        
        return


class HexelBox:
    def __init__(self, master, g, Hexel):
        
        # Link to backend object
        self.hexel = Hexel 
        
        # Create module frame and define grid structure
        self.master = tk.Frame(master, borderwidth = 2, relief = "groove")
        self.master.rowconfigure([0], minsize=5, weight=1)
        self.master.columnconfigure([0], minsize=5, weight=1)
        self.master.grid(row = 0, column = g)
        
        # Hexel Label
        self.moduleLabel = tk.Label(self.master, text = "Hexel Serial:", font = ('Ariel 10'))
        self.moduleLabel.grid(row = 0, column = 0, sticky = "W", padx = 5)
        
        # Hexel Serial Entry Box
        self.serEntry = tk.Entry(self.master, width = 10, font = ('Ariel 10'))
        self.serEntry.grid(row = 1, column = 0, sticky = "EW", padx = 5)
        self.serEntry.insert(0, self.hexel.hVars.ser)
        
        # Hexel Label
        self.stagePosLabel = tk.Label(self.master, text = "Stage Position:", font = ('Ariel 10'))
        self.stagePosLabel.grid(row = 2, column = 0, sticky = "W", padx = 5)
        
        # Hexel Serial Entry Box 
        self.stagePosEntry = tk.Entry(self.master, width = 10, font = ('Ariel 10'))
        self.stagePosEntry.grid(row = 3, column = 0, sticky = "EW", padx = 5)
        self.stagePosEntry.insert(0, self.hexel.hVars.pos)

        # Hexel Label
        self.intTimeLabel = tk.Label(self.master, text = "OSA Integration Time (us):", font = ('Ariel 10'))
        self.intTimeLabel.grid(row = 4, column = 0, sticky = "W", padx = 5)
        
        # Hexel Serial Entry Box
        self.intTimeEntry = tk.Entry(self.master, width = 10, font = ('Ariel 10'))
        self.intTimeEntry.grid(row = 5, column = 0, sticky = "EW", padx = 5, pady = (0,5))
        self.intTimeEntry.insert(0, self.hexel.hVars.dur)
        
        # Move stage button
        self.moveButton = tk.Button(self.master, text="Move Stage", command=self.moveStage, font = ('Ariel 8'))
        self.moveButton.grid(row = 6, column = 0, columnspan = 3, padx = 0, sticky = "EW")
        
        # Move stage button
        self.singleButton = tk.Button(self.master, text="Measure Single", command=self.measureSingle, font = ('Ariel 8'))
        self.singleButton.grid(row = 7, column = 0, columnspan = 3, padx = 0, sticky = "EW")
        
        # Most recent power measurement label
        pStr = "Power: {:.4f} W".format(0)
        self.pVar = tk.StringVar(self.master, value = pStr)
        self.pM = tk.Label(self.master, textvariable = self.pVar, font = ('Ariel 8'))
        self.pM.grid(row=8, column=0, sticky = "w", padx = 5)
        
        # Most recent spectrum measurement label
        sStr = "Center WL: {:.4f} nm".format(0)
        self.sVar = tk.StringVar(self.master, value = sStr)
        self.sM = tk.Label(self.master, textvariable = self.sVar, font = ('Ariel 8'))
        self.sM.grid(row=9, column=0, sticky = "w", padx = 5)
        
        return

    def loadVars(self):
        """
        Load entry box values from vars object
        """
        self.serEntry.insert(0, self.hexel.vars.ser)
        self.stagePosEntry.insert(0, self.hexel.vars.pos)
        self.intTimeEntry.insert(0, self.hexel.vars.dur)
        return
    
    def updateVars(self):
        """
        Update vars object from entry box values
        """
        self.hexel.hVars.ser = int(self.serEntry.get())
        self.hexel.hVars.pos = int(self.stagePosEntry.get())
        self.hexel.hVars.dur = int(self.intTimeEntry.get())
        return

    def enable(self):
        """
        Enable the measurement, disable entry boxes
        """
        self.serEntry.configure(state = 'disabled')
        self.stagePosEntry.configure(state = 'disabled')
        self.stagePosEntry.configure(state = 'disabled')
        self.intTimeEntry.configure(state = 'disabled')
        self.moveButton.configure(state = 'normal')
        self.singleButton.configure(state = 'normal')
        
        return
    
    def disable(self):
        """
        Disable the measurement, enable entry boxes
        """
        self.serEntry.configure(state = 'normal')
        self.stagePosEntry.configure(state = 'normal')
        self.stagePosEntry.configure(state = 'normal')
        self.intTimeEntry.configure(state = 'normal')
        self.moveButton.configure(state = 'disabled')
        self.singleButton.configure(state = 'disabled')
        
        return

    def moveStage(self):
        """
        Move the stage to the defined coordinate
        """
        # TODO: complete this
        print("This needs to be filled in")
        return
    
    def measureSingle(self):
        """
        Measure just that hexel
        """
        # TODO: complete this
        print("This needs to be filled in")
        return
    
    def setParams(self):
        """
        Method to send GUI entries to backend object
        """
        ser = self.moduleFrame.get()
        pos = self.stagePosEntry.get()
        dur = self.intTimeEntry.get()
        
        self.hexel.vars.ser = int(ser)
        self.hexel.vars.pos = int(pos)
        self.hexel.vars.dur = int(dur)
        
        return

def main():
    """ MAIN THREAD """
    # CREATE ROOT TKINTER OBJECT
    root = tk.Tk()
    
    # CREATE APPLICATION
    app = HexelLifeTestBox(root)
    
    # RUN MAINLOOP
    root.mainloop()
    
    return


if __name__=="__main__":
    main()