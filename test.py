import socket
import sys
dst = "192.168.0.2"
if len(sys.argv) > 1:
    dst = sys.argv[1]
st = "upnp:rootdevice"
if len(sys.argv) > 2:
    st = sys.argv[2]
msg = [
    'NOTIFY * HTTP/1.1',
    'Host:239.255.255.250:1900',
    'NT:'+st,
    'Man:"ssdp:discover"',
    'MX:20',
    '']
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
s.sendto('\r\n'.join(msg).encode()+b'\r\n', (dst, 1900) )
try:
    data, addr = s.recvfrom(32*1024)
except socket.timeout:
    print("Timeout")
    exit()
print("[+] %s\n%s" % (addr, data.decode()))
