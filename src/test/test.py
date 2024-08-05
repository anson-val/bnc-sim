import galois
GF256 = galois.GF(2 ** 8)
x = GF256([[236, 87, 38, 112], [123,22,223,32]])
print(x[0][1])