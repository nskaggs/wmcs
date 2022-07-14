#!/usr/bin/env python3

import requests
import argparse


class Config:
    """configuration for this script."""

    def __init__(self, api_token, netbox_url):
        self.api_token = api_token
        if not netbox_url:
            self.netbox_url = "https://netbox.wikimedia.org"
        else:
            self.netbox_url = netbox_url


def generate_netbox_link(config, id):
    return "{}/dcim/devices/{}/".format(config.netbox_url, id)


def print_result_header():
    print(
        "name, purchase date, ticket, status, manufacturer, model, serial, asset tag, rack, position, IPv4, vlan, site, netbox link"
    )


def print_result(config, result):
    netbox_link = generate_netbox_link(config, result["id"])
    if not result["primary_ip4"]:
        result["primary_ip4"] = {}
        result["primary_ip4"]["address"] = "None"
        vlan = "None"
    else:
        vlan = request_query_vlan(config, result)
    if not result["rack"]:
        result["rack"] = {}
        result["rack"]["name"] = "None"
    print(
        "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
            result["name"],
            result["custom_fields"]["purchase_date"],
            result["custom_fields"]["ticket"],
            result["status"]["value"],
            result["device_type"]["manufacturer"]["name"],
            result["device_type"]["model"],
            result["serial"],
            result["asset_tag"],
            result["rack"]["name"],
            result["position"],
            result["primary_ip4"]["address"],
            vlan,
            result["site"]["slug"],
            netbox_link,
        )
    )


def request_query_list(config, query):
    request_url = "{}/api/dcim/devices/?q={}".format(config.netbox_url, query)
    request_headers = {"Authorization": "Token {}".format(config.api_token)}
    return requests.get(url=request_url, headers=request_headers)


def request_query_vlan(config, result):
    ipaddr = result["primary_ip4"]["id"]
    request_url = "{}/api/ipam/ip-addresses/{}".format(config.netbox_url, ipaddr)
    request_headers = {"Authorization": "Token {}".format(config.api_token)}
    ip_result = requests.get(url=request_url, headers=request_headers)

    if not ip_result.json()["assigned_object_id"]:
        return "None"
    interface = ip_result.json()["assigned_object_id"]
    request_url = "{}/api/dcim/interfaces/{}".format(config.netbox_url, interface)
    request_headers = {"Authorization": "Token {}".format(config.api_token)}
    interface_result = requests.get(url=request_url, headers=request_headers)

    if not interface_result.json()["connected_endpoint"]:
        return "None"
    endpoint = interface_result.json()["connected_endpoint"]["id"]
    request_url = "{}/api/dcim/interfaces/{}".format(config.netbox_url, endpoint)
    request_headers = {"Authorization": "Token {}".format(config.api_token)}
    endpoint_result = requests.get(url=request_url, headers=request_headers)

    if endpoint_result.json()["untagged_vlan"]:
        return endpoint_result.json()["untagged_vlan"]["name"]
    else:
        return "None"


def main():
    parser = argparse.ArgumentParser(
        description="Utility to fetch and list WMCS servers from Netbox"
    )
    parser.add_argument("--token", action="store", help="Netbox API token")
    parser.add_argument("--url", action="store", help="Netbox URL")
    args = parser.parse_args()

    config = Config(args.token, args.url)

    print_result_header()
    r = request_query_list(config, "cloud")
    for result in r.json()["results"]:
        print_result(config, result)

    r = request_query_list(config, "lab")
    for result in r.json()["results"]:
        print_result(config, result)

    r = request_query_list(config, "labtest")
    for result in r.json()["results"]:
        print_result(config, result)


if __name__ == "__main__":
    main()
