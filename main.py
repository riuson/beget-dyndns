#!/usr/bin/env python

# Read from environment:
# - IP Address detection url;
# - domain names;
# - login;
# - password.
# Get IP Address.
# Send API request to update IP.

# Beget API Docs:
#   https://beget.com/ru/kb/api/funkczii-upravleniya-dns


import json
import os

import requests
from requests import get
import urllib.parse

# Array of domain names.
domains = os.environ['DOMAINS'].split(',')

# Login on Beget.
beget_login = os.environ['BEGET_LOGIN']

# Password on Beget.
beget_password = os.environ['BEGET_PASSW']

# Url to get external IP Address.
get_ip_url = os.environ['GET_IP_URL']


# Gets external IP Address.
def get_external_ip_address() -> str:
    result = get(get_ip_url).content.decode('utf8')
    print('Our external IP address is: {}'.format(result))
    return result


# Creates Data parameter.
def create_json_data(
    domain_name: str,
    ip_address: str) -> str:
    data = {
        "fqdn": domain_name,
        "records": {
            "A": [
                {
                    "priority": 10,
                    "value": ip_address
                }
            ]
        }
    }
    result = json.dumps(data, separators=(',', ':'))
    return result


# Sends request.
def send_request(data: str) -> requests.Response:
    response = get(
        'https://api.beget.com/api/dns/changeRecords',
        params={
            'login': beget_login,
            'passwd': beget_password,
            'input_format': 'json',
            'output_format': 'json',
            'input_data': data
        },
    )

    return response


# Main.
if __name__ == '__main__':
    ip_address = get_external_ip_address()

    for domain_name in domains:
        data = create_json_data(domain_name=domain_name, ip_address=ip_address)
        send_request(data)
