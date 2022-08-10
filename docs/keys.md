> *NOTE: ```keys``` command is still under active development and currently only supported in MacOS*

With the ```keys``` command you can either list all the locally available keys or show the address of a specific key. To list all the keys available run the following command:
```
jenesis alpha keys list
```

To look up the address for a specified key you can use the ```show``` command and pass the key name as an argument:
```
jenesis keys show my_key
```
To access other key functionalities such as adding new keys, looking up an address, and recovering keys you can use [fetchd CLI - Managing Keys](https://docs.fetch.ai/ledger_v2/cli-keys/)
