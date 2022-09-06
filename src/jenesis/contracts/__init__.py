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

    def execute_msgs(self) -> dict:
        return self._extract_msgs('execute_msg')

    def query_msgs(self) -> dict:
        return self._extract_msgs('query_msg')

    def init_args(self) -> dict:
        return self.schema.get('instantiate_msg', {}).get('properties',{}).keys()

    def _extract_msgs(self, msg_type: str) -> dict:
        msgs = {}
        if 'oneOf' in self.schema[msg_type]:
            schemas = self.schema[msg_type]['oneOf']
        else:
            schemas = self.schema[msg_type]['anyOf']
        for schema in schemas:
            msg = schema['required'][0]
            if 'required' in schema['properties'][msg]:
                args = schema['properties'][msg]['required']
            else:
                args = []
            msgs[msg] = args
        return msgs

    def __repr__(self):
        return self.name
