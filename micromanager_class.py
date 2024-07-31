import pymmcore
import os.path
import os
import matplotlib.pyplot as plt


class MMcamera():
    def __init__(self, mm_dir="C:\Program Files\Micro-Manager-2.0.3", config_file="MMConfig_pvcam_simple_1.cfg"):
        self.mmc = pymmcore.CMMCore()
        os.environ["PATH"] += os.pathsep.join(["", mm_dir])  # adviseable on Windows
        self.mmc.setDeviceAdapterSearchPaths([mm_dir])
        self.mmc.loadSystemConfiguration(os.path.join(mm_dir, config_file))

    def getImage(self):
        self.mmc.snapImage()
        return self.mmc.getImage().astype(int)

    def getExptime(self):
        return self.mmc.getExposure()

    def setExptime(self, time=10.0):
        self.mmc.setExposure(time)

    def getBinning(self):
        return self.mmc.getProperty("Camera", "Binning")

    def setBinning(self, binning="1x1"):
        self.mmc.setProperty("Camera", "Binning", binning)

    def getPMode(self):
        return self.mmc.getProperty("Camera", "PMode")

    def setPMode(self, mode="Normal"):
        self.mmc.setProperty("Camera", "PMode", mode)

    def getPixelType(self):
        return self.mmc.getProperty("Camera", "PixelType")

    def getGain(self):
        return self.mmc.getProperty("Camera", "Gain")

    def setGain(self, gain=1):
        self.mmc.setProperty("Camera", "Gain", str(gain))

    def setMaxSens(self, binning="4x4"): #for PVCAM cameras
        self.setBinning(binning)
        self.setPMode("Alternate Normal")
        self.setGain(2)

    def getAllBinningvalues(self):
        return self.mmc.getAllowedPropertyValues("Camera", "Binning")

    def getAllPModevalues(self):
        return self.mmc.getAllowedPropertyValues("Camera", "PMode")

    def getBytesPerPixel(self):
        return self.mmc.getBytesPerPixel()


if __name__ == "__main__":
    camera = MMcamera()
    camera.setExptime(100)
    print(f"Explosure time {camera.getExptime()} ms")
    # camera.setMaxSens("8x8")
    camera.setBinning(2)
    print(f"Binning {camera.getBinning()}")
    print(f"All allowed binning options: {camera.getAllBinningvalues()}")
    print(f"Pixel type {camera.getPixelType()}")
    # camera.setPMode("Alternate Normal")
    print(f"PMode {camera.getPMode()}")
    print(f"All PMode options: {camera.getAllPModevalues()}")
    # camera.setGain(2)
    print(f"Gain {camera.getGain()}")
    print(f"Bytes per pixel {camera.getBytesPerPixel()}")
    img = camera.getImage()
    imgplot = plt.imshow(img)
    plt.show()
