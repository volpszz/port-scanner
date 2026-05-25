import socket
import sys
import time

rHost = input("Insert the target ip: ")
rHostIP = socket.gethostbyname(rHost)
rPorts = [53,22,80,111,139,443,32768]

print("-" *50)
print("be patient, scanning...", str(rHostIP))
print("-" *50)

try:


    for ports in rPorts:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(0.1)

        result = s.connect_ex((rHostIP,ports)) #if the port is open = 0, closed = 1

        if result == 0:
            print("port {} aberta! ".format(ports))
            s.close()

except KeyboardInterrupt:
    print("Program closed by the user! \n")
    sys.exit()


time.sleep(5)
 
