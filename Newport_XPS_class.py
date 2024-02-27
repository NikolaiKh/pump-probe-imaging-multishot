from newportxps import NewportXPS
import time


class DelayLine:
    def __init__(self, controller='GROUP1.POSITIONER'):
        self.controller = controller
        self.group = controller.split('.')[0]  # get group name
        self.init()  # Delay Line initialization

    def init(self):
        # Delay Line initialization
        self.myxps = NewportXPS('192.168.50.2', username='Administrator',
                                password='Administrator')  # Connect to the XPS
        self.myxps.kill_group(group=self.group)
        # self.myxps.kill_group()
        # self.myxps.initialize_allgroups()
        self.myxps.initialize_group(group=self.group)
        # self.myxps.home_allgroups()
        self.myxps.home_group(group=self.group)
        self.position = 0

    def move_to(self, position):
        self.position = position
        try:
            self.myxps.move_stage(self.controller, position)
        except:  # if XPS controller crashed
            while True:
                time.sleep(30)
                try:
                    print("Reconnecting XPS")
                    self.init()
                    self.myxps.move_stage(self.controller, position)
                    break
                except:
                    print("Reconnecting XPS again")
                finally:
                    print(f"XPS at position {self.get_position()}")

        
    def get_position(self):
        positioner = self.controller
        try:
            pos = self.myxps.get_stage_position(positioner)
        except:  # if XPS controller crashed
            while True:
                time.sleep(30)
                try:
                    print("Reconnecting XPS")
                    self.init()
                    self.move_to(self.position)
                    pos = self.myxps.get_stage_position(positioner)
                    break
                except:
                    print("Reconnecting XPS again")
                finally:
                    print(f"XPS at position {pos}")
        return pos


if __name__ == "__main__":

    # We will proceed with Delay Line setup, by uncommenting the code below
    # myxps = XPS_Q8_drivers.XPS() # Connect to the XPS
    # socketId = myxps.TCP_ConnectToServer('XPS_web_ip', 5001, 20)   # Check connection passed
    # if (socketId == -1):
    #     print ('Connection to XPS failed, check IP & Port')
    
    # Now we will check if the DelayLine class works:
    controller = 'GROUP1.POSITIONER'
    delay_line = DelayLine(controller)
    for position in range(0, 50, 5): # in mm
        delay_line.move_to(position)
        print(delay_line.get_position())
