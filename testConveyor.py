from UART import *

s = serial.Serial('COM4', 9600, timeout=0.0001)
uart = ReadFromSerial(s)
while(1):
    # print()
    a = int(input())
    if (a==1):
        s.write(b'1')
        print(float(uart.read_one_struct())*10)
        s.close()