#!/bin/python3
import curses
from discover import getDevices
from UPnPDevice import Device
import json

options = {
	'commands_input': 'UPnP console> ',
	'files': {
		'servicesFile': 'services.json',
		'optionsFile': 'options.json',
		'responseFile': 'response.xml',
	},
	'UPnP_directory': 'UPnP/',
	'service': '',
	'arguments': {},
}


def writeMenu(stdscr, menu_items, selected_item):
	for i, item in enumerate(menu_items):
			if i == selected_item:
				stdscr.addstr(i, 0, f"> {item}", curses.A_REVERSE)
			else:
				stdscr.addstr(i, 0, f"  {item}")


def sendMenu(stdscr, device, action):
	curses.curs_set(0)
	stdscr.clear()
	message = ""
	menu_items =  [x.getElementsByTagName('name')[0].firstChild.nodeValue for x in device.getActionArguments(action, options['service'])]
	menu_items.append('Go Back')
	menu_items.append('Send!')
	selected_line = len(menu_items) + 1
	selected_item = 0
	text_lines = []
	inputingValue = False
	options['arguments'] = {}

	while True:
		try:

			stdscr.clear()



			# Render the menu items
			writeMenu(stdscr, menu_items, selected_item)

			# Display the selected item separately
			stdscr.addstr(selected_line, 0, f"Argumetns to send: {str(options['arguments'])}", curses.A_BOLD)
			stdscr.addstr(selected_line+2, 0, f"Service in use: {str(options['service'])}")
			stdscr.addstr(selected_line+5, 0, str(message))

			# Get user input
			key = stdscr.getch()
			selection = menu_items[selected_item]
			# Handle user input
			if key == curses.KEY_DOWN:
				selected_item = (selected_item + 1) % len(menu_items)
				# Clear the previous selected item message
				stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
			elif key == curses.KEY_UP:
				selected_item = (selected_item - 1) % len(menu_items)
				# Clear the previous selected item message
				stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
			if inputingValue:
				if selection == 'Send!':
					return device.sendAction(options['service'], action, options['arguments'])
				if key == curses.KEY_BACKSPACE and options['arguments'][selection]!='':
				 	options['arguments'][selection] = options['arguments'][selection][:-1]
				if key >= 32 and key <= 126 or key == ord('\n'):
					try:
					 	options['arguments'][selection] += chr(key)
					except:
					 	options['arguments'][selection] = chr(key)
					finally:
					 	options['arguments'][selection] = options['arguments'][selection].replace('\n', '').replace(chr(curses.KEY_BACKSPACE), '')
				if key == ord('\n'):
					inputingValue = not inputingValue
					message += '\nArgument saved!\n'

			elif key == ord('\n'):
				if selection == 'Send!':
					return device.sendAction(options['service'], action, options['arguments'])
				try:
					options['arguments'][selection]
				except:
					options['arguments'][selection] = ''
				message = "Press enter to send and move the arrows to write in other arguments\nValue: "+str(options['arguments'][selection])
				inputingValue = not inputingValue


			# Refresh the screen
			stdscr.refresh()
		except KeyboardInterrupt:
			break


def serviceMenu(stdscr, device):
	curses.curs_set(0)
	stdscr.clear()
	message = ""
	menu_items = device.getRawAttr('services')
	menu_items.append('Go Back')
	selected_line = len(menu_items) + 1
	selected_item = 0
	if options['service'] != '':
		selected_item = menu_items.index(options['service'])
	while True:
		stdscr.clear()


		# Render the menu items
		writeMenu(stdscr, menu_items, selected_item)

		# Display the selected item separately
		stdscr.addstr(selected_line, 0, f"Selected Service: {menu_items[selected_item]}", curses.A_BOLD)
		stdscr.addstr(selected_line+5, 0, str(message))
		stdscr.addstr(selected_line+2, 0, f"Service in use: {str(options['service'])}")

		# Get user input
		key = stdscr.getch()

		# Handle user input
		if key == curses.KEY_DOWN:
			selected_item = (selected_item + 1) % len(menu_items)
			# Clear the previous selected item message
			stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
		elif key == curses.KEY_UP:
			selected_item = (selected_item - 1) % len(menu_items)
			# Clear the previous selected item message
			stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
		elif key == ord('\n'):
			# Erase the selected item message
			selection = menu_items[selected_item]
			if selection != "Go Back":
				globals()['options']['service'] = selection
			break

		# Refresh the screen
		stdscr.refresh()

