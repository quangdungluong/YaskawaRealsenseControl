from UART import *

s = serial.Serial('COM4')
uart = ReadFromSerial(s)
while(1):
    # print()
    a = int(input())
    if (a==1):
        try:
            s.open()
        except:
            print("already opened")
        print(float(uart.read_one_struct())*10)
        s.close()