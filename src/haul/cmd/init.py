import argparse
import configparser
import os
import subprocess


def run(_args: argparse.Namespace):
    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = user_name + " <" + user_email + ">"

    project_path = os.getcwd()
    project_name = os.path.basename(project_path)

    config = configparser.ConfigParser()
    config.add_section("project")
    config.set("project", "name", project_name)
    config.set("project", "authors", "[" + authors + "]")

    config.add_section("profile.testing")
    config.set("profile.testing", "network", "fetchai-dorado")

    project = "contracts/.gitkeep"
    path = os.path.join(project_path, "haul.toml")

    try:
        os.makedirs(project)
        with open(path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
    except FileExistsError:
        print("Project already initialized")


def add_init_command(parser):
    init_cmd = parser.add_parser("init")
    init_cmd.set_defaults(handler=run)
