import requests

soap_request = '''<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:GetWANAccessProvider xmlns:u="urn:schemas-upnp-org:service:WANPPPConnection:1">
        </u:GetWANAccessProvider>
    </s:Body>
</s:Envelope>
'''

headers = {
    "Content-Type": 'text/xml; charset=\"utf-8\"',
    'SOAPAction': '"urn:schemas-upnp-org:service:WANPPPConnection:1#GetWANAccessProvider"'
}

url = 'http://192.168.1.254:49154/upnp/control/WANPPPConnection1'

r = requests.post(url, headers=headers, data=soap_request)

print(r.text)
