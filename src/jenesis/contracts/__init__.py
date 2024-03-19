import os.path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from cosmpy.aerial.contract import _compute_digest


SchemaType = Dict[str, Any]


@dataclass
class Contract:
    name: str
    variable_name: str = field(init=False)
    source_path: str
    binary_path: str
    cargo_root: str
    schema: SchemaType
    instantiate_schema: Optional[SchemaType] = field(default=None, init=False)
    query_schema: Optional[SchemaType] = field(default=None, init=False)
    execute_schema: Optional[SchemaType] = field(default=None, init=False)

    def __post_init__(self):
        self.variable_name = self.name.replace("-", "_")
        self.instantiate_schema = {}
        self.query_schema = {}
        self.execute_schema = {}
        self.update_schema()

    def update_schema(self):
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
        return _extract_msgs(self.execute_schema)

    def query_msgs(self) -> dict:
        return _extract_msgs(self.query_schema)

    def init_args(self) -> dict:
        return _get_msg_args(self.instantiate_schema)

    def __repr__(self):
        return self.name


def _extract_msgs(schema: dict) -> dict:
    msgs = {}
    if 'oneOf' in schema:
        schemas = schema['oneOf']
    elif 'anyOf' in schema:
        schemas = schema['anyOf']
    else:
        return msgs
    for msg_schema in schemas:
        msg = msg_schema['required'][0]
        args = _get_msg_args(msg_schema['properties'][msg])
        msgs[msg] = args
    return msgs


def _get_msg_args(msg_schema):
    msg_args = {}
    args = msg_schema.get('properties', {}).keys()
    required = msg_schema.get('required', [])
    for arg in args:
        description = msg_schema['properties'][arg]
        msg_args[arg] = {
            'required': arg in required,
            'type': description.get('type') or description.get('$ref')
        }
    return msg_args
