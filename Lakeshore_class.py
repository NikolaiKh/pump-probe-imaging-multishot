import pyvisa
import re
import time

# Class is based on the file https://github.com/RickyZiegahn/Lakeshore-Cryostat-Controller
# by Richard Ziegahn
# It works with models 330, 336, 340,
# testsed with 340 only, connected via GPIB

# COM port settings from original file of Richard Ziegahn:
# gpibport = 5
# ser = serial.Serial(port=pname,baudrate=57600,parity='O',bytesize=7,timeout=1)
# sleeptime = 10

class Lakeshore:
    def __init__(self, gpibport):
        rm = pyvisa.ResourceManager()
        self.lakeshore = rm.open_resource(f'GPIB0::{gpibport}::INSTR')
        self.name = self.lakeshore.query('*IDN?')        
        rlist = self.name.split(',')
        self.model = rlist[1]
        self.state = f'Lakeshore is connected. Model {self.model}'


    def query(self,string):
        '''
        Asks for data then returns the response
        '''
        if self.model == 'MODEL330':
            read = self.lakeshore.query(string + '\n')
            # while ser.inWaiting() != 0:
            #     ser.readline()
            return read
        if self.model == 'MODEL336':
            self.lakeshore.write(string + '\n')
            return self.lakeshore.readline()

    def set_setpoint(self, temperature, loop='1'):
        '''
        Gives the controller the desired temperature
        330: INPUT: SETP[set point]
        340: INPUT: SETP <loop>,<value>
        336: INPUT: SETP <output>,<value>
        Loop and output are the same thing: the temperature
        '''
        if self.model == 'MODEL330':
            temperature = round(float(temperature),2)
            self.lakeshore.write('SETP' + str(temperature) + '\n')
        if self.model == 'MODEL340' or self.model == 'MODEL336':
            temperature = round(float(temperature),3)
            self.lakeshore.write('SETP ' + str(loop) + ', ' + str(temperature) + '\n')

    def query_setpoint(self, loop='1'):
        '''
        Returns the previous desired temperature
        330: INPUT: SETP?
             RETURN: <value>
        340: INPUT SETP? <loop>
             RETURN: <value>
        336: INPUT SETP? <output>
             RETURN: <value>
        Loop and output are the same thing
        '''
        if self.model == 'MODEL330':
            rstr = self.lakeshore.query('SETP? ')
            rstr = rstr[0:len(rstr)-2]
            return rstr
        elif self.model == 'MODEL340' or self.model == 'MODEL336':
            rstr = self.lakeshore.query('SETP? ' + str(loop))
            rstr = rstr[0:len(rstr)-2]
            return rstr

    def query_heat(self, output='1'):
        '''
        Returns a heater output in percentage.
        330: INPUT: HEAT?
             RETURN: <heater value> #increments of 5%
        340: INPUT: HTR?
             RETURN: <heater value>
        336: INPUT:HTR? <output>
             RETURN: <heater value>
        '''
        if self.model == 'MODEL330':
            rstr = self.lakeshore.query('HEAT? ')
            rstr = rstr[0:len(rstr)-2]
            return rstr
        elif self.model == 'MODEL340' or self.model == 'MODEL336':
            rstr = self.lakeshore.query('HTR? ' + output)
            rstr = rstr[0:len(rstr)-2]
            return rstr

    def set_heater_range(self, value_range, output='1'):
        '''
        Sets the range of the heater
        Value_range must be 0,1,2,3, or 5.
        330: INPUT: RANGE[heater range]
        0 is off, 1 is low, 2 is medium, 3 is high
        340: INPUT: RANGE <range>
        0 is off; 1 is 2.5mW; 2 is 25mW; 3 is 250mW; 4 is 2.5W; 5 is 25W
        336: INPUT: RANGE <output>,<range>
        For output 1: 0 is off; 1 is 0.1W; 2 is 10W; 3 is 100W
        For output 2: 0 is off; 1 is 0.5W; 2 is 5W; 3 is 50W
        '''
        if self.model == 'MODEL330':
            self.lakeshore.write('RANG' + value_range + '\n')
        elif self.model == 'MODEL340' or self.model == 'MODEL336':
            self.lakeshore.write('RANGE ' + output + ',' + value_range + '\n')

    def query_heater_range(self, output='1'):
        '''
        Returns the heater range.
        330: INPUT: RANG?
             RETURN: <range>
        340: INPUT: RANGE?
             RETURN: <range>
        336: INPUT: RANGE? <output>
             RETURN: <range>
        '''
        if self.model == 'MODEL330':
            rstr = self.lakeshore.query('RANG?')
            rstr = rstr[0:len(rstr)-2]
            return rstr
        elif self.model == 'MODEL340' or self.model == 'MODEL336':
            rstr = self.lakeshore.query('RANGE? ' + output)
            rstr = rstr[0:len(rstr)-2]
            return rstr

    def set_alarm(self, value_channel, on_off, value_high, value_low):
        '''
        Configures the alarm. If the temperature measured goes
        out of the high/low range, an alarm will be triggered. 
        Possible Value Channels are 'A' or 'B'.
        330: N/A
        340: INPUT: ALARM <input>, <off/on>, <source>, <high value>, <low value>, <latch enable>, <relay>
        336: INPUT: ALARM <input>,<off/on>,<high value>,<low value>,<deadband>,<latch enable>,<audible>,<visible>
        '''
        if self.model == 'MODEL340':
            self.lakeshore.write('ALARM ' + value_channel.upper() + ', ' + on_off + ', 1, ' + 
                      value_high + ', ' + value_low + '0,0\n')
        elif self.model == 'MODEL336':
            self.lakeshore.write('ALARM ' + value_channel.upper() + ',' + on_off + ',' + 
                      value_high + ',' + value_low + ',0,0,0,1\n')
        
    def query_alarm(self, value_channel):
        '''
        Returns a list of the alarm configeration
        Options of value channels are A/B
        330: N/A
        340: INPUT: ALARM? <input>
             RETURN: <off/on>, <source>, <high value>, <low value>, <latch enable>, <relay enable>
        336: INPUT: ALARM? <input>
             RETURN: <off/on>,<high value>,<low value>,<deadband>,<latch enable>,<audible>,<visible>
        '''
        if self.model == 'MODEL340':
            rstr = self.lakeshore.query('ALARM? ' + value_channel)
            rlisttemp = rstr.split(',')
            rlisttemp[2] = rlisttemp[2][1:(len(rlisttemp[2])-2)]
            rlisttemp[3] = rlisttemp[3][1:(len(rlisttemp[3])-2)]
            #item 0 is off/on; 1 is source; 2 is high value; 3 is low value; 
            #4 is latch enable; 5 is relay enable.
            #Create new list that has the parameters in the same 
            #order as the 336 list
            rlist = [rlisttemp[0],rlisttemp[2],rlisttemp[3]]
            return rlist
        elif self.model == 'MODEL336':
            rstr = self.lakeshore.query('ALARM? ' + value_channel)
            rlist = rstr.split(',')
            rlist[-1] = rlist[-1][0:len(rlist[-1])-2]
            #item 0 is off/on; 1 is high value, 2 is low value; 3 is deadband; 
            #4 is latch anable; 5 is audible; 6 is visible        
            return rlist

    def query_alarm_status(self, value_channel):
        '''
        Queries the status of the alarm.
        330: N/A
        340: INPUT: ALARMST? <input>
             RETURN: <high status>,<low status>
        336: INPUT: ALARMST? <value_channel>
             RETURN: <high state>,<low state>
        0 = off, 1 = on
        '''
        if (self.model == 'MODEL340' or self.model == 'MODEL336'):
            rstr = self.lakeshore.query('ALARMST? ' + value_channel)
            rlist = rstr.split(',')
            rlist[-1] = rlist[-1][0:len(rlist[-1])-2]
            #item 0 is high state; 1 is low state
            return rlist

    def query_temp(self, sensor):
        '''
        Reads the current temperature in Kelvin
        330: INPUT: CDAT? OR SDAT?
             RETURN: <temperature>
        340: INPUT: KRDG? <input>
             RETURN: <temperature>
        336: INPUT: KRDG? <sensor (A/B)>
             RETURN: <temperature>
        '''
        if self.model == 'MODEL330':
            if sensor == 'A':
                rstr = self.lakeshore.query('SDAT? ')
            if sensor == 'B':
                rstr = self.lakeshore.query('CDAT? ')
            rstr = rstr[0:len(rstr)-2]
            return rstr
        elif self.model == 'MODEL340' or self.model == 'MODEL336':
            rstr = self.lakeshore.query('KRDG? ' + sensor)
            rstr = rstr[0:len(rstr)-2]
            return rstr


if __name__ == "__main__":
    temp_controller = Lakeshore(12) #use your GPIB port
    print(temp_controller.state)
    curr_temp = float(temp_controller.query_temp('A'))
    set_temp = float(temp_controller.query_setpoint())
    print('Current temperature ', temp_controller.query_temp('A'), 'K')    
    temp_controller.set_setpoint(305)
    time.sleep(2)
    set_temp = float(temp_controller.query_setpoint())
    print('Set point is ', set_temp, 'K')    
    while abs(curr_temp - set_temp) > 0.5:
        curr_temp = float(temp_controller.query_temp('A'))
        print('Current temperature ', curr_temp, 'K')
        print('Set point is ', temp_controller.query_setpoint(), 'K')
        time.sleep(2)