from typing import Optional

import grpc
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract, _compute_digest
from cosmpy.crypto.address import Address
from cosmpy.protos.cosmwasm.wasm.v1.query_pb2 import QueryCodeRequest


class MonkeyContract(LedgerContract):
    def __init__(self, path: Optional[str], client: LedgerClient, address: Optional[Address] = None,
                 digest: Optional[bytes] = None,
                 code_id: Optional[int] = None):
        # pylint: disable=super-init-not-called
        self._path = path
        self._client = client
        self._address = address

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
