Jenesis is a command line tool for rapid contract and service development.

# Installation

Open your terminal, navigate to your project, and install jenesis via PyPI

```
pip3 install jenesis
```

# Getting Started
There are multiple commands integrated into jenesis that allow you to perform a variety of tasks, these commands are:

- new 
- init
- keys
- add
- compile
- deploy
- shell

## Create a new project
The most straightforward way to create a project is using the ```new``` command
```
jenesis new my_project
```

The command above will create a new directory called my_project. Inside this directory a jenesis.toml file will be created containing the following information:

```
[project]
name = "my_project"
authors = [Alice Tyler <alice.tyler@email.com>]

[profile.testing]
network = "fetchai-testnet"

[profile.testing.contracts]
```

The project name is the argument passed to the ```new``` command while the authors field is populated by querying the user's GitHub username and email address. The profile network is automatically set to **fetchai-testnet**. The contracts field will remain empty until new contracts are added. 

The contracts folder will also be created inside my_project directory that will eventually contain all the information needed to compile and deploy the desired contracts, however, at this stage, this folder will be empty. 

The ```init``` command is very similar to the ```new``` command, but in this case, you won't need a project name argument since this command is intended to run inside an already created project directory to initialize your project.

```
jenesis init
```

This command will create the same files and folders inside your project directory as the ones described for the ```new``` command.



## Keys

Jenesis has a basic interaction with keys, with the ```keys``` command you can either list all the keys locally available or show the address of a specific key. To list all the keys available run the following command:
```
jenesis alpha keys list
```

To look up the address for a specified key you can use the ```show``` command and pass the key name as an argument:
```
jenesis keys show my_key
```
To access other key functionalities such as adding new keys, looking up an address, and recovering keys you can use [fetchd CLI - Managing Keys](https://docs.fetch.ai/ledger_v2/cli-keys/)
