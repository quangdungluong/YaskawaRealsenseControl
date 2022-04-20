import os
import sys
import threading
import time

import numpy as np
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QMessageBox,
                             QTableWidgetItem)

from main_ui import Ui_MainWindow
from MainThread import *


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.display_width = 640
        self.display_height = 480
        self.img_label.resize(self.display_width, self.display_height)
        self.update_image(np.zeros([self.display_height, self.display_width, 3], dtype=np.uint8))
        self.fps_box.setChecked(True)
        self.detect_box.setChecked(True)

        self.conveyor = False
        self.thread1 = Main_loop()

        ## Connection and Basic Control button
        self.connect_btn.clicked.connect(self.connect)
        self.start_btn.clicked.connect(self.start_manual)
        self.stop_btn.clicked.connect(self.stop_manual)
        self.servoOn_btn.clicked.connect(self.servo_on)
        self.home_btn.clicked.connect(self.go_home)
        self.toolOn_btn.clicked.connect(self.tool_on)

        ## Machine Controller button
        self.startConveyor_btn.clicked.connect(self.start_conveyor)

        ## Manual Position button
        self.getPos_btn.clicked.connect(self.get_position)
        self.setPos_btn.clicked.connect(self.set_position)
        self.setDefault_btn.clicked.connect(self.set_default_position)

        ## Incremental Position
        self.speed_spin.valueChanged.connect(lambda x: self.change_speed(x, 'speed_spin'))
        self.speed_slider.valueChanged.connect(lambda x: self.change_speed(x, 'speed_slider'))
        self.incX_btn.clicked.connect(lambda x: self.incremental_pos("X", "inc"))
        self.decX_btn.clicked.connect(lambda x: self.incremental_pos("X", "dec"))
        self.incY_btn.clicked.connect(lambda x: self.incremental_pos("Y", "inc"))
        self.decY_btn.clicked.connect(lambda x: self.incremental_pos("Y", "dec"))
        self.incZ_btn.clicked.connect(lambda x: self.incremental_pos("Z", "inc"))
        self.decZ_btn.clicked.connect(lambda x: self.incremental_pos("Z", "dec"))
        self.incRx_btn.clicked.connect(lambda x: self.incremental_pos("Rx", "inc"))
        self.decRx_btn.clicked.connect(lambda x: self.incremental_pos("Rx", "dec"))
        self.incRy_btn.clicked.connect(lambda x: self.incremental_pos("Ry", "inc"))
        self.decRy_btn.clicked.connect(lambda x: self.incremental_pos("Ry", "dec"))
        self.incRz_btn.clicked.connect(lambda x: self.incremental_pos("Rz", "inc"))
        self.decRz_btn.clicked.connect(lambda x: self.incremental_pos("Rz", "dec"))

        ## Camera
        self.startCam_btn.clicked.connect(self.start_capture)
        self.stopCam_btn.clicked.connect(self.stop_capture)
        self.detect_box.clicked.connect(self.detect)

        ## Auto button
        self.startAuto_btn.clicked.connect(self.start_auto)
        self.stopAuto_btn.clicked.connect(self.stop_auto)

        ## Adjust Confidence and IoU Threshold
        self.confSpinBox.valueChanged.connect(lambda x: self.changeCam_config(x, 'confSpinBox'))
        self.confSlider.valueChanged.connect(lambda x: self.changeCam_config(x, 'confSlider'))
        self.iouSpinBox.valueChanged.connect(lambda x: self.changeCam_config(x, 'iouSpinBox'))
        self.iouSlider.valueChanged.connect(lambda x: self.changeCam_config(x, 'iouSlider'))

        ## Choose model
        self.comboBox.clear()
        self.model_list = os.listdir('./model')
        self.model_list = [file for file in self.model_list if file.endswith('.pt')]
        self.model_list.sort(key=lambda x: os.path.getsize('./model/'+x))
        self.comboBox.addItems(self.model_list)
        self.comboBox.currentTextChanged.connect(self.change_model)
        
        ## close event
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

        ## Get teaching point
        self.btnTeaching.clicked.connect(self.teaching_point)
        self.btnClearData.clicked.connect(self.clear_point)
        self.btnForward.clicked.connect(self.forward_point)

    ################################################################
    ##########  Connection, Basic and Machine Controller   #########
    ################################################################

    def connect(self):
        self.statusbar.showMessage("Connected...")
        self.thread1.r.UDP_IP = str(self.ipAddress.text())
        self.thread1.r.UDP_PORT = int(self.portAddress.text())

    def start_manual(self):
        self.statusbar.showMessage("Start...")
        self.thread1.r.servoON()
        self.servoOn_btn.setText("ServoOff")

    def stop_manual(self):
        self.statusbar.showMessage("Stop and go home...")
        self.go_home()
        self.thread1.r.servoOFF()
        self.servoOn_btn.setText("ServoOn")

    def go_home(self):
        self.statusbar.showMessage("Go home...")
        self.thread1.r.Write_Robot_XYZ(xc, yc, zc)

    def servo_on(self):
        if (self.servoOn_btn.text() == "ServoOn"):
            self.statusbar.showMessage("Turn servo on...")
            self.thread1.r.servoON()
            self.servoOn_btn.setText("ServoOff")
        else:
            self.statusbar.showMessage("Turn servo off...")
            self.thread1.r.servoOFF()
            self.servoOn_btn.setText("ServoOn")

    def start_conveyor(self):
        if (self.conveyor):
            self.startConveyor_btn.setText("Start Conveyor")
            self.thread1.r.writeByte(2, 0)
            self.conveyor = False
        else:
            self.startConveyor_btn.setText("Stop Conveyor")
            self.thread1.r.writeByte(2, 1)
            self.conveyor = True

    def tool_on(self):
        self.thread1.r.ToolStart()
        if (self.toolOn_btn.text() == "Tool On"):
            self.toolOn_btn.setText("Tool Off")
        else:
            self.toolOn_btn.setText("Tool On")


    ################################################################
    #####################  Manual Control   ########################
    ################################################################
    def get_position(self):
        x, y, z, rx, ry, rz = self.thread1.r.pos_robot(self.thread1.r.Read_Robot_XYZ())
        x, y, z, rx, ry, rz = x/1000, y/1000, z/1000, rx/10000, ry/10000, rz/10000
        self.X_line.setText(str(x))
        self.Y_line.setText(str(y))
        self.Z_line.setText(str(z))
        self.Rx_line.setText(str(rx))
        self.Ry_line.setText(str(ry))
        self.Rz_line.setText(str(rz))

    def set_position(self):
        x = self.setX_line.text()
        y = self.setY_line.text()
        z = self.setZ_line.text()
        rx = self.setRx_line.text()
        ry = self.setRy_line.text()
        rz = self.setRz_line.text()
        if (self.setSpeed_line.text() != ""):
            self.thread1.r.v_r = int(self.setSpeed_line.text())
        self.thread1.r.Write_Robot_XYZ(x, y, z, rx, ry, rz)

    def set_default_position(self):
        self.setX_line.setText(xc)
        self.setY_line.setText(yc)
        self.setZ_line.setText(zc)
        self.setRx_line.setText(rx)
        self.setRy_line.setText(ry)
        self.setRz_line.setText(rz)
        self.setSpeed_line.setText(v_r)

    def incremental_pos(self, coord, flag):
        step = int(self.step_spin.text())
        x, y, z, rx, ry, rz = self.thread1.r.pos_robot(self.thread1.r.Read_Robot_XYZ())
        x, y, z, rx, ry, rz = x/1000, y/1000, z/1000, rx/10000, ry/10000, rz/10000
        if coord == "X":
            if flag == "inc": x += step
            else: x -= step
        if coord == "Y":
            if flag == "inc": y += step
            else: y -= step
        if coord == "Z":
            if flag == "inc": z += step
            else: z -= step
        if coord == "Rx":
            if flag == "inc": rx += step
            else: rx -= step
        if coord == "Ry":
            if flag == "inc": ry += step
            else: ry -= step
        if coord == "Rz":
            if flag == "inc": rz += step
            else: rz -= step
        x, y, z, rx, ry, rz = str(x), str(y), str(z), str(rx), str(ry), str(rz)
        self.thread1.r.Write_Robot_XYZ(x, y, z, rx, ry, rz)

    def change_speed(self, x, detect_flag):
        if detect_flag == 'speed_spin':
            self.speed_slider.setValue(int(x))
        elif detect_flag == 'speed_slider':
            self.speed_spin.setValue(x)
            self.thread1.r.v_r = x
        else:
            pass

    ################################################################
    #####################  Teaching Point   ########################
    ################################################################
    def teaching_point(self):
        n = self.tableWidgetPoints.rowCount()
        self.tableWidgetPoints.setRowCount(n)
        self.tableWidgetPoints.setColumnCount(6)
        self.tableWidgetPoints.insertRow(n)
        x, y, z, rx, ry, rz = self.thread1.r.pos_robot(self.thread1.r.Read_Robot_XYZ())
        self.tableWidgetPoints.setItem(n, 0, QTableWidgetItem(str(x/1000)))
        self.tableWidgetPoints.setItem(n, 1, QTableWidgetItem(str(y/1000)))
        self.tableWidgetPoints.setItem(n, 2, QTableWidgetItem(str(z/1000)))
        self.tableWidgetPoints.setItem(n, 3, QTableWidgetItem(str(rx/10000)))
        self.tableWidgetPoints.setItem(n, 4, QTableWidgetItem(str(ry/10000)))
        self.tableWidgetPoints.setItem(n, 5, QTableWidgetItem(str(rz/10000)))

    def clear_point(self):
        row = self.tableWidgetPoints.currentRow()
        self.tableWidgetPoints.removeRow(row)

    def forward_point(self):
        row = self.tableWidgetPoints.currentRow()
        x = self.tableWidgetPoints.item(row, 0).text()
        y = self.tableWidgetPoints.item(row, 1).text()
        z = self.tableWidgetPoints.item(row, 2).text()
        rx = self.tableWidgetPoints.item(row, 3).text()
        ry = self.tableWidgetPoints.item(row, 4).text()
        rz = self.tableWidgetPoints.item(row, 5).text()
        print(x, y, z, rx, ry, rz)
        self.thread1.r.Write_Robot_XYZ(x, y, z, rx, ry, rz)

    ################################################################
    #######################  Auto Control   ########################
    ################################################################
    def start_auto(self):
        self.thread1.change_pixmap_signal.connect(self.update_image)
        self.thread1.send_fps.connect(self.show_fps)
        self.thread1.start()
        self.thread1.r.servoON()
        self.servoOn_btn.setText("ServoOff")
        self.thread1.r.Write_Robot_XYZ(xc, yc, zc)

    def stop_auto(self):
        self.thread1.r.writeByte(5, 1)
        self.thread1.r.writeByte(6, 1)
        self.thread1.r.writeByte(1, 1)
        # self.thread1.quit()
        # self.thread1.wait(50)
        # self.go_home()
        self.thread1.r.CheckToolOff()
        self.thread1.r.servoOFF()
        self.servoOn_btn.setText("ServoOn")
        self.statusbar.showMessage("Stop and go home...")

    def start_capture(self):
        # if not self.thread1.cam_flag:
        #     self.thread1.change_pixmap_signal.connect(self.update_image)
        #     self.thread1.send_fps.connect(self.show_fps)
        #     self.thread1.start()

        #     self.thread2 = threading.Thread(target=self.thread1.camera_run)
        #     self.thread2.setDaemon(True)
        #     self.thread2.start()
        # else:
        #     self.thread2 = threading.Thread(target=self.thread1.camera_run)
        #     self.thread2.setDaemon(True)
        #     self.thread2.start()
        self.thread1.change_pixmap_signal.connect(self.update_image)
        self.thread1.send_fps.connect(self.show_fps)
        # self.thread1.start()

        self.thread2 = threading.Thread(target=self.thread1.camera_run)
        # self.thread2.setDaemon(True)
        self.thread2.start()

        self.statusbar.showMessage("Start capture...")


    def stop_capture(self):
        if self.thread1.cam_flag:
            self.thread1.change_pixmap_signal.disconnect(self.update_image)
            self.thread1.quit()
            self.thread1.wait(500)
            self.thread1.cam_flag = False
            self.thread1.camera.pipeline.stop()
            time.sleep(1)
            self.update_image(np.zeros([480,640,3],dtype=np.uint8))
            self.statusbar.showMessage("Stop capture...")

    def detect(self):
        self.thread1.camera.detect_flag = self.detect_box.isChecked()
        if (self.detect_box.isChecked()):
            self.statusbar.showMessage("Detecting...")
        else:
            self.statusbar.showMessage("Stop detecting...")

    def changeCam_config(self, x, detect_flag):
        if detect_flag == 'confSpinBox':
            self.confSlider.setValue(int(x*100))
        elif detect_flag == 'confSlider':
            self.confSpinBox.setValue(x/100)
            self.thread1.camera.model.conf = x/100
        elif detect_flag == 'iouSpinBox':
            self.iouSlider.setValue(int(x*100))
        elif detect_flag == 'iouSlider':
            self.iouSpinBox.setValue(x/100)
            self.thread1.camera.model.iou = x/100
        else:
            pass
        self.statusbar.showMessage("Changed model configuration...")

    def change_model(self):
        self.model_type = self.comboBox.currentText()
        self.thread1.camera.weights = "./model/%s" % self.model_type
        self.confSpinBox.setProperty("value", 0.25)
        self.confSlider.setProperty("value", 25)
        self.iouSpinBox.setProperty("value", 0.45)
        self.iouSlider.setProperty("value", 45)
        
        self.statusbar.showMessage("Changed model...")


    def show_fps(self, fps):
        if self.fps_box.isChecked():
            self.fps_label.setText(fps)
        else:
            self.fps_label.setText("")
    
    ################################################################
    #######################  GUI Control   #########################
    ################################################################
    def closeEvent(self, event):
        close = QMessageBox.question(self,
                                        "Quit",
                                        "Are you sure want to stop process?",
                                        QMessageBox.Yes | QMessageBox.No)
        if close == QMessageBox.Yes:
            self.stop_auto()
            if (self.conveyor):
                self.conveyor = False
                self.start_conveyor()
            time.sleep(0.5)
            event.accept()
        else:
            event.ignore()

    def display_msg(self, msg):
        self.statusbar.showMessage(msg)

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.img_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        h, w, ch = cv_img.shape
        bytes_per_line = ch*w
        convert_to_qt_format = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(convert_to_qt_format)
