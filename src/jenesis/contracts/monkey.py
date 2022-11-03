from typing import Dict, Optional, Any, Callable, List
from abc import ABC, abstractmethod
from keyword import iskeyword

import grpc
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract, _compute_digest
from cosmpy.aerial.tx_helpers import SubmittedTx
from cosmpy.aerial.wallet import Wallet
from cosmpy.crypto.address import Address
from cosmpy.protos.cosmwasm.wasm.v1.query_pb2 import QueryCodeRequest
from jsonschema import ValidationError, validate as validate_schema
from makefun import create_function
from jenesis.contracts import Contract


PYTHON_KEYWORD_PREFIX = '_'


class InstantiateArgsError(RuntimeError):
    pass


class ContractObserver(ABC):
    @abstractmethod
    def on_code_id_update(self, code_id: int):
        pass

    @abstractmethod
    def on_contract_address_update(self, address: Address):
        pass


def validate(args: Any, schema: dict):
    try:
        validate_schema(args, schema)
    except ValidationError as ex:
        print("Contract message failed validation. To send to ledger anyway, retry with 'do_validate=False'")
        raise ex


class MonkeyContract(LedgerContract):
    def __init__(
        self,
        contract: Contract,
        client: LedgerClient,
        address: Optional[Address] = None,
        digest: Optional[bytes] = None,
        code_id: Optional[int] = None,
        observer: Optional[ContractObserver] = None,
        init_args: Optional[dict] = None,
    ):
        # pylint: disable=super-init-not-called
        self._contract = contract
        self._path = contract.binary_path
        self._client = client
        self._address = address
        self._observer = observer
        self._init_args = init_args

        # build the digest
        if contract.binary_path is not None:
            self._digest = _compute_digest(contract.binary_path)
        elif digest is not None:
            self._digest = digest
        else:
            raise RuntimeError('Unable to determine contract digest')

        # look up the code id if this is the first time
        if code_id is None:
            self._code_id = self._find_contract_id_by_digest(self._digest)
        elif code_id <= 0:
            self._code_id = 0
        else:
            self._code_id = self._find_contract_id_by_digest_with_hint(code_id)

        # if code id is not found, store this as code_id = 0 so we don't keep looking for it
        if self._code_id is None:
            self._code_id = 0

        # trigger the observer if necessary
        if self._observer is not None and self._code_id is not None:
            self._observer.on_code_id_update(self._code_id)

    def store(
            self,
            sender: Wallet,
            gas_limit: Optional[int] = None,
            memo: Optional[str] = None,
    ) -> int:
        code_id = super().store(sender, gas_limit=gas_limit, memo=memo)

        # trigger the observer if necessary
        if self._observer is not None:
            self._observer.on_code_id_update(code_id)

        return code_id

    def instantiate(
            self,
            code_id: int,
            args: Any,
            sender: Wallet,
            label: Optional[str] = None,
            gas_limit: Optional[int] = None,
            admin_address: Optional[Address] = None,
            funds: Optional[str] = None,
            do_validate: Optional[bool] = True,
    ) -> Address:
        # if no args provided, insert init args from configuration
        if args is None:
            if self._init_args is not None:
                args = self._init_args
            else:
                raise InstantiateArgsError(
                    'Please provide instantiation arguments either in "args" or in the jenesis.toml configuration for this contract and profile'
                )
        if do_validate and self._contract.instantiate_schema:
            validate(args, self._contract.instantiate_schema)
        address = super().instantiate(code_id, args, sender, label=label, gas_limit=gas_limit,
                                      admin_address=admin_address, funds=funds)

        if self._observer is not None:
            self._observer.on_contract_address_update(address)

        return address

    def _deploy(
        self,
        args: Any,
        sender: Wallet,
        label: Optional[str] = None,
        store_gas_limit: Optional[int] = None,
        instantiate_gas_limit: Optional[int] = None,
        admin_address: Optional[Address] = None,
        funds: Optional[str] = None,
        do_validate: Optional[bool] = True,
    ) -> Address:

        # in the case where the contract is already deployed
        if self._address is not None and self._code_id is not None:
            return self._address

        assert self._address is None

        if self._code_id is None or self._code_id <= 0:
            self.store(sender, gas_limit=store_gas_limit)

        assert self._code_id

        address = self.instantiate(
            self._code_id,
            args,
            sender,
            label=label,
            gas_limit=instantiate_gas_limit,
            admin_address=admin_address,
            funds=funds,
            do_validate=do_validate,
        )
        return address

    def execute(
        self,
        args: Any,
        sender: Wallet,
        gas_limit: Optional[int] = None,
        funds: Optional[str] = None,
        do_validate: Optional[bool] = True,
    ) -> SubmittedTx:
        if do_validate and self._contract.execute_schema:
            validate(args, self._contract.execute_schema)
        return super().execute(args, sender, gas_limit, funds)

    def query(self, args: Any, do_validate: Optional[bool] = True) -> Any:
        if do_validate and self._contract.query_schema:
            validate(args, self._contract.query_schema)
        return super().query(args)

    def make_queries(self) -> Dict[str, Callable]:

        def make_query(msg: str, msg_args: List[str]):
            def query(self, *args, **kwargs):
                query_arg = {msg: {python_keyword_unwrapper(key): value for (key, value) in kwargs.items()}}
                return self.query(query_arg, *args)

            sig = self._make_function_signature(msg, msg_args, [])
            func = create_function(sig, query)
            return func

        queries = {}
        for (msg, msg_args) in self._contract.query_msgs().items():
            queries[msg] = make_query(msg, msg_args)

        return queries

    def make_executions(self) -> Dict[str, Callable]:

        def make_execution(msg: str, msg_args: List[str]):
            def execute(self, sender, gas_limit=None, funds=None, **kwargs):
                execute_arg = {msg: {python_keyword_unwrapper(key): value for (key, value) in kwargs.items()}}
                return self.execute(execute_arg, sender, gas_limit, funds)

            ledger_args = ['sender', 'label', 'store_gas_limit', 'gas_limit', 'funds']
            sig = self._make_function_signature(
                msg, msg_args, ledger_args
            )
            func = create_function(sig, execute)
            return func

        executions = {}
        for (msg, msg_args) in self._contract.execute_msgs().items():
            executions[msg] = make_execution(msg, msg_args)

        return executions

    def make_deploy(self) -> Dict[str, Callable]:

        def make_deploy(msg: str, msg_args: List[str]):
            def deploy(
                self,
                sender,
                label=None,
                store_gas_limit=None,
                instantiate_gas_limit=None,
                admin_address=None,
                funds=None,
                **kwargs
            ):
                init_arg = {python_keyword_unwrapper(key): value for (key, value) in kwargs.items()}
                return self._deploy(
                    init_arg,
                    sender,
                    label,
                    store_gas_limit,
                    instantiate_gas_limit,
                    admin_address,
                    funds,
                )

            ledger_args = [
                'sender', 'label', 'store_gas_limit', 'instantiate_gas_limit', 'admin_address', 'funds'
            ]
            sig = self._make_function_signature(msg, msg_args, ledger_args)
            func = create_function(sig, deploy)
            return func

        deploy = {'deploy': make_deploy('deploy', self._contract.init_args())}

        return deploy

    @staticmethod
    def _make_function_signature(
        name: str,
        msg_args: Dict[str, Any],
        ledger_args: List[str],
    ):
        sig_args = ['self']
        for (arg, description) in msg_args.items():
            if description.get('required'):
                sig_args.append(python_keyword_wrapper(arg))
        for (arg, description) in msg_args.items():
            if not description.get('required'):
                sig_args.append(f"{python_keyword_wrapper(arg)}=None")
        sig_args += [f'{arg}=None' for arg in ledger_args]
        return f'{name}({",".join(sig_args)})'

    def _find_contract_id_by_digest_with_hint(self, code_id_hint: int) -> Optional[int]:

        # try and lookup the specified code id
        try:
            req = QueryCodeRequest(code_id=code_id_hint)
            resp = self._client.wasm.Code(req)

            if resp.code_info.data_hash == self.digest:
                return int(resp.code_info.code_id)
        except (grpc.RpcError, RuntimeError) as ex:
            not_found = False

            # pylint: disable=no-member
            if hasattr(ex, 'details') and 'not found' in ex.details() or 'not found' in str(ex):
                not_found = True

            if not not_found:
                raise

        return self._find_contract_id_by_digest(self._digest)

    def __repr__(self):
        return str(self._address)


