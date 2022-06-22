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
import logging
import os
import requests
import signal
import sys
from requests import get
from threading import Event

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


# Class required for graceful exit from in docker container.
class GracefulKiller:
    kill_now = False
    event = Event()

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.event.set()
        self.kill_now = True

    def wait(self, seconds: int):
        self.event.wait(seconds)


# Main.
if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    killer = GracefulKiller()
    states = {}
    logging.info('Script was started ...')

    while True:
        if killer.kill_now:
            logging.info('Termination requested...')
            break

        try:
            ip_address = get_external_ip_address()
            logging.info(f'Current IP Address is {ip_address}.')

            for domain_name in domains:
                previous_ip_address = states.get(domain_name)

                if (previous_ip_address is None) or (previous_ip_address != ip_address):
                    data = create_json_data(domain_name=domain_name, ip_address=ip_address)
                    response = send_request(data)
                    decoded_answer = json.loads(response.text)

                    try:
                        if (response.status_code == 200)\
                                and (decoded_answer['status'] == 'success')\
                                and (decoded_answer['answer']['result'] is True):
                            states[domain_name] = ip_address
                            logging.info(f'Record for {domain_name} was updated to {ip_address} successfully')
                        else:
                            logging.error(
                                f'Error was occur while processing domain {domain_name}! Response code: {response.status_code}.'
                                f'Response text: "{response.text}".')
                    except KeyError:
                        logging.error(
                            f'Error was occur while processing domain {domain_name}! Response code: {response.status_code}.'
                            f'Response text: "{response.text}".')
                else:
                    logging.info(f'Record for {domain_name} already updated.')

        except Exception:
            logging.exception('Exception was occur!')
        finally:
            killer.wait(10 * 60)

    logging.info('Script done.')
