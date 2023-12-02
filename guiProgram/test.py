from UPnPDevice import Device
import requests
deviceDict = {
    "location": "http://192.168.1.1:2555/upnp/InternetGatewayDevice:2/desc.xml",
    "baseURL": "http://192.168.1.1:2555",
    "device_name": "NOS CPE Device",
    "device_type": "urn:schemas-upnp-org:device:InternetGatewayDevice:2"
}

device = Device(deviceDict)
action = device.services.get('/upnp/InternetGatewayDevice:2/Layer3Forwarding1.ctl').actions.get('GetDefaultConnectionService')
print(action.args())