#!/bin/python3
from UPnPDevice import Device, getValue
import json
#test()
#print(test.sendAction(
#	'/VolumeService/control/',
#	'GetVolumeState',
#	{'uuid': '1'}))

#test = Device({"location": "http://192.168.0.2:49152/stbdevice.xml", "device_name": "Box", "baseURL": "http://192.168.0.2:49152"})
test = Device({"location": "http://192.168.1.254:49154/305a4f2b/gatedesc2a.xml", "device_name": "Sagemcom F@ST 5657", "baseURL": "http://192.168.1.254:49154/305a4f2b/"})
#test = Device({"location": "http://192.168.1.254:1990/7e20e062-7e5d-4bea-912c-fa7fc418c7c5/WFADevice.xml", "device_name": "Sagemcom F@ST 5657", "baseURL": "http://192.168.1.254:1990"})
test()
print(test.loadActions())


#print([getValue(x, 'direction') for x in test.getActionArguments('GetKeyboardInfo','/KeyboardService/control/')])
#print(test.sendAction(
#	'/upnp/control/Layer3Forwarding1',
#	'', 
#	{'NewMessage': 'Hello'}))