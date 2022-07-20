import argparse
import configparser
import os
import subprocess


def run(args: argparse.Namespace):
    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = user_name + " <" + user_email + ">"

    config = configparser.ConfigParser()
    config.add_section("project")
    config.set("project", "name", args.project)
    config.set("project", "authors", "[" + authors + "]")

    config.add_section("profile.testing")
    config.set("profile.testing", "network", "fetchai-dorado")

    current_path = os.getcwd()

    project = os.path.join(args.project, "contracts/.gitkeep")

    path = os.path.join(current_path, args.project, "haul.toml")  # new

    try:
        os.makedirs(project)
        with open(path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
    except FileExistsError:
        print("Project already exists")


def add_new_command(parser):
    new_cmd = parser.add_parser("new")
    new_cmd.add_argument("-p", "--project", required=True, help="Project name")
    new_cmd.set_defaults(handler=run)
