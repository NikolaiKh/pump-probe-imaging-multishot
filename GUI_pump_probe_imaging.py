import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsScene, QFileDialog
from PyQt6.QtCore import QObject, QThread, QThreadPool, QRunnable, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt
import traceback, sys
from tkinter import messagebox
import qimage2ndarray
import numpy as np
import re
from interface import Ui_Form
import Lockin_SR_class as Lockin_class
import Newport_XPS_class as DelayLine_class
import micromanager_class
from multiprocessing.pool import ThreadPool
import time
import pyqtgraph as pg
import threading
import queue


uiclass, baseclass = pg.Qt.loadUiType("interface.ui")

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class Worker(QRunnable):
    # used for LIA and XPS initialization
    '''
    Worker thread for any function
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    taken from https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthreadpool/
    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(
                *self.args, **self.kwargs
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done



class MainForm(QWidget):
    def __init__(self):
        super().__init__()
        # set parameters of GUI
        self.setWindowTitle('Imaging Pump Probe')

        # create an instance of Ui_Form
        self.ui = Ui_Form()

        # initialization of GUI
        self.ui.setupUi(self)

        # plot blank images
        self.ui.plotWidget.ui.histogram.hide()
        self.ui.plotWidget.ui.roiBtn.hide()
        self.ui.plotWidget.ui.menuBtn.hide()
        self.scene = QGraphicsScene()
        self.show()

        # camera initialization
        self.camera_init()

        # set functions for buttons
        self.ui.folderButton.clicked.connect(self.show_folder_dialog)
        self.ui.connectLIAandXPSbutton.clicked.connect(self.lia_xps_init)
        self.ui.StopButton.clicked.connect(self.stop_button)
        self.ui.StartButton.clicked.connect(self.start_button_press)
        self.ui.TestButton.clicked.connect(self.test_button)
        self.ui.testImgButton.clicked.connect(self.get_test_img)
        # self.ui.pModeComboBox.currentTextChanged.connect(self.PModeComboBox_changed())
        # self.ui.binningComboBox.currentIndexChanged(self.binningComboBox_changed)

        # folder and file names
        self.folder_path = self.ui.folder_edit.text()
        # variable for stopping main loop
        self.isStop = True
        # setup thread pool
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def camera_init(self):
        # camera connection
        self.camera = micromanager_class.MMcamera()
        #set max sensetivity
        self.camera.setMaxSens()
        #get gain
        gain = int(self.camera.getGain())
        self.ui.gain_spinBox.setValue(gain)
        #get and set PModes to combobox
        PModes = self.camera.getAllPModevalues()
        self.ui.pModeComboBox.addItems(PModes)
        pmode = self.camera.getPMode()
        index = PModes.index(pmode)
        if index >= 0:
            self.ui.pModeComboBox.setCurrentIndex(index)
        #get and set binnings to combobox
        binnings = self.camera.getAllBinningvalues()
        self.ui.binningComboBox.addItems(binnings)
        bin = self.camera.getBinning()
        index = binnings.index(bin)
        if index >= 0:
            self.ui.binningComboBox.setCurrentIndex(index)

    def lia_xps_init(self):
        # Pass the function to execute
        worker = Worker(self.connect_LIA_XPS)  # Any other args, kwargs are passed to the run function
        # Execute
        self.threadpool.start(worker)

    def connect_LIA_XPS(self):
        # connect LIA
        self.lockin_id = self.ui.LockIn.text() #set lock-in addres
        self.lia = Lockin_class.Lockin(self.lockin_id)
        self.ui.liaStatuslabel.setText(self.lia.state)
        #connect delay line
        controller = 'GROUP1.POSITIONER'
        self.delay_line = DelayLine_class.DelayLine(controller)
        self.getDLposition()
        # connect Pump PWR L/2
        controller = 'GROUP3.POSITIONER'
        self.pumpPWR = DelayLine_class.DelayLine(controller)
        self.getPumpPWR()
        self.ui.XPSStatuslabel.setText("XPS is connected")

    def getDLposition(self):
        self.currDLposition = self.delay_line.get_position()
        self.ui.currentDLposituionlabel.setText(f"Current delay pos: {self.currDLposition} mm")

    def getPumpPWR(self):
        self.curr_pumpPWR = self.pumpPWR.get_position()
        self.ui.curr_pumpPWRlabel.setText(f"Current PWR: {self.curr_pumpPWR} deg")

    def PModeComboBox_changed(self):
        self.camera.setPMode(str(self.ui.pModeComboBox.currentText()))

    def binningComboBox_changed(self):
        self.camera.setBinning(str(self.ui.binningComboBox.currentText()))

    def stop_button(self):
        self.isStop = True

    def start_button_press(self):
        # Pass the function to execute
        worker = Worker(self.start_button_thread) # Any other args, kwargs are passed to the run function
        # Execute
        self.threadpool.start(worker)

    def start_button_thread(self):
        # start main measurements
        if not hasattr(self, 'lia'):
            messagebox.showerror("Error", "Lock-in is not connected!")
            return

        if not hasattr(self, 'delay_line'):
            messagebox.showerror("Error", "Delay line is not connected!")
            return

        # main loop measurements
        self.isStop = False
        self.delay_move(self.ui.DelayLineMin.text())
        self.PWR_move(self.ui.PWRmin.text())
        self.set_camera_settings()

        # load the parameters of measurements
        delay = {}
        delay['start'] = float(self.ui.DelayLineMin.text())
        delay['stop'] = float(self.ui.DelayLineMax.text())
        delay['step'] = float(self.ui.DelayLineStep.text()) * np.sign(delay['stop'] - delay['start'])
        if delay['start'] == delay['stop']:
            arrayoftime = np.array(delay['start'])
        else:
            arrayoftime = np.arange(delay['start'], delay['stop'] + delay['step'], delay['step'])

        if self.ui.additionalDL_checkBox.isChecked():
            seq = self.ui.additionalDLseq_Edit.text()
            temp = re.findall(r"[-+]?\d*\.\d+|\d+", seq)
            res = list(map(float, temp))
            begintimearray = np.arange(res[0], res[2] + res[1], res[1])
            arrayoftime = np.unique(np.concatenate([begintimearray, arrayoftime])) #concatenate and exclude doubled items

        power = {}
        power['start'] = float(self.ui.PWRmin.text())
        power['stop'] = float(self.ui.PWRmax.text())
        power['step'] = float(self.ui.PWRstep.text()) * np.sign(power['stop'] - power['start'])
        if power['start'] == power['stop']:
            arrayofpwr = np.array(power['start'])
        else:
            arrayofpwr = np.arange(power['start'], power['stop'] + power['step'], power['step'])

        all_steps = len(arrayoftime)*len(arrayofpwr)
        counter = 0
        for pwr_index, pwr_position in enumerate(arrayofpwr):
            if not self.isStop:
                self.PWR_move(pwr_position)
                for delay_index, delay_position in enumerate(arrayoftime):
                    if not self.isStop:
                        self.delay_move(delay_position)
                        self.take_images()
                        delay_pwr = f"pwr_{pwr_position}_delay_{delay_position}"
                        self.save_images(delay_pwr)
                        # save first reference image any case
                        if counter == 1:
                            folder = self.ui.folder_edit.text()
                            filename = self.ui.FileName.text()
                            fullpath = os.path.join(folder, filename)
                            self.save_snap(self.reference_img, fullname=fullpath+".dat")
                            self.ui.referenceImage_view.export(fullpath + ".png")
                            fullpath = os.path.join(folder, "protocol_"+filename)
                            self.save_mainwindow_screenshot(fullpath + ".png")
                        counter += 1
                        progress = int(100 * counter / all_steps)
                        self.ui.progressBar.setValue(progress)
                        # self.repaint()
                        # self.update()
        messagebox.showinfo("Done", "Measurements are done.")

    def test_button(self):
        self.delay_move(self.ui.DelayLineMin.text())
        self.PWR_move(self.ui.PWRmin.text())
        self.set_camera_settings()
        self.take_images()

    def take_images(self):
        aux = self.ui.ShutterOut.text()
        self.lia.set_aux(aux, 0) # close shutter
        self.reference_img = self.camera.getImage()
        self.update_frame(self.reference_img, self.ui.referenceImage_view)
        self.lia.set_aux(aux, 5) # open shutter
        self.pumped_img = self.camera.getImage()
        self.lia.set_aux(aux, 0) # open shutter
        self.update_frame(self.pumped_img, self.ui.pumpedImage_view)
        self.difference_img = self.pumped_img - self.reference_img
        a = self.difference_img.astype(float)
        b = self.reference_img.astype(float)
        self.norm_img = np.divide(a, b, out=np.zeros_like(a), where=b != 0)
        # update images on ui
        self.update_frame(self.difference_img, self.ui.differenceImage_view)
        self.update_frame(self.norm_img, self.ui.normalizedImage_view)

    def get_test_img(self):
        self.set_camera_settings()
        img = self.camera.getImage()
        self.update_frame(img, self.ui.referenceImage_view)
        #2D imaging
        self.ui.plotWidget.setImage(img)
        # saving
        folder = self.ui.folder_edit.text()
        filename = self.ui.FileName.text()
        fullname = os.path.join(folder, filename)+".png"
        self.ui.plotWidget.export(fullname)

    def set_camera_settings(self):
        self.camera.setExptime(int(self.ui.ExpTime.text()))
        self.camera.setBinning(self.ui.binningComboBox.currentText())
        self.camera.setGain(int(self.ui.gain_spinBox.text()))
        mode = self.ui.pModeComboBox.currentText()
        self.camera.setPMode(mode) # Normal mode closes the program sometimes

    def delay_move(self, position):
        self.ui.currentDLposituionlabel.setText("Delay line is moving")
        # try:
        #     currDLposition = self.delay_line.get_position()
        #     self.delay_line.move_to(position)
        # except: # if XPS controller crashed
        #     time.sleep(240)
        #     self.connect_LIA_XPS()
        # check the position accuracy. 5e-4 mm = 3 fs for single delay stage
        self.DL_setted = position
        currDLposition = -1
        while abs(currDLposition - float(position)) > 0.0005:
            try:
                self.delay_line.move_to(position)
                time.sleep(0.05)
                currDLposition = self.delay_line.get_position()
            except:  # if XPS controller crashed
                while True:
                    time.sleep(30)
                    try:
                        self.ui.currentDLposituionlabel.setText("Reconnecting XPS")
                        self.connect_LIA_XPS()
                        self.pumpPWR.move_to(self.pumpPWR_setted)
                        self.delay_line.move_to(position)
                        break
                    except:
                        self.ui.currentDLposituionlabel.setText("Reconnecting XPS again")

        self.ui.currentDLposituionlabel.setText(f"Current delay pos: {currDLposition}mm")
        self.ui.currentDLposituionlabel.repaint()
        self.ui.currentDLposituionlabel.update()

    def PWR_move(self, position):
        self.ui.curr_pumpPWRlabel.setText("PWR is moving")
        # while True:
        #     try:
        #         self.pumpPWR.move_to(position)
        #         break
        #     except: # if XPS controller crashed
        #         time.sleep(10)
        #         try:
        #             print("Trying reconnect XPS")
        #             self.connect_LIA_XPS()
        #             break
        #         except:
        #             print("Trying reconnect XPS again")
        # check the position accuracy
        self.pumpPWR_setted = position
        curr_pumpPWR = -400
        while abs(curr_pumpPWR - float(position)) > 0.001:
            try:
                self.pumpPWR.move_to(position)
                time.sleep(0.05)
                curr_pumpPWR = self.pumpPWR.get_position()
            except:  # if XPS controller crashed
                while True:
                    time.sleep(30)
                    try:
                        self.ui.curr_pumpPWRlabel.setText("Reconnecting XPS")
                        self.connect_LIA_XPS()
                        self.pumpPWR.move_to(position)
                        self.delay_line.move_to(self.DL_setted)
                        break
                    except:
                        self.ui.curr_pumpPWRlabel.setText("Reconnecting XPS again")

        self.ui.curr_pumpPWRlabel.setText(f"Current PWR: {curr_pumpPWR}deg")
        self.ui.curr_pumpPWRlabel.repaint()
        self.ui.curr_pumpPWRlabel.update()

    def show_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder_path:
            self.ui.folder_edit.setText(folder_path+"/")
            self.folder_path = self.ui.folder_edit.text()

    def update_frame(self, frame, widget):
        image_data = frame.T
        # Get the number of rows and columns
        num_rows, num_columns = image_data.shape
        # Get the central subarray
        central_subarray = image_data[num_rows//4: num_rows*3//4, num_columns//4: num_columns*3//4]
        # Compute the maximum and minimum values
        max_value = np.max(central_subarray)
        min_value = np.min(central_subarray)
        # View image
        widget.setImage(image_data)
        widget.setLevels(min_value, max_value)  # Set min_value and max_value according to your desired range
        widget.show()

    def save_snap(self, image, fullname, format='%d'):
        # saving one image
        folder = self.ui.folder_edit.text()
        # filename = self.ui.FileName.text()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Folder does not exist!")
            return
        # if not filename:
        #     messagebox.showerror("Error", "Please enter a file name")
        #     return
        # fullname = os.path.join(folder, filename)
        if os.path.exists(fullname):
            overwrite = messagebox.askyesno('File already exists', 'File already exists. Overwrite?')
            if overwrite:
                with open(fullname, "w") as file:
                    np.savetxt(file, image, fmt=format)
                    # messagebox.showinfo("Save", "File saved successfully.")
            else:
                self.isStop = True
        else:
            with open(fullname, "w") as file:
                np.savetxt(file, image, fmt=format)
                # messagebox.showinfo("Save", "File saved successfully.")
        return

    def save_images(self, delay_pwr=""):
        base_folder = self.ui.folder_edit.text()
        file_base_name = self.ui.FileName.text()
        # save reference image
        if self.ui.checkBoxReferenceImg.isChecked():
            folder = base_folder + f"ref_{file_base_name}"
            if not os.path.isdir(folder):
                os.makedirs(folder)
            filename = f"{delay_pwr}.dat"
            fullname = os.path.join(folder, filename)
            self.save_snap(self.reference_img, fullname=fullname)
            # save screenshot
            self.ui.referenceImage_view.export(fullname+".png")

        # save pumped image
        if self.ui.checkBoxPumped.isChecked():
            folder = base_folder + f"pumped_{file_base_name}"
            if not os.path.isdir(folder):
                os.makedirs(folder)
            filename = f"{delay_pwr}.dat"
            fullname = os.path.join(folder, filename)
            self.save_snap(self.pumped_img, fullname=fullname)
            # save screenshot
            self.ui.pumpedImage_view.export(fullname + ".png")

        # save difference image
        if self.ui.checkBoxDifference.isChecked():
            folder = base_folder + f"diff_{file_base_name}"
            if not os.path.isdir(folder):
                os.makedirs(folder)
            filename = f"{delay_pwr}.dat"
            fullname = os.path.join(folder, filename)
            self.save_snap(self.difference_img, fullname=fullname)
            # save screenshot
            self.ui.differenceImage_view.export(fullname + ".png")

         # save pumped image
        if self.ui.checkBoxDifferenceNormalized.isChecked():
            folder = base_folder + f"diffNorm_{file_base_name}"
            if not os.path.isdir(folder):
                os.makedirs(folder)
            filename = f"{delay_pwr}.dat"
            fullname = os.path.join(folder, filename)
            self.save_snap(self.norm_img,  fullname=fullname, format="%.5f")
            # save screenshot
            self.ui.normalizedImage_view.export(fullname + ".png")
        return

    def save_mainwindow_screenshot(self, fullpath):
        # Get the primary screen
        screen = QApplication.primaryScreen()
        # Capture the entire main window
        pixmap = screen.grabWindow(self.winId())
        # Save the screenshot to a file
        pixmap.save(fullpath, 'png')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    mainWindow = MainForm()
    sys.exit(app.exec())
