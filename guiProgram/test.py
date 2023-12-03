import requests

# Set up headers for the SUBSCRIBE request
headers = {
    "HOST": "http://192.168.1.1:2555/",  # Extract the host from the URL
    "CALLBACK": f"<http://192.168.1.6:8080>",  # Specify your callback URL
    "NT": "upnp:event",
    "TIMEOUT": "Second-300"  # Specify the timeout duration
}

# Send the SUBSCRIBE request
response = requests.subscribe(full_event_sub_url, headers=headers)

if response.status_code == 200:
    print("Successfully subscribed to events.")
    print(f"Subscription ID: {response.headers.get('SID')}")
else:
    print(f"Failed to subscribe to events. Status code: {response.status_code}")

