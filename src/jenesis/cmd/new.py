import argparse

from jenesis.config import Config


def run(args: argparse.Namespace):
    Config.create_project(args.project, args.profile)


def add_new_command(parser):
    new_cmd = parser.add_parser("new")
    new_cmd.add_argument("project", help="Project name")
    new_cmd.add_argument(
        "-p", "--profile", default="testing", help="The profile to create"
    )
    new_cmd.set_defaults(handler=run)
