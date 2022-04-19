from RobotControl import *

r = RobotControl()

data = r.ReadByte(2)
print(data[32])