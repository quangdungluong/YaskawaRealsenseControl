from RobotControl import *

r = RobotControl()
a = bytes.fromhex('59') + r.to_hex16(12) + bytes.fromhex('06')
print(a)
def to_hex8(z):
    if z < 0:
        z = z + 16 ** 8
    z1 = int(z / (16 ** 2))
    ztem = z - z1 * (16 ** 6)
    z2 = ztem - z1 * (16 ** 2)
    v1 = [z2]
    bv = bytes(v1)
    return bv

print(to_hex8(1))
print(to_hex8(2))
print(to_hex8(7))
print(to_hex8(29))
print(to_hex8(31))