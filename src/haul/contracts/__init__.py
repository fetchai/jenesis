import os.path
from dataclasses import dataclass
from typing import Optional

from cosmpy.aerial.contract import _compute_digest


@dataclass
class Contract:
    name: str
    source_path: str
    binary_path: str
    schema: dict

    def digest(self) -> Optional[str]:
        if not os.path.isfile(self.binary_path):
            return None

        return _compute_digest(self.binary_path).hex()

    def messages(self) -> dict:
        return self.schema.keys()

    def init_args(self) -> dict:
        return self.schema['instantiate_msg']['properties'].keys()

    def __repr__(self):
        return self.name
