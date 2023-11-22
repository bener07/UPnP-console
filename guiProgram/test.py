from UPnPDevice import Device
from UPnPDevice import printj
from UPnPDevice import Service 
import xmltodict

deviceDict = {
      'location': 'http://192.168.1.254:49154/42337661/gatedesc2a.xml',
      'baseURL': 'http://192.168.1.254:49154/42337661/',
      'device_name': 'Sagemcom F@ST 5657',
      'device_type': 'urn:schemas-upnp-org:device:InternetGatewayDevice:2'
   }

#device = Device(
#   deviceDict
#)
service = Service(deviceDict)
print(service.information())