def make_contract(
    contract: Contract,
    client: LedgerClient,
    address: Optional[Address] = None,
    digest: Optional[bytes] = None,
    code_id: Optional[int] = None,
    observer: Optional[ContractObserver] = None,
    init_args: Optional[dict] = None,
) -> Any:
    """
    Makes the contract objects for interaction from the shell and scripts.
    The purpose of this factory function is to attach the contract executions
    and queries so that the shell's autocomplete function will work.

    :param contract: The static contract data
    :param client: The client for interacting with the ledger
    :param address: The contract address
    :param digest: The contract digest
    :param code_id: The contract code_id
    :param observer: The contract observer
    :param init_args: The instantiation arguments
    :return: The contract object with queries and executions attached
    """

    monkey_contract = MonkeyContract(
        contract, client, address, digest, code_id, observer, init_args
    )

    # add methods based on schema
    contract_functions = {}
    if contract.schema is not None:
        contract_functions.update(monkey_contract.make_queries())
        contract_functions.update(monkey_contract.make_executions())
        contract_functions.update(monkey_contract.make_deploy())

    JenesisContract = type('JenesisContract', (MonkeyContract,), contract_functions)

    return JenesisContract(
        contract, client, address, digest, code_id, observer, init_args
    )


def python_keyword_wrapper(arg: str) -> str:
    return f'{PYTHON_KEYWORD_PREFIX}{arg}' if iskeyword(arg) else arg


def python_keyword_unwrapper(arg: str) -> str:
    if PYTHON_KEYWORD_PREFIX in arg:
        if iskeyword(arg[len(PYTHON_KEYWORD_PREFIX):]):
            return arg[len(PYTHON_KEYWORD_PREFIX):]
    return arg
