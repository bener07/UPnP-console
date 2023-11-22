import socket, requests
import json
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
		self.baseURL = device['baseURL']
		self.location = device['location']
		self.name = device['device_name']
		self.actions = dict()
		self.services = dict()
		self.responseFile = 'response.xml'
		self.action_arguments = dict()


	def __str__(self):
		return f"Name: {self.name}\nlocation: {self.location}\nbase url:{self.baseURL}"

	def __len__(self):
		return len(self.services)+len(self.actions)

	def __dict__(self):
		return self.services.keys()

	def __call__(self):
		print("Called")
		#self.loadServices()
		#self.loadActions()

	def analyzeURL(self):
		location_url = self.location.split('/')
		baseURL = self.baseURL.split('/')
		if '.xml' not in location_url[3] or location_url[3] == baseURL[0]:
			baseURL.insert(3, location_url[3])
		self.baseURL = "/".join(baseURL)

	def getActionArguments(self, actionName, service):
		url = self.__makeURL(self.services[service])
		try:
			response = requests.get(url)
		except:
			url = (self.baseURL+'/'+getValue(self.services[service], 'SCPDURL')).replace('//', '/').replace(':/', '://')
			print(url)
			response = requests.get(url)
		actionPage = xml.parseString(response.content)
		getArguments = lambda action: [x for x in action.getElementsByTagName('argument') if getValue(x, 'direction') == 'in']
		action = [x for x in actionPage.getElementsByTagName('action') if getValue(x, 'name') == actionName ][0]
		return getArguments(action)

	def __formArguments(self):
		return_arguments = ""
		for argument in self.action_arguments:
			try:
				argument, value = argument
				return_arguments += f"<{argument}>{value}</{argument}>"
			except Exception as e:
				print(e)
		return return_arguments


	def send(self, service, action, arguments):
		# SOAP request payload based on the service's SCPD
		soap_request = f'''<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
		s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
		<s:Body>
		{self.__formActionBody(self.services[service], self.actions[action])}
		</s:Body>
		</s:Envelope>
		'''
		print(soap_request)
		try:
			headers = {
				"Content-Type": "text/xml; charset=\"utf-8\"",
				"SOAPAction": f"\"{getValue(self.services[service], 'serviceType')}#{action}\"",
			}
			# get the action route
			request_page = getValue(self.services[service], 'controlURL')
			url = (self.baseURL+'/'+request_page)
			url = self.__filter_url(url)

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

	def __filter_url(self, url):
		splitURL = url.split('/')
		for string in splitURL:
			indexLocation = splitURL.index(string)
			for checkString in splitURL:
				if string == checkString and indexLocation != splitURL.index(checkString):
					splitURL.remove(checkString)
		url = "/".join(splitURL)
		return (url).replace('///', '/').replace('//', '/').replace(':/', '://')

	def __scdURL(self, xmlobj, valueToSearch):
		page = getValue(xmlobj, valueToSearch)
		return self.__filter_url(self.baseURL+'/'+page)


	def __makeURL(self, xmlobj):
		page = getValue(xmlobj, 'SCPDURL')
		url = ""
		try:
			if page.split('/')[1] == self.baseURL.split('/')[3]:
				page = "".join(page.split('/')[-1])
		except:
			url
		url = self.baseURL+"/"+page
		return self.__filter_url(url)

	def loadActions(self):
		if self.services == {}:
			self.loadServices()
		for service in self.services:
			url = self.__makeURL(self.services[service])
			try:
				response = requests.get(url)
			except:
				print(url)
				response = requests.get(url)
			actionPage = xml.parseString(response.content)
			for action in actionPage.getElementsByTagName('action'):
				self.actions[getValue(action, 'name')] = action
		return self.actions

	# Load services from the device
	def loadServices(self):
		services = self.root.getElementsByTagName('service')
		for service in services:
			service = xmltodict.parse(service.toprettyxml()).get('service')
			service.update({'baseURL': self.baseURL})
			self.services[service['controlURL']] = Service(service)
		return services


	def __getService(self, controlURL):
		return [self.services[x] for x in self.services if getValue(self.services[x], 'controlURL') == controlURL][0]

	def __getFullServiceInformation(self, controURL):
		service = self.__getService(controURL)
		url = (self.baseURL+getValue(service, 'SCPDURL')).replace('//', '/').replace(':/', '://')
		try:
			r = requests.get(url)
		except:
			url = (self.baseURL+'/'+getValue(service, 'SCPDURL')).replace('//', '/').replace(':/', '://')
			r = requests.get(url)
		response = xml.parseString(r.content)
		# options['storedServices'][service['serviceId']] = response
		response = [x for x in response.getElementsByTagName('action')]
		return response

	def getServiceActions(self, controURL):
		fullServiceInformation = self.__getFullServiceInformation(controURL)
		serviceActions = fullServiceInformation if isinstance(fullServiceInformation, list) else [fullServiceInformation]
		try:
			return [getValue(action, 'name') for action in serviceActions]
		except Exception as e:
			print(f"Error getting Actions: {e}")



class Service:
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
		url = re.sub(r'(?<!http:)/+', '/', url)
		servicePage = requests.get(url)
		servicePage = xml.parseString(servicePage.text)
		actions = {}
		for action in servicePage.getElementsByTagName('action'):
			action = xmltodict.parse(action.toprettyxml()).get('action')
			actions[action.get('name')] = Action(action.get('name'),action.get('argumentList'))
		return actions

class Action(Service):
	def __init__(self, actionName, arguments):
		self.name = actionName
		if not isinstance(arguments, dict):
			raise TypeError("Arguments are not of type dictionary")
		for key, value in arguments.items():
			setattr(self, key, value)
		self.userArguments = list()

	def __formArguments(self):
		return_arguments = ""
		for argument, value in self.args():
			try:
				return_arguments += f"<{argument}>{value}</{argument}>"
			except Exception as e:
				print(e)
		return return_arguments

	def __formBody(self):
		arguments = self.__formArguments()
		body = f'''	<u:{getValue(action, 'name')} xmlns:u="{getValue(service, 'serviceType')}">
			{arguments}
		</u:{getValue(action, 'name')}>'''
		return body

	def args(self):
		return [(arg, getattr(self, arg)) for arg in vars(self)]

	def setArg(self, argument, value):
		self.userArguments.append(Argument(argument, value))



class Argument(Action):
	def __init__(self, argument, value):
		self.argument = argument
		self.value = value