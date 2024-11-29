import requests
import json

def create_workstation(identifier, latitude, longitude, description):
    url = "http://localhost:8000/create"
    headers = {"Content-Type": "application/json"}


    payload = {
        "identifier": identifier,
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "description": description
    }

    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Print the response status code and body
        print("Status Code:", response.status_code)
        print("Response Body:", response.json())

        # Check for success
        if response.status_code == 200:
            print("Worksite created successfully!")
        else:
            print("Failed to create worksite.")

    except requests.exceptions.RequestException as e:
        print("An error occurred while sending the request:", e)



identifier = input("what is the name of the site: ")
longitude = float(input(f"What is the longitude of {identifier}: "))
latitude = float(input(f"What is the latitude of {identifier}: "))
description = input("Describe your worksite: ")

create_workstation(identifier, longitude, latitude, description);