from RobotControl import *
import time

r = RobotControl()
# r.servoON()
# r.checkConveyor()
r.Conveyor()
time.sleep(5)
r.checkConveyor()
r.Conveyor()
r.checkConveyor()
# r.servoOFF()