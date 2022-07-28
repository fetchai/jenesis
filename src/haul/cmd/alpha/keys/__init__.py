import argparse

from cosmpy.crypto.address import Address
from cosmpy.crypto.keypairs import PublicKey

from haul.keyring import query_keychain_items, query_keychain_item


def run_list(_args: argparse.Namespace):
    key_names = query_keychain_items()
    if len(key_names) == 0:
        print('No keys available')
        return

    for name in sorted(key_names):
        print(name)


def run_show(args: argparse.Namespace):
    info = query_keychain_item(args.name)
    if info.algorithm != 'secp256k1':
        print(f'Unsupported key algorithm {info.algorithm}')

    public_key = PublicKey(info.public_key)
    address = Address(public_key)

    print(str(address))


def add_keys_command(parser):
    keys_cmd = parser.add_parser('keys')
    subparsers = keys_cmd.add_subparsers()

    list_cmd = subparsers.add_parser('list')
    list_cmd.set_defaults(handler=run_list)

    show_cmd = subparsers.add_parser('show')
    show_cmd.add_argument('name', help='The name of the key to show')
    show_cmd.set_defaults(handler=run_show)
