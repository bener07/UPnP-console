#!/bin/python3
import PySimpleGUI as sg
from UPnPDevice import Device

import subprocess, os
import requests, socket
from pprint import pprint
from xml.etree import ElementTree

loading = True
loadedDevices = []
selectedDevice = None
device = []
service = ''
action = ''

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
			window['message'].update('Loading...')
			window.refresh()
			response, addr = ssdp_socket.recvfrom(1024)
			devices.append(response.decode('utf-8'))
		except socket.timeout:
			print("Timed out")
			break
	# Parse and print discovered devices
	for device in devices:
		device = device.replace('Location', 'LOCATION')
		location = device.split('LOCATION:', 1)[1].split('\r\n', 1)[0].strip()
		response = requests.get(location)
		root = ElementTree.ElementTree(ElementTree.fromstring(response.content))
		device = {
			"location": location,
			"response": response,
			"device_name": root.find(".//{urn:schemas-upnp-org:device-1-0}friendlyName").text,
			"device_type" : root.find(".//{urn:schemas-upnp-org:device-1-0}deviceType").text,
		}
		try:
			urlBase = root.find('.//{urn:schemas-upnp-org:device-1-0}URLBase').text
		except:
			urlBase = "/".join(location.split('/')[:-1])+"/"
		device['baseURL'] = urlBase
		yield device
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
				globals()['device'] = Device(selected_value)
				break

		if event=="Quit!" or event==sg.WIN_CLOSED:
			break
	window.close()

def convert_dict_to_tree_data(deviceDict, dataTree, parent=''):
	for key, value in deviceDict.items():
		if isinstance(deviceDict[key], dict):
			dataTree.Insert(parent, key, key, value)
			convert_dict_to_tree_data(deviceDict[key], dataTree, key)
		else:
			dataTree.Insert(parent, key, key, value)
	return dataTree

def loadDeviceTree(device):
	dataTree = sg.TreeData()
	if device == []:
		return dataTree
	dataTree = convert_dict_to_tree_data(device.toDict(), dataTree)
	return dataTree


def sendEvent(device):
	service = globals()['service']
	action = globals()['action']
	action = device.services.get(service).actions.get(action)
	argumentLayout = [
		[sg.Text('Arguments')],
	]
	try:
		if action is None:
			action = device.services.get(service).actions.get(action)
		argLayout = []
		print(action.argument)
		if isinstance(action.argument, list):
			for argument in action.argument:
				print(argument)
				direction = argument.get('direction')
				name = argument.get('name')
				argLayout.append([sg.Text(f'Direction: {direction}\nName: {name}')])
				if argument['direction'] == 'in':
					argLayout.append(sg.Input(key=name))
			print(argLayout)
			argumentLayout.append(argLayout)
		else:
			direction = action.argument.get('direction')
			name = action.argument.get('name')
			argLayout = [sg.Text(f'Direction: {direction}\nName: {name}')]
			if action.argument.get('direction') == 'in':
				argLayout.append([sg.Text("Value for {}".format(name)), sg.Push(), sg.Input(key=name)])
			argumentLayout.append(argLayout)
	except Exception as e:
		print("something went widely wrong, here's the action\n", e)
	argumentLayout.append([sg.Button('Send!', key='SEND')])
	argwindow = sg.Window('Define your Arguments!', resizable=True, layout=argumentLayout)
	while True:
		event, values = argwindow.read()
		if event=='SEND':
			# the send returns a string and this is suppose to print it
			for name, value in values.items():
				action.setArg(name, value)
			print(action.send())
			break
		if event=='Exit' or event==sg.WIN_CLOSED:
			break

	argwindow.close()




def main():
	sg.theme('DarkBlue2')
	selectedDevice = globals()['selectedDevice']
	deviceTreeData = sg.TreeData()

	# define the menu
	menu = [
		['Window', ['New', 'Refresh']],
		['Device', ['Info','Select', 'Load']],
	]

	# set the main layout
	mainWindowlayout = [
		[
			sg.Menu(menu),
			sg.Text("UPnP console", font=('Roboto', 30))

		],
		[
			sg.Text(f'Device: {selectedDevice}', key="_DEVICE_", font=('Roboto', 20))
		],
		[
			sg.Tree(key='-Device Tree-',
				auto_size_columns=True,
				headings=[],
				select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
				data=loadDeviceTree(globals()['device']),
				enable_events=True,
				expand_x=True,
				expand_y=True,
				show_expanded=False,
				),
			sg.Output(s=(100, 30), key='-OUTPUT-')
		],
		[sg.Text("Select a service and an action to then send it", key='message')],
		[
			sg.Text("Service: None", key='-SELECTED SERVICE-'),
			sg.Push(),
			sg.Button('Send', key='-SEND-')
		],
		[sg.Text("Action: None", key='-SELECTED ACTION-')]
	]

	# initiate the window
	window = sg.Window(title="UPnP console", layout=mainWindowlayout, resizable=True)
	counter = 0 	# to force some options to be executed just once
	# start the window loop
	while True:
		selected_device = globals()['selectedDevice']
		event, values = window.read(timeout=100)
		if event=='Select Device' or globals()['selectedDevice'] is None:
			loadingWindow()
			window['_DEVICE_'].update('Device: '+ globals()['selectedDevice']['device_name'])

		# in case the device selected and it's not necessary to load it again
		if selected_device is not None and counter != 1:
			deviceTree = loadDeviceTree(globals()['device'])
			window['-Device Tree-'].update(deviceTree)
			window.refresh()
			counter += 1

		if event == 'Info':
			sg.Popup(str(globals()['device']), keep_on_top=True)

		# shows the loading window in case the user wants to set a new device
		if event=='Load':
			counter = 0
			loadingWindow()
			window['_DEVICE_'].update('Device: '+ globals()['selectedDevice']['device_name'])

		# in case the user wants a new window it creates a new process for it
		if event=='New':
			file_location = os.path.abspath(__file__)
			subprocess.Popen([file_location])

		if event=='-Device Tree-':
			selected_value = values['-Device Tree-'][0] if values['-Device Tree-'] else None
			window['-OUTPUT-'].update('')
			try:
				selected_value = window.Element('-Device Tree-').TreeData.tree_dict[selected_value]
			except:
				selected_value = window.Element('-Device Tree-').TreeData.tree_dict[0]

			if selected_value.parent == 'services':
				globals()['service'] = selected_value.key
				window.Element('-SELECTED SERVICE-').update('Service: '+globals()['service'])

			elif selected_value.parent=='actions':
				globals()['action'] = selected_value.key
				window.Element('-SELECTED ACTION-').update('Action: '+globals()['action'])
			else:
				window.Element('-SELECTED ACTION-').update('Action: '+globals()['action'])
				window.Element('-SELECTED SERVICE-').update('Service: '+globals()['service'])
			pprint(selected_value.values)
		
		if event=='-SEND-':
			service = globals()['service']
			action = globals()['action']
			if service != '' and action != '':
				sendEvent(Device(selected_device))
				#print(globals()['device'])
			else:
				window.Element('message').update('Please select a service and action to send it!')

		if event=='Exit' or event==sg.WIN_CLOSED:
			break
		window.refresh()
	window.close()

if __name__ == '__main__':
	main()