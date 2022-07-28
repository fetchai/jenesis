Haul is a command line tool for rapid contract and service development.

# Installation

Open your terminal, navigate to your project, and install haul via PyPI

```
pip3 install haul
```


# Getting Started
There are multiple commands integrated into haul that allow you to perform a variety of tasks, these commands are:

- new 
- init
- add
- compile
- deploy
- shell
- keys

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

## Add contract templates
Once you have successfully created your project, you can add contract templates. You first need to navigate to your project's directory and run the following command:

```
haul add contract <TEMPLATE> <NAME>
```

An example of how to add the template **starter** with the name my-first-contract is given below:

```
haul add contract starter my-first-contract
```

This ```add contract``` command will add a contract template to your haul project inside contracts/my-first-contract/ folder. 

## Compile contracts
Once the template has been added to your project, you can compile the contract by running the following command inside your
project directory:

```
haul compile
```
This will compile all packages in your project's contracts directory and output the wasm code under the artifacts directory.

Note that in order to run haul compile you need to have docker running. A common mistake is to run docker as a root user, you can manage docker as a non-root user by running the following commands:
```
sudo groupadd docker
sudo usermod -aG docker $USER
```

You will have to log out and log back in to activate the changes. If you are using Linux, you can run the following command to activate the changes:
```
newgrp docker
```
Finally, verify that you can run docker without sudo
```
docker run hello-world
```
Now you can re-try ```haul compile```


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
