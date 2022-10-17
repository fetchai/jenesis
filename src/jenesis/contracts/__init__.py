import os.path
from dataclasses import dataclass
from typing import Optional

from cosmpy.aerial.contract import _compute_digest


@dataclass
class Contract:
    name: str
    source_path: str
    binary_path: str
    cargo_root: str
    schema: dict

    def __post_init__(self):
        self.instantiate_schema = {}
        self.query_schema = {}
        self.execute_schema = {}

        # check for workspace-style schemas
        if self.name in self.schema:
            contract_schema = self.schema[self.name]
        else:
            contract_schema = self.schema

        for (msg_type, schema) in contract_schema.items():
            if 'instantiate' in msg_type:
                self.instantiate_schema = schema
            elif 'query' in msg_type:
                self.query_schema = schema
            elif 'execute' in msg_type:
                self.execute_schema = schema

    def digest(self) -> Optional[str]:
        if not os.path.isfile(self.binary_path):
            return None

        return _compute_digest(self.binary_path).hex()

    def execute_msgs(self) -> dict:
        return self._extract_msgs(self.execute_schema)

    def query_msgs(self) -> dict:
        return self._extract_msgs(self.query_schema)

    def init_args(self) -> dict:
        return list(self.instantiate_schema.get('properties',{}).keys())

    def _extract_msgs(self, msg_schema: dict) -> dict:
        msgs = {}
        if 'oneOf' in msg_schema:
            schemas = msg_schema['oneOf']
        elif 'anyOf' in msg_schema:
            schemas = msg_schema['anyOf']
        else:
            return msgs
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
