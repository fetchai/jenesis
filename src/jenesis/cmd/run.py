import argparse
import os
import sys

from jenesis.config import Config, Profile
from jenesis.network import network_context

from .shell import get_profile, load_shell_globals


PROJECT_PATH = os.getcwd()


def run(args: argparse.Namespace):
    cfg = Config.load(PROJECT_PATH)
    profile: Profile = get_profile(cfg, args)

    with network_context(profile.network, cfg.project_name, profile.name):
        shell_globals = load_shell_globals(cfg, profile)

        # Make the script args available inside the script
        sys.argv = [args.script_path] + args.args
        shell_globals['sys'] = sys

        with open(args.script_path, encoding="utf-8") as file:
            code = compile(
                file.read(),
                os.path.basename(args.script_path),
                'exec',
            )
            exec(code, shell_globals)


def add_run_command(parser):
    run_cmd = parser.add_parser("run")
    run_cmd.add_argument(
        "-p", "--profile", default=None, help="The profile to use"
    )
    run_cmd.add_argument("script_path", help="The path to the script to run")
    run_cmd.add_argument(
        "args", nargs= "*", help="The args to pass to the script"
    )
    run_cmd.set_defaults(handler=run)
