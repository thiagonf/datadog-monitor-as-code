import logging
import os
import re
from getopt import GetoptError, getopt
from sys import argv, exit

import yaml
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from dotenv import load_dotenv


def setup_dd_client():
    apiKey, appKey = get_envs()
    configuration = Configuration()
    configuration.api_key["apiKeyAuth"] = apiKey
    configuration.api_key["appKeyAuth"] = appKey
    api_client = ApiClient(configuration)
    api_instance = MonitorsApi(api_client)
    return api_instance


def get_envs():
    load_dotenv()
    apiKey = os.getenv('API_KEY')
    appKey = os.getenv('APP_KEY')

    if apiKey is None or appKey is None:
        print("ERROR: API_KEY or APP_KEY not found!")
        exit(2)

    return apiKey, appKey


def get_monitors(setup_dd_client, monitor_tag):
    api_instance = setup_dd_client()
    return api_instance.list_monitors(monitor_tags=monitor_tag)


def slugify(string):
    string = string.lower().strip()
    string = re.sub(r'[^\w\s-]', '', string)
    string = re.sub(r'[\s_-]+', '-', string)
    string = re.sub(r'^-+|-+$', '', string)
    return string


def validate_name(monitor_name):
    if len(monitor_name) > 62:
        print("============================================================")
        logging.error(f"The monitor's name is longer than 62 character. \n  \
        {monitor_name} \n You must change the name in the field: \n \
        - metadata > name \n \
        - metadata > labels > service")
        print("============================================================")


def check_if_folder_exists():
    if not os.path.isdir("monitors"):
        os.makedirs("monitors")


def format_monitor(monitor_response, monitor_name):
    monitor = {
        "apiVersion": "datadoghq.com/v1alpha1",
        "kind": "DatadogMonitor",
        "metadata": {
            "name": monitor_name,
            "labels": {"service": monitor_name}
        },
        "spec": {}
    }

    monitor["spec"]["name"] = str(
        monitor_response["name"]).replace("\n", "\\n")
    monitor["spec"]["type"] = str(
        monitor_response["type"]).replace("\n", "\\n")
    monitor["spec"]["query"] = str(monitor_response["query"]).replace("\n", "")
    monitor["spec"]["restricted_roles"] = monitor_response["restricted_roles"]
    monitor["spec"]["tags"] = monitor_response["tags"]
    format_message(monitor_response, monitor)
    format_priority(monitor_response, monitor)
    format_options(monitor_response, monitor)
    return monitor


def format_priority(monitor_response, monitor):
    if(monitor_response["priority"] is not None):
        monitor["spec"]["priority"] = monitor_response["priority"]

    return monitor


def format_message(monitor_response, monitor):
    message_monitor = str(
        monitor_response["message"]).replace("\n", "\\n")

    monitor["spec"]["message"] = f'{{{{ print "{message_monitor}" }}}}'

    return monitor


def format_options(monitor_response, monitor):
    try:
        thresholds = monitor_response["options"].get("thresholds").to_dict()
        items = thresholds.items()
        thresholds = {str(key): str(value) for key, value in items}
        monitor["spec"]["options"] = {"thresholds": thresholds}
    except Exception:
        pass
    return monitor


def main(argv):
    check_if_folder_exists()
    service = get_args(argv)
    check_args(service)

    monitors = get_monitors(setup_dd_client, f"service:{service}")

    for monitor_response in monitors:

        monitor_name = slugify(monitor_response["name"])
        validate_name(monitor_name)
        monitor = format_monitor(monitor_response, monitor_name)

        file_name = monitor_name + ".yaml"

        with open("monitors/"+file_name, "w") as f:
            yaml.dump(monitor, f, width=float("inf"))


def print_examples():
    print("To convert all monitors from service_A to code:")
    print("python3 convert_monitor.py -s service_A")


def check_args(service_name):
    error = False
    if service_name is None:
        print("ERROR It's necessary to define a service name!")
        error = True
    if error:
        print_examples()
        exit(2)


def get_args(argv):
    service = None
    try:
        opts, _ = getopt(argv, "hs:",
                         ["service="])
        for opt, arg in opts:
            if opt == "-h":
                print_examples()
                exit(1)
            elif opt in ("-s", "--service"):
                service = arg
    except GetoptError:
        print("ERROR: Invalid argument!")
        print_examples()
        exit(2)

    return service


if __name__ == "__main__":
    main(argv[1:])
