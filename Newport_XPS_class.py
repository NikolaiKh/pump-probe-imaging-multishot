from newportxps import NewportXPS


class DelayLine():
    def __init__(self, controller='GROUP1.POSITIONER'):
        
        self.controller = controller
        
        # Delay Line initialization
        self.myxps = NewportXPS('192.168.50.2', username='Administrator', password='Administrator')    # Connect to the XPS
            
        self.myxps.kill_group()
        self.myxps.initialize_allgroups()
        self.myxps.home_allgroups()
        
    def move_to(self, position):
        positioner = self.controller  
        self.myxps.move_stage(positioner, position)
        
    def get_position(self):
        positioner = self.controller
        return self.myxps.get_stage_position(positioner)    


if __name__ == "__main__":

    # We will proceed with Delay Line setup, by uncommenting the code below
    # myxps = XPS_Q8_drivers.XPS() # Connect to the XPS
    # socketId = myxps.TCP_ConnectToServer('XPS_web_ip', 5001, 20)   # Check connection passed
    # if (socketId == -1):
    #     print ('Connection to XPS failed, check IP & Port')
    
    # Now we will check if the DelayLine class works:
    controller = 'GROUP1.POSITIONER'
    delay_line = DelayLine(controller)
    position = 15 # in mm
    delay_line.move_to(position)
    print(delay_line.get_position())
