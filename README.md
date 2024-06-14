# pump-probe-imaging-multishot
The gui makes images in pump probe regime, i.e. it moves delay line (NewPort XPS controller), makes reference image (no pump) with MicroManager core, opens shutter (using lock-in SR830), makes pumped image. Program saves .dat files and .png screenshots

Tested with Teledyne Retiga R3 camera on Win10 (Win7 didn't take images with mmcore, with no reason).

GUI is made with QtDesigner and converted to interface.py with ChatGPT-made program Qt_convertor_ui_to_py.py.

Camera, shutter and laser are not synchronized!!! It could be a problem at short explosure times (few ms). I used it with 8 sec exp time, SHG images in antiferromagnet. 

pyqtgraph is used for fast images show: https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot 
