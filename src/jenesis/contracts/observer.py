from cosmpy.crypto.address import Address

from jenesis.config import Config
from jenesis.contracts.monkey import ContractObserver


class DeploymentUpdater(ContractObserver):
    def __init__(self, cfg: Config, project_path: str, profile: str, contract: str):
        self._cfg = cfg
        self._project_path = str(project_path)
        self._profile = str(profile)
        self._contract = str(contract)

    def on_code_id_update(self, code_id: int):
        self._cfg.update_deployment(self._profile, self._contract, None, code_id, None)
        self._cfg.save(self._project_path)

    def on_contract_address_update(self, address: Address):
        self._cfg.update_deployment(self._profile, self._contract, None, None, address)
        self._cfg.save(self._project_path)
