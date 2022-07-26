import argparse
import os
from tempfile import mkdtemp
import shutil
import subprocess


def run_add_contract(args: argparse.Namespace):
    template = args.template
    name = args.name

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, 'contracts', name)

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_root, 'haul.toml')):
        print('Please run command from project root')
        return False

    # check to see if the contract already exists
    if os.path.exists(contract_root):
        print(f'Contract "{name}" already exists')
        return False

    # create the temporary clone folder
    temp_clone_path = mkdtemp(prefix='haul-', suffix='-tmpl')

    # clone the templates folder out in the temporary file
    cmd = ['git', 'clone', '--single-branch', 'git@github.com:fetchai/haul-templates.git', '.']
    with open(os.devnull, 'w') as null_file:
        subprocess.check_call(cmd, stdout=null_file, stderr=subprocess.STDOUT, cwd=temp_clone_path)

    # find the target contract
    contract_template_path = os.path.join(temp_clone_path, 'contracts', template)
    if not os.path.isdir(contract_template_path):
        print(f'Unknown template {template}')
        return False

    # process all the files as part of the template
    for root, _, files in os.walk(contract_template_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, contract_template_path)

            output_filepath = os.path.join(contract_root, rel_path)
            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
            with open(file_path, 'r') as input_file:
                with open(output_filepath, 'w') as output_file:
                    contents = input_file.read()

                    # replace the templating parameters here
                    contents = contents.replace('<<NAME>>', name)

                    output_file.write(contents)

            print(f'- {rel_path} -> {output_filepath}')

    # clean up the temporary folder
    shutil.rmtree(temp_clone_path)

