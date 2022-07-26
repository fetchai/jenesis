Haul is a command line tool for rapid contract and service development.

# Installation

Open your terminal, navigate to your project, and install via PyPI

```
pip3 install haul
```


# Getting Started
There are multiple commands integrated intohaulthat allow you to perform a variety of tasks, these commands are:
* new
* init
* deploy
* compile
* shell
* keys

## Create a new project
The most straightforward way to create a project is using the ```new``` command
```
haul new my_project
```

The command above will create a new directory called my_project. Inside this directory a haul.toml file will be created containing the following information:

```
[project]
name = "my_project"
authors = [Alice Tyler <alice.tyler@email.com>]

[profile.testing]
network = "fetchai-dorado"
```

The project name is the argument passed to the ```new``` command while the authors field is populated by querying the user's GitHub username and email address. The profile network is automatically set to **dorado testnet**.

A contracts folder will also be created inside my_project directory that will contain all the information needed to deploy or compile the desired contracts. The ```init``` command is very similar to the ```new``` command, but in this case, you won't need a project name argument since this command is intended to run inside an already created project directory to initialize your project.

```
haul init
```

This command will create the same files and folders inside your project directory as the ones described for the ```new``` command.

## Deploy contracts

Once you have successfully created your project and have a .toml file inside the contracts folder describing all the information necessary, you can use the following command to deploy a contract:

```
haul deploy profile_name
```

You must pass the profile_name as an argument to the deploy command who reads the .toml file inside the contracts folder, this will indicate which profile's contract or set of contracts will be deployed in the network

## Keys

Haul has a basic interaction with keys, with the ```keys``` command you can either list all the keys locally available or show the address of a specific key. To list all the keys available run the following command:
```
haul keys list
```

To look up the address for a specified key you can use the ```show``` command and pass the key name as an argument:
```
haul keys show my_key
```
To access other key functionalities such as adding new keys, looking up an address, and recovering keys you can use [fetchd CLI - Managing Keys](https://docs.fetch.ai/ledger_v2/cli-keys/)

## What's next?

Mastered all of the above? Great! But you have only scratched the surface. Check out our [main documentation site](https://docs.fetch.ai/) for more guides and resources.
