#!/bin/python3
import requests, socket
import multiprocessing
import sys, time, itertools, webbrowser, inquirer, webbrowser, json
from UPnPDevice import Device
from xml.etree import ElementTree
from pprint import pprint

def printj(text):
    print(json.dumps(text, indent=2))

globals()['done'] = False
manage_animation = multiprocessing.Value('i', 0)


def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if manage_animation.value == 1:
            sys.stdout.flush()
            break
        sys.stdout.write('\rloading ' + c)
        sys.stdout.flush()
        time.sleep(0.1)

def showMenu(options, message):
    questions = [
        inquirer.List("option",
            message=message,
            choices=options)
        ]
    return inquirer.prompt(questions)

def main():
    devices = list(getDevices())
    questions = [
        inquirer.List("device",
            message="Select device",
            choices=[x['device_name'] for x in devices],
            ),
    ]
    answer = inquirer.prompt(questions)
    device = [ x  for x in devices if x['device_name']==answer['device']][0]
    device = Device(device)
    options = [
        "Load",
        "Select Services",
        "Show Services",
        "Show Actions",
        "Exit"
    ]
    while True:
        answer = showMenu(options, "Select Option")
        
        if answer['option'] == "Load":
            device()
        
        if answer['option'] == "Select Service":
            handleServices()
        
        if answer['option'] == "Show Services":
            printj(device.getAttr('services'))
        
        if answer['option'] == "Show Actions":
            printj(device.getAttr('actions'))
        
        if answer['option'] == "Exit":
            break


def getDevices():
    process = multiprocessing.Process(target=animate)
    process.start()

    ssdp_request = (
        'M-SEARCH * HTTP/1.1\r\n'
        'HOST: 239.255.255.250:1900\r\n'
        'MAN: "ssdp:discover"\r\n'
        'MX: 2\r\n'
        'ST: upnp:rootdevice\r\n\r\n'
    )

    # Send the request and receive responses
    ssdp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ssdp_socket.settimeout(2)
    ssdp_socket.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
    devices = []
    while True:
        try:
            response, addr = ssdp_socket.recvfrom(1024)
            devices.append(response.decode('utf-8'))
        except socket.timeout:
            break
    # Parse and print discovered devices
    for device in devices:
        device = device.replace('Location', 'LOCATION')
        location = device.split('LOCATION:', 1)[1].split('\r\n', 1)[0].strip()
        response = requests.get(location)
        root = ElementTree.ElementTree(ElementTree.fromstring(response.content))
        yield {
            "location": location,
            "baseURL": "/".join(location.split('/')[:-1])+"/",
            "response": response,
            "device_name": root.find(".//{urn:schemas-upnp-org:device-1-0}friendlyName").text,
            "device_type" : root.find(".//{urn:schemas-upnp-org:device-1-0}deviceType").text,
        }
    manage_animation.value = 1

if __name__ == "__main__":
    main()