#!/usr/bin/env python3
import subprocess
import time


def main():
    filename = "usage" + str(time.time()) + ".csv"

    f = open(filename, "w")
    f.write("Project, Instances, VCPU, MEM (GB), DISK (GB), Block Storage (GB)\n")

    # get list of projects
    output = subprocess.run(
        ["sudo", "wmcs-openstack", "project", "list", "-f", "value", "-c", "ID"],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    projects = output.split("\n")[:-1]

    for project in projects:
        # gather limit stats
        output = subprocess.run(
            [
                "sudo",
                "wmcs-openstack",
                "limits",
                "show",
                "--project",
                project,
                "--absolute",
                "-f",
                "value",
            ],
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8")
        limits = output.split("\n")

        # parse out resource usage and limits
        for line in limits:
            attr = line.split(" ")[0]
            if attr == "totalInstancesUsed":
                instances = line.split(" ")[1]
            elif attr == "totalCoresUsed":
                cpu = line.split(" ")[1]
            elif attr == "totalRAMUsed":
                ram = line.split(" ")[1]
                # Convert to GB
                ram = str(int(ram) / 1024)

        # parse stats and output as csv
        f.write(f"{project},{instances},{cpu},{ram},")

        # in order to get disk usage, we need to check other calls
        # gather disk used
        output = subprocess.run(
            [
                "sudo",
                "wmcs-openstack",
                "resource",
                "usage",
                "show",
                "--os-placement-api-version",
                "1.9",
                project,
                "-f",
                "value",
            ],
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8")
        resources = output.split("\n")

        for line in resources:
            attr = line.split(" ")[0]
            if attr == "DISK_GB":
                disk_gb = line.split(" ")[1]

        f.write(f"{disk_gb},")

        # gather cinder quota
        ps = subprocess.run(
            ["sudo", "wmcs-openstack", "quota", "show", project, "-f", "table"],
            stdout=subprocess.PIPE,
        )
        pipe = subprocess.run(
            ["grep", "| gigabytes             |"],
            input=ps.stdout,
            stdout=subprocess.PIPE,
        )
        output = subprocess.run(
            ["cut", "-d", "|", "-f", "3"], input=pipe.stdout, stdout=subprocess.PIPE
        ).stdout.decode("utf-8")
        diskquota = output.strip()
        f.write(f"{diskquota}\n")
    f.close()


if __name__ == "__main__":
    main()
