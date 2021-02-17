#!/usr/bin/env python3

# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# network-config-check.py - Validate subnets in the networks.yml files

"""
This script expects to read a networks.yml from standard input and then validate
its subnets. For each network it will ensure that:
 - each uai_macvlan subnet's network falls within the network's range
 - each uai_macvlan subnet's DHCP addresses, if defined, fall within the subnnet's range

When validation passes the script exists with a 0 status code. Any non-zero status
code means that there was a failure. The failure will be visible in the script's output.

This script does also check the non-uai_macvlan subnets, but it will no fail when
those do not validate. Instead we'll print a warning message to standard output.

Usage:
    $ cat /etc/ansible/hosts/group_vars/all/networks.yml | python3 network-config-check.py
    OK 10.2.0.0/16 in 10.2.0.0/16
    OK 10.2.50.0 in 10.2.0.0/16
    OK 10.2.99.252 in 10.2.0.0/16
    OK 10.2.100.0/24 in 10.2.0.0/16
    OK 10.2.200.0/23 in 10.2.0.0/16
    OK 10.2.200.10 in 10.2.200.0/23
    OK 10.2.201.244 in 10.2.200.0/23
    $ echo $?
    0
"""

import ipaddress
import sys

import yaml


def is_ip_in_subnet(ip, subnet, warn=False):
    """Check to see if the IP address is in the subet.

    This is wrapper around stdlib functionality that adds output and the
    ability to warn instead of fail.

    The `warn` parameter is a hack that should be removed once we can be sure
    that all subnets are expected to be valid.
    """
    if ipaddress.ip_address(ip) in subnet:
        print(f"OK {ip} in {subnet}")
        return True
    else:
        if warn:
            print(f"WARNING {ip} not in {subnet}", file=sys.stderr)
            return True
        else:
            print(f"FAILED {ip} not in {subnet}", file=sys.stderr)
            return False


def is_subnet_in_network(subnet, network, warn=False):
    """Check to see if the subnet falls within the network.

    This is wrapper around stdlib functionality that adds output and the
    ability to warn instead of fail.

    The `warn` parameter is a hack that should be removed once we can be sure
    that all subnets are expected to be valid.
    """
    if network.overlaps(subnet):
        print(f"OK {subnet} in {network}")
        return True
    else:
        if warn:
            print(f"WARNING {subnet} not in {network}", file=sys.stderr)
            return True
        else:
            print(f"FAILED {subnet} not in {network}", file=sys.stderr)
            return False


def is_valid_network(network):
    """Validate the subnets within a network.

    Each subnet should be within the network range. If DHCP address are
    provided in the subnet those will be checked as well.
    """
    valid = True
    nmn_network = ipaddress.ip_network(network["network"])
    for subnet in network["subnets"]:
        warn = subnet["label"] != "uai_macvlan"
        ip_subnet = ipaddress.ip_network(subnet["network"])
        if not is_subnet_in_network(ip_subnet, nmn_network, warn):
            valid = False

        # Check the DHCP range
        if "dhcp" in subnet:
            if not is_ip_in_subnet(subnet["dhcp"]["start"], ip_subnet, warn):
                valid = False
            if not is_ip_in_subnet(subnet["dhcp"]["end"], ip_subnet, warn):
                valid = False

    return valid


def main(argv):
    try:
        data = yaml.load(sys.stdin)
    except:
        print("FAILED to parse the provided YAML", file=sys.stderr)
        return 3

    try:
        failed = False
        for network in data["networks"]["node_management"]["blocks"]["ipv4"]:
            if not is_valid_network(network):
                failed = True
    except KeyError as err:
        print(
            "FAILED to find the expected data structure. Missing key: {err}",
            file=sys.stdout
        )
        return 4

    if failed:
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
