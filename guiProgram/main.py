#!/bin/python3
import PySimpleGUI as sg
from UPnPDevice import Device

import subprocess, os
import json
import requests, socket
from xml.etree import ElementTree

loading = True
loadedDevices = []
selectedDevice = None
device = []

def getDevices(window):
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
	count = 0
	while True:
		try:
			count += 1
			window['message'].update('Loading'+('.'*count))
			response, addr = ssdp_socket.recvfrom(1024)
			devices.append(response.decode('utf-8'))
			window.refresh()
		except socket.timeout:
			print("Timed out")
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
	window['message'].update('')

def loadingWindow():
	loadedDevices = globals()['loadedDevices']


	loadingLayout = [
		[
			sg.Text("UPnP options"),
		],
		[
			sg.Button("Load Devices", key="_LOAD_"),
			sg.Text("", key="message")
		],
		[
			sg.Listbox(
				values=[device["device_name"] for device in loadedDevices],
				enable_events=True, 
				size=(50, 10),
				key="-DEVICE LIST-",
				font=('Arial Bold', 10)
			),
		],
		[
			sg.Button("Quit!"),
			sg.Button("Refresh", key="_RESET DEVICES_"),
			sg.Push(),
			sg.Button('Select', key="_SELECT DEVICE_")
		]
	]
	window = sg.Window(layout=loadingLayout, title="Load Devices")
	while True:
		event, values = window.read()

		if event=="_LOAD_":
			loadedDevices = [device for device in getDevices(window)]
			globals()['loadedDevices'] = loadedDevices
			print(list(loadedDevices))
			devicesNames = [device["device_name"] for device in loadedDevices]
			window['-DEVICE LIST-'].update(devicesNames)

		if event == '-DEVICE LIST-':
			selected_value = values['-DEVICE LIST-'][0] if values['-DEVICE LIST-'] else 'None'
			window['message'].update(f'Selected device: {selected_value}')

		if event=='_RESET DEVICES_':
			loadedDevices = []
			globals()['loadedDevices'] = loadedDevices
			window['message'].update("Devices reseted")
			window['-DEVICE LIST-'].update(loadedDevices)

		if event=='_SELECT DEVICE_':
			selected_value = values['-DEVICE LIST-'][0] if values['-DEVICE LIST-'] else None
			if selected_value is None:
				window['message'].update('Select one device!')
			else:
				selected_value = [x for x in loadedDevices if x['device_name'] == selected_value][0]
				globals()['selectedDevice'] = selected_value
				break

		if event=="Quit!" or event==sg.WIN_CLOSED:
			break
	window.close()


def main():
	sg.theme('DarkGrey1')
	selectedDevice = globals()['selectedDevice']

	menu = [
		['Window', ['New', 'Refresh']],
		['Device', ['Select', 'Load']],
	]

	deviceTreeData = sg.TreeData()

	mainWindowlayout = [
		[
			sg.Menu(menu),
			sg.Text("UPnP console", font=('Roboto', 30))

		],
		[
			sg.Tree(key='-Device Tree-',
				auto_size_columns=True,
				headings=[],
				select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
				data=deviceTreeData,
				enable_events=True
				),
		],
		[
			sg.Text(f'Device: {selectedDevice}', key="_DEVICE_", font=('Roboto', 20))
		]
	]


	window = sg.Window(title="UPnP console", layout=mainWindowlayout)
	counter = 0 	# to force some options to be executed just once
	while True:
		selected_device = globals()['selectedDevice']
		event, values = window.read(timeout=100)
		if event=='Select Device' or globals()['selectedDevice'] is None:
			loadingWindow()
			window['_DEVICE_'].update('Device: '+ globals()['selectedDevice']['device_name'])

		if selected_device is not None and counter != 1:
			globals()['device'] = Device(selected_device)
			print("Hello world")
			for service in globals()['device'].services:
				print(service)
				deviceTreeData.Insert(service)
			window['-Device Tree-'].update(deviceTreeData)
			window.refresh()
			counter += 1

		if event=='Load':
			counter = 0
			print(globals()['device'])

		if event=='New':
			file_location = os.path.abspath(__file__)
			subprocess.Popen([file_location])

		if event=='Exit' or event==sg.WIN_CLOSED:
			break

	window.close()

if __name__ == '__main__':
	main()