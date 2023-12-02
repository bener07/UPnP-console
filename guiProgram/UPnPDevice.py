import socket, requests
import json
from xml.dom.minidom import *
import xml.dom.minidom as xml
import xmltodict
import html
import re

def loadFile(fileLocation):
	try:
		with open(options['UPnP_directory']+fileLocation, "r") as file:
			return json.loads(file.read())
	except FileNotFoundError:
		print("File does not exist!")
		raise FileNotFoundError
		return FileNotFoundError

def getValue(service, valueToSearch):
	return service.getElementsByTagName(valueToSearch)[0].firstChild.nodeValue

def printj(text, jsonident=2):
    print(json.dumps(text, indent=int(jsonident)))



class Device:
	def __init__(self, device):
		response = requests.get(device['location'])
		self.root = xml.parseString(response.content)
		self.services = dict()
		self.responseFile = 'response.xml'
		for key, value in device.items():
			setattr(self, key, value)
		self.__call__()


	def __str__(self):
		return f"Name: {self.device_name}\nlocation: {self.location}\nbase url:{self.baseURL}"

	def __len__(self):
		return len(self.services)+len(self.actions)
	
	def __call__(self):
		self.loadServices()

	def toDict(self):
		deviceDict = {}
		for var in vars(self):
			try:
				if var == 'root' or var=='response':
					pass
				else:
					deviceDict[var] = getattr(self, var) if getattr(self, var) is not None else 'None'
				for key, value in deviceDict[var].items():
					deviceDict[var][key] = value.toDict()
			except:
				pass
		return deviceDict

	# Load services from the device
	def loadServices(self):
		services = self.root.getElementsByTagName('service')
		for service in services:
			service = xmltodict.parse(service.toprettyxml()).get('service')
			service.update({'baseURL': self.baseURL})
			self.services[service['controlURL']] = Service(service)
		return services


class Service(Device):
	def __init__(self, service):
		if not isinstance(service, dict):
			raise TypeError('Service is not of type dictionary')
		for key, value in service.items():
			setattr(self, key, value)
		self.actions = self.loadActions()

	def information(self):
		return [(var, getattr(self, var)) for var in vars(self)]


	def __str__(self):
		return "".join([f"{var}: {value}\n" for var, value in self.information()])


	def loadActions(self):
		url = self.baseURL+self.SCPDURL
		url = self.filter_url(url)
		r = requests.get(url, headers={"Accept": '*/*'})
		servicePage = xml.parseString(r.text)
		# print(servicePage.toprettyxml(), r.headers)
		actions = {}
		for action in servicePage.getElementsByTagName('action'):
			action = xmltodict.parse(action.toprettyxml()).get('action')
			argumentList = action.get('argumentList')
			actionName = action.get('name')
			actions[action.get('name')] = Action(actionName, argumentList, service=self)
		return actions

	def filter_url(self, url):
		url = re.sub(r'(?<!http:)/+', '/', url)
		schema, url = url.split('//')
		previous = ''
		for string in url.split('/'):
			stringLocation = url.find(string)
			if previous == string:
				filtered_url = url.split('/')
				filtered_url.remove(string)
				url = "/".join(filtered_url)
			previous = string
		return "//".join((schema, url))

class Action(Service):
	def __init__(self, actionName, arguments, service=None):
		self.name = actionName
		self.userArguments = list()
		self.service = service
		if not isinstance(arguments, dict) and arguments is not None:
			raise TypeError("Arguments are not of type dictionary")
		if arguments is None:
			pass
		else:
			for key, value in arguments.items():
				setattr(self, key, value)

	def args(self):
		return self.argument

	def setArg(self, argument, value):
		self.userArguments.append(Argument(argument, value))
		return self.userArguments

	def __formActionBody(self):
		service = self.service
		action = self
		arguments = self.__formArguments()
		body = f'<u:{action.name} xmlns:u="{service.serviceType}">\n'+\
				f'{arguments}'+\
			f'\t\t</u:{action.name}>\n'
		return body


	def __formArguments(self):
		return_arguments = ""
		for argument in self.userArguments:
			try:
				return_arguments += f"\t\t\t<{argument.name}>{argument.value}</{argument.name}>\n"
			except Exception as e:
				print(e)
		return return_arguments


	def send(self):
		service = self.service
		action = self
		# SOAP request payload based on the service's SCPD
		soap_request = f'<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '+\
		's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n'+\
		'\t<s:Body>\n'+\
		f'\t\t{self.__formActionBody()}'+\
		'\t</s:Body>\n'+\
		'</s:Envelope>'
		print(soap_request)
		try:
			headers = {
				"Content-Type": "text/xml; charset=\"utf-8\"",
				"SOAPAction": f"\"{service.serviceType}#{action.name}\"",
			}
			# get the action route
			request_page = service.controlURL
			url = (service.baseURL+'/'+request_page)
			url = self.filter_url(url)

			response = requests.post(url, data=soap_request, headers=headers)
			xml_str = xml.parseString(response.text)
			xml_pretty = html.unescape(xml_str.toprettyxml())
			if response.status_code == 200:
				print("SOAP request sent successfully")
				return xml_pretty
			else:
				print(f"Failed to send SOAP request. Status code: {response.status_code}")
				return xml_pretty
			with open(self.responseFile, 'w') as file:
				file.write(xml_pretty)

		except requests.exceptions.RequestException as e:
			print(f"An error occurred: {e}")
			return f"something went wrong: {e}"


class Argument(Action):
	def __init__(self, name, value):
		self.name = name
		self.value = value