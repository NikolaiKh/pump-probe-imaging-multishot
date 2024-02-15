import pyvisa
import re


class Lockin:
    def __init__(self, gpibport):
        rm = pyvisa.ResourceManager()
        self.lockin = rm.open_resource(f'GPIB0::{gpibport}::INSTR')
        # # get SR name and model (830 / 844). It is important for aux_out !!!!
        self.name = self.lockin.query("*IDN?")
        match = re.search(r"SR(\d{3})", self.name)
        self.model = int(match.group(1))
#         self.model = 830
        self.state = f'Lock-in is connected. Model {self.model}'

    def getXYR(self):
        # get X Y R signals from SR844
        out_signal = self.lockin.query("SNAP? 1,2,3")
        signal = out_signal.split(",")
        sigX = float(signal[0])
        sigY = float(signal[1])
        sigR = float(signal[2])
        return [sigX, sigY, sigR]

    def set_aux(self, aux, voltage):
        if self.model == 844:  # check the model number
            # set aux_out_1 voltage to SR844
            self.lockin.write(f"AUXO {aux}, " + str(voltage))  # !!!! SR844 command. SR830 has another string
            return voltage
        elif self.model == 830:  # check the model number
            self.lockin.write(f"AUXV {aux}, " + str(voltage))  # SR830
            return voltage


if __name__ == "__main__":
    lia = Lockin(8)
    lia.set_aux(2, 0)
    print(lia.state)
    print(lia.getXYR())
