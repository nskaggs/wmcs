import subprocess


def main():
    startdate = "2021-12-01"
    enddate = "2022-01-01"

    fu = open("usage.csv", "w")
    fu.write("Project,CPU Hours,Disk GB-Hours,RAM MB-Hours,Servers\n")

    fl = open("limits.csv", "w")
    fl.write("Project, maxInstances, Instances, maxCPU, CPU, maxRAM, RAM (MB))\n")

    fq = open("quota.csv", "w")
    fq.write("Project, gigabytes\n")

    fr = open("resource.csv", "w")
    fr.write("Project, VCPU, MEMORY_MD, DISK_G\n")

    # get list of projects
    output = subprocess.run(
        ["sudo", "wmcs-openstack", "project", "list", "-f", "value", "-c", "ID"],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    projects = output.split("\n")[:-1]

    for project in projects:
        # gather usage stats
        output = subprocess.run(
            [
                "sudo",
                "wmcs-openstack",
                "usage",
                "show",
                "--project",
                project,
                "--print-empty",
                "-f",
                "value",
                "--start",
                startdate,
                "--end",
                enddate,
            ],
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8")
        usage = output.split("\n")[:-1]
        # parse stats and output as csv
        fu.write(f"{project},{usage[0]},{usage[1]},{usage[2]},{usage[3]}\n")

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
            if attr == "maxTotalInstances":
                maxinstances = line.split(" ")[1]
            elif attr == "totalInstancesUsed":
                instances = line.split(" ")[1]
            elif attr == "maxTotalCores":
                maxcpu = line.split(" ")[1]
            elif attr == "totalCoresUsed":
                cpu = line.split(" ")[1]
            elif attr == "maxTotalRAMSize":
                maxram = line.split(" ")[1]
            elif attr == "totalRAMUsed":
                ram = line.split(" ")[1]

        # parse stats and output as csv
        fl.write(
            f"{project},{maxinstances},{instances},{maxcpu},{cpu},{maxram},{ram},\n"
        )

        # in order to get disk usage, we need to check other calls
        # gather maxdisk (cinder)
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
        fq.write(f"{project},{diskquota},\n")

        # gather disk used (cinder)
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
            if attr == "VCPU":
                vcpu = line.split(" ")[1]
            elif attr == "MEMORY_MB":
                memory_mb = line.split(" ")[1]
            elif attr == "DISK_GB":
                disk_gb = line.split(" ")[1]

        fr.write(f"{project},{vcpu},{memory_mb},{disk_gb}\n")

    fu.close()
    fl.close()
    fq.close()
    fr.close()

    fh = open("hosts.csv", "w")
    fh.write("Host,Summary,CPU,Memory MB,Disk GB\n")

    fp = open("projects.csv", "w")
    fp.write("Project,Host,CPU,Memory MB,Disk GB\n")

    # get list of hosts and show
    output = subprocess.run(
        [
            "sudo",
            "wmcs-openstack",
            "host",
            "list",
            "-f",
            "value",
            "-c",
            "Host Name",
            "--zone",
            "nova",
        ],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    hosts = output.split("\n")[:-1]

    # seperate host totals from project stats
    for host in hosts:
        output = subprocess.run(
            ["sudo", "wmcs-openstack", "host", "show", host, "-f", "value"],
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8")
        stats = output.split("\n")[:-1]
        host_lines = stats[0:3]
        project_lines = stats[3:]

        # write out host info
        for line in host_lines:
            entry = line.split(" ")
            fh.write(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]},{entry[4]}\n")

        # write out project info
        for line in project_lines:
            entry = line.split(" ")
            fp.write(f"{entry[1]},{entry[0]},{entry[2]},{entry[3]},{entry[4]}\n")
    fh.close()
    fp.close()


main()
