import argparse
import os

from jenesis.config import Config


def add_workspace_command(parser):

    add_workspace_cmd = parser.add_parser("workspace")
    add_workspace_cmd.add_argument("template", help="The name of the template to use")
    add_workspace_cmd.add_argument(
        "-b", "--branch", help="The name of the branch that should be used"
    )
    add_workspace_cmd.add_argument(
        "-p", "--profile", default="testing", help="The profile to initialize"
    )
    add_workspace_cmd.add_argument(
        "-n", "--network", default="fetchai-testnet", help="Network to use"
    )
    add_workspace_cmd.set_defaults(handler=run_add_workspace)


def run_add_workspace(args: argparse.Namespace):
    template = args.template
    branch = args.branch

    root = os.path.abspath(os.getcwd())

    workspace_root = os.path.join(root, template)

    # check to see if the contract already exists
    if os.path.exists(workspace_root):
        print(f'Workspace "{template}" already exists')
        return False

    Config.add_workspace(workspace_root, template, branch)

    # check if workspace was downloaded correctly
    if not os.path.exists(workspace_root):
        print(f'Couldnt find "{template}" workspace')
        return False

    # create jenesis project
    Config.create_project(workspace_root, args.profile, args.network)

    return True
