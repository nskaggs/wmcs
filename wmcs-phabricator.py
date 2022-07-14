#!/usr/bin/env python3

import argparse
from phabricator import Phabricator
import time


class Config:
    """configuration for this script."""

    def __init__(self, api_token, phab_url, project):
        self.api_token = api_token
        if not phab_url:
            self.phab_url = "https://phabricator.wikimedia.org/api/"
        else:
            self.phab_url = phab_url
        if not project:
            # cloud services kanban
            self.project = "2774"
        else:
            self.project = project

        self.phab = Phabricator(host=self.phab_url, token=self.api_token)


def print_result_header():
    print("id, dateCreated, dateModified, status, priority, author, owner, title")


def print_result(result):
    print(
        "{}, {}, {}, {}, {}, {}, {}, {}".format(
            result["id"],
            time.strftime("%Y-%m-%d", time.gmtime(result["created"])),
            time.strftime("%Y-%m-%d", time.gmtime(result["modified"])),
            # result["created"],
            # result["modified"],
            result["status"],
            result["priority"],
            result["author"],
            result["owner"],
            result["title"],
        )
    )


def open_phab_tasks(config):
    project = config.phab.project.query(ids=[config.project])
    p_pid = list(project["data"].keys())[0]
    # tasks = config.phab.maniphest.query(projectPHIDs=[p_pid],limit=10,status='status-open')
    tasks = config.phab.maniphest.query(projectPHIDs=[p_pid], status="status-open")

    results = []
    for key, task in tasks.items():
        a_pid = task["authorPHID"]
        o_pid = task["ownerPHID"]
        author = config.phab.user.query(phids=[a_pid])[0]["userName"]
        if config.phab.user.query(phids=[o_pid]):
            owner = config.phab.user.query(phids=[o_pid])[0]["userName"]
        else:
            owner = "None"

        result = {}
        result["id"] = task["id"]
        result["created"] = int(task["dateCreated"])
        result["modified"] = int(task["dateModified"])
        result["status"] = task["status"]
        result["priority"] = task["priority"]
        result["author"] = author
        result["owner"] = owner
        result["title"] = task["title"].replace(",", "")
        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Utility to query information from Phabricator"
    )
    parser.add_argument("--token", action="store", help="Phabricator API token")
    parser.add_argument("--url", action="store", help="Phabricator URL")
    parser.add_argument("--project", action="store", help="Project ID")
    args = parser.parse_args()

    config = Config(args.token, args.url, args.project)

    print_result_header()
    results = open_phab_tasks(config)
    for result in results:
        print_result(result)


if __name__ == "__main__":
    main()
