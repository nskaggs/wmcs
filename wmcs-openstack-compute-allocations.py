#!/usr/bin/env python3
import subprocess
import time


def main():
    filename = "compute-allocations" + str(time.time()) + ".csv"

    f = open(filename, "w")
    f.write("Host, total_cpu, used_cpu, total_ram, used_ram\n")

    # get list of hosts
    output = subprocess.run(
        ["sudo", "wmcs-openstack", "host", "list", "-f", "value", "-c", "Host Name"],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    hosts = output.split("\n")[:-1]

    for host in hosts:
        if "cloudvirt" in host:
            # gather CPU stats
            output = subprocess.run(
                [
                    "sudo",
                    "wmcs-openstack",
                    "host",
                    "show",
                    host,
                    "-c",
                    "CPU",
                    "-f",
                    "value",
                ],
                stdout=subprocess.PIPE,
            ).stdout.decode("utf-8")
            usage = output.split("\n")
            # first is total, second is used_now
            total_cpu = usage[0]
            used_cpu = usage[1]

            # gather MEM stats
            output = subprocess.run(
                [
                    "sudo",
                    "wmcs-openstack",
                    "host",
                    "show",
                    host,
                    "-c",
                    "Memory MB",
                    "-f",
                    "value",
                ],
                stdout=subprocess.PIPE,
            ).stdout.decode("utf-8")
            usage = output.split("\n")
            # first is total, second is used_now
            # convert memory to GB
            total_ram = int(usage[0]) / 1024
            used_ram = int(usage[1]) / 1024

            # parse stats and output as csv
            f.write(f"{host},{total_cpu},{used_cpu},{total_ram},{used_ram}\n")

    f.close()


if __name__ == "__main__":
    main()
