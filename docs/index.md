Jenesis is a command line tool for rapid contract and service development.

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
- `compile`
- `keys` (alpha)
- `deploy` (alpha)
- `run` (alpha)
- `shell` (alpha)

> *NOTE: The alpha commands are in the very early stages of development and may perform unexpectedly*

## Create a new project
Create a project using the ```new``` command
```
jenesis new my_project
```

This will create a new directory called `my_project`. Inside this directory a `jenesis.toml` file will be created containing the following information:

```
[project]
name = "my_project"
authors = [Alice Tyler <alice.tyler@email.com>]

[profile.testing]
network = "fetchai-testnet"

[profile.testing.contracts]
```

The project name is the argument passed to the ```new``` command while the authors field is populated by querying the user's GitHub username and email address. The profile network is automatically set to `fetchai-testnet`. The contracts field will remain empty until new contracts are added.

An empty `contracts` folder will also be created inside `my_project` directory that will eventually contain all the information needed to compile and deploy the desired contracts.

The ```init``` command is similar to the ```new``` command, but in this case, you won't need a project name argument since this command is intended to run inside an existing project directory.

```
jenesis init
```

This command will create the same files and folders inside your project directory as the ones described for the ```new``` command.
