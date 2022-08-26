Jenesis is a command line tool for rapid contract and service development for the Fetch.ai blockchain ecosystem and other CosmWasm-enabled blockchains.

# Installation

Install jenesis for Python 3.7 or newer via PyPI:

```
pip install jenesis
```

# Getting Started
There are multiple commands integrated into jenesis that allow you to perform a variety of tasks these commands are:

- `new` 
- `init`
- `add`
- `attach`
- `compile`
- `keys` (alpha)
- `deploy` (alpha)
- `run` (alpha)
- `shell` (alpha)

> *NOTE: The alpha commands are in the very early stages of development and may perform unexpectedly*

## Create a new project
Create a project using the ```new``` command
```
jenesis new my_project --profile my_profile
```

This will create a new directory called `my_project`. You can use `--profile` and `--network` optional arguments, when they aren't used, profile and network will be set to `testing` and `fetchai-testnet` respectively. Inside this directory a `jenesis.toml` file will be created containing the following information:

```toml
[project]
name = "my_project"
authors = [ "Alice Tyler <alice@mail.com>",]

[profile.my_profile.network]
name = "fetchai-testnet"
chain_id = "dorado-1"
fee_minimum_gas_price = 5000000000
fee_denomination = "atestfet"
staking_denomination = "atestfet"
url = "grpc+https://grpc-dorado.fetch.ai"
faucet_url = "https://faucet-dorado.fetch.ai"
is_local = false

[profile.my_profile.contracts]
```

The project name is the argument passed to the ```new``` command while the authors field is populated by querying the user's GitHub username and email address. The profile's network will be filled with the relevant configuration variables. The contracts field will remain empty until new contracts are added.

An empty `contracts` folder will also be created inside `my_project` directory that will eventually contain all the information needed to compile and deploy the desired contracts.

The ```init``` command is similar to the ```new``` command, but in this case, you won't need a project name argument since this command is intended to run inside an existing project directory.

```
jenesis init
```

This command will create the same files and folders inside your project directory as the ones described for the ```new``` command.

## Configure a network

By default, jenesis will configure the project to run on the latest stable Fetch.ai testnet. To test on a local node instead, pass the argument `--network fetchai-localnode` when creating a project:
```
jenesis new my_project --network fetchai-localnode
```
or
```
jenesis init --network fetchai-localnode
```

The configuration can be found under the `network` heading in the `jenesis.toml` file and can be changed as desired:

```toml
[profile.testing.network]
name = "fetchai-localnode"
chain_id = "localnode"
fee_minimum_gas_price = 5000000000
fee_denomination = "atestfet"
staking_denomination = "atestfet"
url = "grpc+http://127.0.0.1:9090/"
is_local = true
cli_binary = "fetchd"
validator_key_name = "validator"
mnemonic = "gap bomb bulk border original scare assault pelican resemble found laptop skin gesture height inflict clinic reject giggle hurdle bubble soldier hurt moon hint"
password = "12345678"
moniker = "test-node"
genesis_accounts = [ "fetch1vas6cc9650z0s08230ytqjphgzl5tcq9crqhhu",]
```
In particular, to fund some accounts for testing, replace the `genesis_accounts`
field with the addresses to be funded.

When running any of the commands `deploy`, `run`, `shell`, and `attach`,
jenesis will check for a currently running local node, and if there is none, a new one will be created in a docker container.
