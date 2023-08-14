#!/usr/bin/python3
import requests
import webbrowser
import sys
import xmltodict
import json
import xml.dom.minidom
from os import system
import html



#-------------------------------------------------------------------------#
#                                                                         #
#   Services: listed on the main page of the IOT or in a file.            #
#   Actions: each service has actions within it.                          #
#   Arguments: Every action has some arguments these are all              #
#              loaded from the web                                        #
#                                                                         #
#-------------------------------------------------------------------------#


options = {
    'commands_input': 'UPnP console> ',
    'files': {
        'servicesFile': 'services.json',
        'optionsFile': 'options.json',
        'responseFile': 'response.xml',
    },
    'UPnP_directory': 'UPnP/',
    'baseURL': "http://192.168.0.2:49152",
    'jsonIndent': 1,
    'service': '',
    'serviceAction': '',
    'storedServices': {},
}


def main():
    loadOptionsFromFile()
    while True:
        try:
            command = input(options['commands_input'].replace('>', ' ' + options['service'] + ' >'))
            if commands(command.split(' ')):
                continue
            else: 
                system(command)
        except Exception as e:
            print(f'Error: {e}')
        except KeyboardInterrupt:
            break
    # saveOptionstoFile()

def printj(text):
    print(json.dumps(text, indent=int(options['jsonIndent'])))

def commands(command):
    if command[0] == 'exit':
        exit()

    elif command[0] == 'send':
        if len(command) < 2:
            print('Missing arguments! Usage "send (actions of the service)" use "show services" to get all services available\nUse "show service actions" to list all service actions')
            return 1
        else:
            try:
                globals()['options']['serviceAction'] = command[1]
                send_soap_request(getService(options['service']))
            except Exception as e:
                print(f"Error: {e}")
                print(f"Unkown Service {options['service']}!")
        return 1

    elif command[0] == 'get':
        try:
            service = getService(command[1])
            printj(service)
            getFullServiceInformation()
            return 1
        except:
            print('Service not found! Use "show services" to list all services')
            return 1

    elif command[0] == 'set':
        if len(command) < 3:
            print('To few arguments! Usage "set (option) (value to set)"')
            return 1
        if command[1] == 'files':
            options['files'][command[2]] = command[3]
            return 1
        options[command[1]] = command[2]

    elif command[0] == 'unset':
        if len(command) < 2:
            print("Mising 1 argument, value to unset")
            return 1
        options.pop(command[1])

    elif command[0] == 'show':
        try:
            if command[1] == 'actions':
                    printj(getServiceActions())
            if command[1] == 'help':
                print("The following options are available\n\n\tshow options - \t show the options of the program (command_input, device url and so on) \n\tshow service - show the stored services that already got used\n\tshow actions - \tShow the actions available of the device\n\tshow services - \tEnumerates the services used in the actions listed in simpler way\n\tshow help - \t it shows this message\n")
            printj(globals()[command[1]])
        except KeyError:
            print('Option is not available! Use show help for more information')
        except IndexError:
            print("Missing arguments!")
        return 1
    else:
        return 0



def loadOptionsFromFile():
    try:
        with open(options['UPnP_directory']+options['files']['optionsFile']) as file:
            globals()['options'] = json.load(file)
    except: 
        print("Using default options!")



def saveOptionstoFile():
    print("Options Saved!")
    with open(options['UPnP_directory']+options['files']['optionsFile'], "w") as file:
        file.write(json.dumps(options, indent=int(options['jsonIndent'])))



def loadServicesFromWeb():
    r = requests.get(options['baseURL']+'/stbdevice.xml')
    xmlResponse = xmltodict.parse(r.content)
    with open(options['UPnP_directory']+options['files']['servicesFile'], 'w') as file:
        deviceInfo = xmlResponse.get('root').get('device')
        file.write(json.dumps(deviceInfo, indent=int(options['jsonIndent'])))



def getService(controURL):
    return [service for service in globals()['stbdevice']['serviceList']['service'] if service['controlURL'] == controURL][0]


def getServiceActions():
    # get service full information and then filter only the names of the actions
    fullServiceInformation = getFullServiceInformation()['scpd']['actionList']['action']
    serviceActions = fullServiceInformation if isinstance(fullServiceInformation, list) else [fullServiceInformation]
    try:
        return [action['name'] for action in serviceActions]
    except Exception as e:
        print(f"Error getting Actions: {e}")


def loadFile(fileLocation):
    try:
        with open(options['UPnP_directory']+fileLocation, "r") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        print("File does not exist!")
        raise FileNotFoundError


def loadServices():
    try:
        return loadFile(options['files']['servicesFile'])
    except FileNotFoundError:
        print('Actions File Not Found, loading actions from the web...')
        return loadServicesFromWeb()



def getFullServiceInformation():
    service = getService(options['service'])
    if service['serviceId'] in options['storedServices'].keys():
        return options['storedServices'][service['serviceId']]
    else:
        print("Using web")
        r = requests.get(options['baseURL']+service['SCPDURL'])
        response = xmltodict.parse(r.content)
        options['storedServices'][service['serviceId']] = response
        return response

def formArguments(action):
    arguments = ""
    while True:
        try:
            print("Use the following arguments available: ")
            printj(action['argumentList']['argument'])
            text = input("Input the argument and it's value (argument value): ")
            if 'send' in text:
                break
            text = text.split(' ')
            argument, value = text[0], "".join(text[1:])
            arguments += f"<{argument}>{value}</{argument}>"
            print("Use send to exit!")
        except Exception as e:
            print(e)
    return arguments

def formActionBody(service):
    serviceAction = options['serviceAction']
    fullServiceInformation = getFullServiceInformation()['scpd']['actionList']['action']
    serviceActions = fullServiceInformation if isinstance(fullServiceInformation, list) else [fullServiceInformation]
    try:
        verifiedAction = [action  for action in serviceActions if action['name'] == serviceAction][0]
        arguments = formArguments(verifiedAction)
        body = f'''
            <u:{verifiedAction['name']} xmlns:u="{getService(options['service'])['serviceType']}">
                {arguments}
            </u:{verifiedAction['name']}>
        '''
        return body
    except Exception as e:
        print(f"Error: {e}")
        return ''


def send_soap_request(service):
    fullServiceInformation = getFullServiceInformation()
    # SOAP request payload based on the service's SCPD
    soap_request = f'''<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
    s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
    {formActionBody(fullServiceInformation)}
    </s:Body>
</s:Envelope>
    '''
    print(soap_request)
    try:
        headers = {
            "Content-Type": "text/xml; charset=\"utf-8\"",
            "SOAPAction": f"\"{service['serviceType']}#{options['serviceAction']}\"",
        }
        printj(headers)

        response = requests.post(options['baseURL'] + service['controlURL'], data=soap_request, headers=headers)

        xml_str = xml.dom.minidom.parseString(response.text)
        xml_pretty = html.unescape(xml_str.toprettyxml())
        if response.status_code == 200:
            print("SOAP request sent successfully")
            print(xml_pretty)
        else:
            print(f"Failed to send SOAP request. Status code: {response.status_code}")
            print(xml_pretty)
        with open(options['files']['responseFile'], 'w') as file:
            file.write(xml_pretty)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # load actions from file or web
    globals()['stbdevice'] = loadServices()
    globals()['services'] = [x['controlURL'] for x in globals()['stbdevice']['serviceList']['service']]
    print("Full Services loaded, use 'show services' to see them or 'show stbdevice' to get full information.")
    main()
    saveOptionstoFile()