def deviceMenu(stdscr, device):
	curses.curs_set(1)
	stdscr.clear()
	message = ""
	menu_items = [
		"Load All Device",
		"Show Services",
		"Show Actions",
		"Send Actions",
		"Select Service",
		"Help",
		"Go Back"
	]
	selected_item = 0
	backup_menu = []
	selected_line = len(menu_items) + 1

	while True:
		stdscr.clear()

		# Render the menu items
		writeMenu(stdscr, menu_items, selected_item)

		# Display the selected item separately
		stdscr.addstr(selected_line, 0, f"Selected Option: {menu_items[selected_item]}", curses.A_BOLD)
		stdscr.addstr(selected_line+5, 0, str(message))
		stdscr.addstr(selected_line+2, 0, f"Service in use: {str(options['service'])}")
		stdscr.addstr(selected_line+3, 0, str(device))

		# Get user input
		key = stdscr.getch()

		# Handle user input
		if key == curses.KEY_DOWN:
			selected_item = (selected_item + 1) % len(menu_items)
			# Clear the previous selected item message
			stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
		elif key == curses.KEY_UP:
			selected_item = (selected_item - 1) % len(menu_items)
			# Clear the previous selected item message
			stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
		elif key == ord('\n'):
			# Erase the selected item message
			selection = menu_items[selected_item]
			if selection == "Load All Device":
				device()
				message = "Device Loaded!"
			elif selection == "Select Service":
				serviceMenu(stdscr, device)
			elif selection == "Show Services":
				message = json.dumps(device.getRawAttr('services'), indent=2)
			elif selection == "Show Actions":
				try:
					message = json.dumps(device.getServiceActions(options['service']), indent=2)
				except:
					message = "Sorry you haven't select a service :("
			elif selection == "Send Actions":
				try:
					backup_menu = menu_items
					menu_items =  device.getServiceActions(options['service'])
					menu_items.append('Go Back')
					selected_line = len(menu_items) + 1
					selected_item = 0
				except:
					message = "Sorry you haven't select a service :("
			elif selection in device.getRawAttr('actions'):
				message = sendMenu(stdscr, device, selection)
			elif selection == "Help":
				message = ""+\
				"""This are the options available:
- "Load All Device"
	- It Loads the devices services and actions, in case you need it to

- "Show Services"
	- Shows the services that got from the IoT device

- "Show Actions"
	- Shows the actions of all the services form the IoT device

- "Send Actions"
	- Forms a SOAP request and sends it to the service route

- "Select Service"
	- Selects the Service to use.

				"""
			elif selection == "Go Back":
				if backup_menu != []:
					menu_items = backup_menu
					backup_menu = []
					selected_item = 0
					selected_line = len(menu_items) + 1
				else:
					break

		# Refresh the screen
		stdscr.refresh()

		if key == ord('q'):
			break


def main(stdscr):
	curses.curs_set(1)  # Hide the cursor
	stdscr.clear()
	message = ""
	message_attribute = curses.A_DIM

	devices = list(getDevices())
	# Create a list of menu items
	menu_items = [x['device_name'] for x in devices]
	selected_item = 0  # Index of the currently selected item

	# Create a separate line for displaying the selected item
	selected_line = len(menu_items) + 1

	while True:
		stdscr.clear()
		options['service'] = ""

		# Render the menu items
		for i, item in enumerate(menu_items):
			if i == selected_item:
				stdscr.addstr(i, 0, f"> {item}", curses.A_REVERSE)
			else:
				stdscr.addstr(i, 0, f"  {item}")

		# Display the selected item separately
		stdscr.addstr(selected_line, 0, f"Selected device: {menu_items[selected_item]}", curses.A_BOLD)
		stdscr.addstr(selected_line+5, 0, str(message), message_attribute)

		# Get user input
		key = stdscr.getch()

		# Handle user input
		if key == curses.KEY_DOWN:
			selected_item = (selected_item + 1) % len(menu_items)
			# Clear the previous selected item message
			stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
		elif key == curses.KEY_UP:
			selected_item = (selected_item - 1) % len(menu_items)
			# Clear the previous selected item message
			stdscr.addstr(selected_line, 0, " " * (stdscr.getmaxyx()[1] - 1))
		elif key == ord('\n'):
			# Erase the selected item message
			device = [ x  for x in devices if x['device_name']==menu_items[selected_item]][0]
			device = Device(device)
			device()
			deviceMenu(stdscr, device)

		# Refresh the screen
		stdscr.refresh()

		if key == ord('q'):
			break

while True:
	try:
		curses.wrapper(main)
	except Exception as e:
		print(json.dumps(options, indent=3))
		print(f"Your response was probably to big, but here's the.\nError: {e}")
		exit()
	except KeyboardInterrupt:
		print("Bye!")
		exit()
