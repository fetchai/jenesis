import argparse

from .shell import load_config


def run(args: argparse.Namespace):
    shell_globals = load_config(args)
    with open(args.script_path, encoding='utf-8') as script:
        exec(script.read(), shell_globals)


def add_run_command(parser):
    run_cmd = parser.add_parser('run')
    run_cmd.add_argument('-p', '--profile', default='testing', help='The profile to use')
    run_cmd.add_argument('script_path', help='The path to the script to run')
    run_cmd.set_defaults(handler=run)
