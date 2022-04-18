import socket
import time

class RobotControl:
    def __init__(self, udp_ip="192.168.1.14", udp_port=10040):
        self.UDP_IP = udp_ip
        self.UDP_PORT = udp_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)
        self.x_c = 185.0000         ### Home position
        self.y_c = 0.0000
        self.z_c = 125.0000
        self.r_x = 180.0000         ### current orientation
        self.r_y = 0.0000
        self.r_z = 0.0000
        self.v_r = 700             ### Velocity of robot moving


    def mainSelect(self):
        """
        Select the main job
        """
        data = b'YERC \x00$\x00\x03\x01\x00\x03\x00\x00\x00\x0099999999\x87\x00\x01\x00\x00\x02\x00\x00DUNG-TRUNG\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))


    def mainJob(self):
        """
        Start the main job
        """
        self.mainSelect()
        time.sleep(0.1)
        data = bytes.fromhex(
            '59 45 52 43 20 00 04 00 03 01 00 07 00 00 00 00 39 39 39 39 39 39 39 39 '
            '86 00 01 00 01 10 00 00 01 00 00 00')
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))


    def writeByte(self, index, value):
        """
        Write value to byte
        """
        data = bytes.fromhex('59 45 52 43 20 00 01 00 03 01 00 0F 00 00 00 00 39 39 39 39 39 39 39 39 7A 00')
        instance = self.to_hex16(index)
        behind = bytes.fromhex('01 10 00 00 00')
        if (value == 1):
            behind = bytes.fromhex('01 10 00 00 01')
        elif (value == 2):
            behind = bytes.fromhex('01 10 00 00 02')
        data = data + instance + behind
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))
        time.sleep(0.1)


    def writePos(self, index, x_d, y_d, z_d, rx = "180.000", ry = "0.0000", rz = "0.0000"):
        """
        b'YERC \x00h\x00\x03\x01\x00\x04\x00\x00\x00\x0099999999\x7f\x00\x01\x00\x00\x02\x00\x00'
        """
        data = bytes.fromhex(
            '59 45 52 43 20 00 34 00 03 01 00 04 00 00 00 00 39 39 39 39 39 39 39 39 '
            '7F 00') 
        instance = self.to_hex16(index)
        behind = bytes.fromhex('00 02 00 00')
        
        x, y, z, rx, ry, rz = self.char2int(x_d, y_d, z_d, rx, ry, rz)
        xhex = self.to_hex32(x)
        yhex = self.to_hex32(y)
        zhex = self.to_hex32(z)
        rxhex = self.to_hex32(rx)
        ryhex = self.to_hex32(ry)
        rzhex = self.to_hex32(rz)
        data_type = self.to_hex32(16)
        figure = self.to_hex32(0)
        tool = self.to_hex32(0)
        coord = self.to_hex32(0)
        extended_figure = self.to_hex32(0)
        seventh = self.to_hex32(0)
        eighth = self.to_hex32(0)
        data = data + instance + behind + data_type + figure + tool + coord + extended_figure + xhex + yhex + zhex + rxhex + ryhex + rzhex + seventh + eighth
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))


    def servoON(self):  # ID=00 00 after 03 01
        """
        b'YERC \x00\x04\x00\x03\x01\x00\x00\x00\x00\x00\x0099999999\x83\x00\x02\x00\x01\x10\x00\x00\x01\x00\x00\x00'
        """
        data = bytes.fromhex(
            '59 45 52 43 20 00 04 00 03 01 00 00 00 00 00 00 '
            '39 39 39 39 39 39 39 39 83 00 02 00 01 10 00 00 01 00 00 00')
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))
        time.sleep(0.1)

    def servoOFF(self): # ID= 00 01 after 03 01
        """
        b'YERC \x00\x04\x00\x03\x01\x00\x01\x00\x00\x00\x0099999999\x83\x00\x02\x00\x01\x10\x00\x00\x02\x00\x00\x00'
        """
        data = bytes.fromhex(
            '59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 '
            '39 39 39 39 39 39 39 39 83 00 02 00 01 10 00 00 02 00 00 00')
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))
        time.sleep(0.1)

    def CheckToolOn(self):  # ID=05
        data = self.ReadTool()
        n = len(data)   # ID = 06 (ReadTool), length of data received is 33 bytes
        while data[11] != 6 and n != 33:
            data = self.ReadTool()
            n = len(data)
        if data[32] == 1:
            print("Tool On")
        else:
            self.ToolStart()
            print("Change to Tool On")
            time.sleep(0.1)

    def CheckToolOff(self):  # ID=05
        data = self.ReadTool()
        n = len(data)
        while data[11] != 6 and n != 33:
            data = self.ReadTool()
            n = len(data)
        if data[32] == 0:
            print("Tool Off")
        else:
            self.ToolStart()
            print("Change to Tool Off")
            time.sleep(0.1)

    def ReadTool(self):  # ID = 00 06
        """
        b'YERC \x00\x00\x00\x03\x01\x00\x06\x00\x00\x00\x0099999999x\x00\xe9\x03\x01\x0e\x00\x00'
        """
        data = bytes.fromhex(   # #01001 => General Output; or #3001 => 0BB9 (Hex) => B9 0B
            '59 45 52 43 20 00 00 00 03 01 00 06 00 00 00 00 39 39 39 39 39 39 39 39 '
            '78 00 E9 03 01 0E 00 00')
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))
        data, addr = self.sock.recvfrom(1024)
        data = list(data)
        time.sleep(0.1)
        return data


    def ToolStart(self):  # ID = 00 07
        """
        b'YERC \x00\x04\x00\x03\x01\x00\x07\x00\x00\x00\x0099999999\x86\x00\x01\x00\x01\x10\x00\x00\x01\x00\x00\x00'
        """
        self.ToolSelect()
        time.sleep(0.1)
        data = bytes.fromhex(
            '59 45 52 43 20 00 04 00 03 01 00 07 00 00 00 00 39 39 39 39 39 39 39 39 '
            '86 00 01 00 01 10 00 00 01 00 00 00')
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))

    def ToolSelect(self):  # ID=03
        """
        b'YERC \x00$\x00\x03\x01\x00\x03\x00\x00\x00\x0099999999\x87\x00\x01\x00\x00\x02\x00\x00TOOLP\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        """
        data = bytes.fromhex(
            '59 45 52 43 20 00 24 00 03 01 00 03 00 00 00 00 39 39 39 39 39 39 39 39 '
            '87 00 01 00 00 02 00 00 54 4F 4F 4C 50 00 00 00 00 00 00 00 00 00 00 00 '
            '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00')
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))


    def Check_Pos(self, x_d, y_d, z_d):
        data = self.Read_Robot_XYZ()
        n = len(data)
        while data[11] != 2 and n < 75:
            data = self.Read_Robot_XYZ()
            n = len(data)
        if n > 75:
            self.x_c, self.y_c, self.z_c, self.r_x, self.r_y, self.r_z = self.pos_robot(data)
            a = self.compare_pos(x_d, y_d, z_d, self.x_c, self.y_c, self.z_c)
        else:
            a = 1
        return a


    def Read_Robot_XYZ(self):  # ID = 00 02
        """
        b'YERC \x00\x00\x00\x03\x01\x00\x02\x00\x00\x00\x0099999999u\x00e\x00\x00\x01\x00\x00'
        """
        data = bytes.fromhex(
            '59 45 52 43 20 00 00 00 03 01 00 02 00 00 00 00 39 39 39 39 39 39 39 39 '
            '75 00 65 00 00 01 00 00')
        self.sock.sendto(data, (self.UDP_IP, self.UDP_PORT))
        data, addr = self.sock.recvfrom(1024)
        data = list(data)
        time.sleep(0.1)
        return data


    def pos_robot(self, data):
        try:
            # X 52 55
            x = self.to_int(data[52], data[53], data[54], data[55])
            # Y 56 59
            y = self.to_int(data[56], data[57], data[58], data[59])
            # Z 60 63
            z = self.to_int(data[60], data[61], data[62], data[63])
            # Rx 64 67
            rx = self.to_int(data[64], data[65], data[66], data[67])
            # Ry 68 71
            ry = self.to_int(data[68], data[69], data[70], data[71])
            # Rz 72 75
            rz = self.to_int(data[72], data[73], data[74], data[75])
        except:
            x, y, z, rx, ry, rz = -1, -1, -1, -1, -1, -1
        return x, y, z, rx, ry, rz


    def Write_Robot_XYZ(self, x_d, y_d, z_d, rx = "180.000", ry = "0.0000", rz = "0.0000"): # ID = 00 04
        data = bytes.fromhex(
            '59 45 52 43 20 00 68 00 03 01 00 04 00 00 00 00 39 39 39 39 39 39 39 39 '
            '8A 00 01 00 01 02 00 00')
        x, y, z, rx, ry, rz = self.char2int(x_d, y_d, z_d, rx, ry, rz)
        robot = bytes.fromhex('01 00 00 00 00 00 00 00')
        speed_type = bytes.fromhex('01 00 00 00')
        speed = self.to_hex32(self.v_r)
        coor = self.to_hex32(16)
        xhex = self.to_hex32(x)
        yhex = self.to_hex32(y)
        zhex = self.to_hex32(z)
        rxhex = self.to_hex32(rx)
        ryhex = self.to_hex32(ry)
        rzhex = self.to_hex32(rz)
        behind = bytes.fromhex(
            '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 '
            '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 '
            '00 00 00 00 00 00 00 00 00 00 00 00')
        datas = robot + speed_type + speed + coor + xhex \
                + yhex + zhex + rxhex + ryhex + rzhex + behind
        datas = data + datas
        self.sock.sendto(datas, (self.UDP_IP, self.UDP_PORT))
        time.sleep(0.1)
        while self.Check_Pos(x_d, y_d, z_d) == 1:
            pass


    def to_int(self, x, y, z, a):
        re = a * (16 ** 6) + z * (16 ** 4) + y * (16 ** 2) + x
        if re > 2147483648:  # 2^31
            re = re - 16 ** 8
        return re


    def compare_pos(self, xc, yc, zc, x, y, z):
        xg, yg, zg, rxg, ryg, rzg = self.char2int(xc, yc, zc, 0, 0, 0)
        if abs(xg - x) < 100 and abs(yg - y) < 100 and abs(zg - z) < 100:
            return 0
        else:
            return 1


    def char2int(self, x, y, z, rx, ry, rz):
        x = int(float(x) * 1000)
        y = int(float(y) * 1000)
        z = int(float(z) * 1000)
        rx = int(float(rx) * 10000)
        ry = int(float(ry) * 10000)
        rz = int(float(rz) * 10000)
        return x, y, z, rx, ry, rz


    def to_hex32(self, z):
        if z < 0:
            z = z + 16 ** 8
        z1 = int(z / (16 ** 6))
        ztem = z - z1 * (16 ** 6)
        z2 = int(ztem / (16 ** 4))
        ztem = ztem - z2 * (16 ** 4)
        z3 = int(ztem / (16 ** 2))
        z4 = ztem - z3 * (16 ** 2)
        v1 = [z4, z3, z2, z1]
        bv = bytes(v1)
        return bv


    def to_hex16(self, z):
        if z < 0:
            z = z + 16 ** 8
        z1 = int(z / (16 ** 2))
        ztem = z - z1 * (16 ** 6)
        z2 = ztem - z1 * (16 ** 2)
        v1 = [z2, z1]
        bv = bytes(v1)
        return bv

    def to_hex8(self, z):
        if z < 0:
            z = z + 16 ** 8
        z1 = int(z / (16 ** 2))
        ztem = z - z1 * (16 ** 6)
        z2 = ztem - z1 * (16 ** 2)
        v1 = [z2]
        bv = bytes(v1)
        return bv   

z_inc = 4.0000
# Home position 1
xc = "185.0000"; yc = "-0.0040"; zc = "125.0000"; rx = "180.0000"; ry = "0.0000"; rz = "0.0000"; v_r = "500"
# Home position 2
xc2 = "250.0000"; yc2 = "0.0000"; zc2 = "0.0000"; zc2_test = "-20.0000"
# Conveyor Sensor
x2 = "250.0000"; y2 = "100.0000"; z2 = "-60.0000"
# Disk Sensor
x3 = "-36.0000"; y3 = "-250.0000"; z3 = "0.0000"# z3 = "-61.0000"