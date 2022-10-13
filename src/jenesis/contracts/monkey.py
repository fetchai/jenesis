from typing import Optional, Any
from abc import ABC, abstractmethod

import grpc
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract, _compute_digest
from cosmpy.aerial.tx_helpers import SubmittedTx
from cosmpy.aerial.wallet import Wallet
from cosmpy.crypto.address import Address
from cosmpy.protos.cosmwasm.wasm.v1.query_pb2 import QueryCodeRequest
from jsonschema import ValidationError, validate as validate_schema
from jenesis.contracts import Contract


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

        # determine the code id
        if code_id is not None:
            self._code_id = self._find_contract_id_by_digest_with_hint(code_id)
        else:
            self._code_id = self._find_contract_id_by_digest(self._digest)

        # add methods based on schema
        if contract.schema is not None:
            self._add_queries()
            self._add_executions()

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

    def deploy(
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
        code_id = self.store(sender, gas_limit=store_gas_limit)
        address = self.instantiate(
            code_id,
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

    def _add_queries(self):

        def make_query(query_msg):
            def query(*args, **kwargs):
                query_args = {query_msg: kwargs}
                return self.query(query_args, *args)
            return query

        for query_msg in self._contract.query_msgs():
            if getattr(self, query_msg, None) is None:
                setattr(self, query_msg, make_query(query_msg))

    def _add_executions(self):

        def make_execution(execute_msg):
            def execute(*args, **kwargs):
                execute_args = {execute_msg: kwargs}
                return self.execute(execute_args, *args)
            return execute

        for execute_msg in self._contract.execute_msgs():
            if getattr(self, execute_msg, None) is None:
                setattr(self, execute_msg, make_execution(execute_msg))

    def __repr__(self):
        return str(self._address)
