import argparse
import os

from .shell import load_config


def run(args: argparse.Namespace):
    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return

    shell_globals = load_config(args)
    with open(args.script_path, encoding="utf-8") as script:
        exec(script.read(), shell_globals)


def add_run_command(parser):
    run_cmd = parser.add_parser("run")
    run_cmd.add_argument(
        "-p", "--profile", default="testing", help="The profile to use"
    )
    run_cmd.add_argument("script_path", help="The path to the script to run")
    run_cmd.set_defaults(handler=run)
