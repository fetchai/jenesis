from cosmpy.crypto.address import Address

from jenesis.config import Config
from jenesis.contracts.monkey import ContractObserver


class DeploymentUpdater(ContractObserver):
    def __init__(self, cfg: Config, project_path: str, profile: str, deployment_name: str):
        self._cfg = cfg
        self._project_path = str(project_path)
        self._profile = str(profile)
        self._deployment_name = str(deployment_name)

    def on_code_id_update(self, code_id: int):
        self._cfg.update_deployment(self._profile, self._deployment_name, None, code_id, None)
        self._cfg.save(self._project_path)

    def on_contract_address_update(self, address: Address):
        self._cfg.update_deployment(self._profile, self._deployment_name, None, None, address)
        self._cfg.save(self._project_path)
