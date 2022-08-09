from typing import Optional, Any
from abc import ABC, abstractmethod

import grpc
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract, _compute_digest
from cosmpy.aerial.wallet import Wallet
from cosmpy.crypto.address import Address
from cosmpy.protos.cosmwasm.wasm.v1.query_pb2 import QueryCodeRequest


class InstantiateArgsError(RuntimeError):
    pass


class ContractObserver(ABC):
    @abstractmethod
    def on_code_id_update(self, code_id: int):
        pass

    @abstractmethod
    def on_contract_address_update(self, address: Address):
        pass


class MonkeyContract(LedgerContract):
    def __init__(
        self,
        path: Optional[str],
        client: LedgerClient,
        address: Optional[Address] = None,
        digest: Optional[bytes] = None,
        code_id: Optional[int] = None,
        observer: Optional[ContractObserver] = None,
        init_args: Optional[dict] = None,
    ):
        # pylint: disable=super-init-not-called
        self._path = path
        self._client = client
        self._address = address
        self._observer = observer
        self._init_args = init_args

        # build the digest
        if path is not None:
            self._digest = _compute_digest(self._path)
        elif digest is not None:
            self._digest = digest
        else:
            raise RuntimeError('Unable to determine contract digest')

        # determine the code id
        if code_id is not None:
            self._code_id = self._find_contract_id_by_digest_with_hint(code_id)
        else:
            self._code_id = self._find_contract_id_by_digest(self._digest)

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
    ) -> Address:
        # if no args provided, insert init args from configuration
        if args is None:
            if self._init_args is not None:
                args = self._init_args
            else:
                raise InstantiateArgsError(
                    'Please provide instantiation arguments either in "args" or in the haul.toml configuration for this contract and profile'
                )
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
    ) -> Address:
        code_id = self.store(sender, gas_limit=store_gas_limit)
        address = self.instantiate(
            code_id,
            args,
            sender,
            label=label,
            gas_limit=instantiate_gas_limit,
            admin_address=admin_address,
            funds=funds
        )
        return address

    def _find_contract_id_by_digest_with_hint(self, code_id_hint: int) -> Optional[int]:

        # try and lookup the specified code id
        try:
            req = QueryCodeRequest(code_id=code_id_hint)
            resp = self._client.wasm.Code(req)

            if resp.code_info.data_hash == self.digest:
                return int(resp.code_info.code_id)
        except grpc.RpcError as ex:
            not_found = False

            # pylint: disable=no-member
            if hasattr(ex, 'details') and 'not found' in ex.details():
                not_found = True

            if not not_found:
                raise

        return self._find_contract_id_by_digest(self._digest)

    def __repr__(self):
        return str(self._address)
