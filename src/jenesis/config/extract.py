from typing import Any, Optional, List, TypeVar, Generic

from jenesis.config.errors import ConfigurationError

T = TypeVar('T')


def _extract_value(data: Any, path: str) -> Optional[Any]:
    tokens = path.split('.')

    sub_path = tokens[:-1]
    name = tokens[-1]

    for token in sub_path:
        if not isinstance(data, dict):
            return None

        item = data.get(token)
        if item is None:
            return None

        data = item

    if not isinstance(data, dict):
        return None

    return data.get(name)


def _extract_type(data: Any, path: str, obj_type: Generic[T]) -> Optional[T]:
    item = _extract_value(data, path)
    if item is None or (not isinstance(item, obj_type)):
        return None

    return obj_type(item)


def _extract_list_type(data: Any, path: str, obj_type: Generic[T]) -> Optional[List[T]]:
    items = _extract_type(data, path, list)
    return [obj_type(item) for item in items]


def _required(value: Optional[T]) -> T:
    if value is None:
        raise ConfigurationError('unable to extract configuration value')
    return value


def extract_req_int(data: Any, path: str) -> int:
    return _required(_extract_type(data, path, int))


def extract_opt_int(data: Any, path: str) -> Optional[int]:
    return _extract_type(data, path, int)


def extract_req_float(data: Any, path: str) -> float:
    return _required(_extract_type(data, path, float))


def extract_opt_float(data: Any, path: str) -> Optional[float]:
    return _extract_type(data, path, float)


def extract_req_str(data: Any, path: str) -> str:
    return _required(_extract_type(data, path, str))


def extract_opt_str(data: Any, path: str) -> Optional[str]:
    return _extract_type(data, path, str)


def extract_req_dict(data: Any, path: str) -> dict:
    return _required(_extract_type(data, path, dict))


def extract_opt_dict(data: Any, path: str) -> Optional[dict]:
    return _extract_type(data, path, dict)


def extract_req_list(data: Any, path: str) -> List[Any]:
    return _required(_extract_type(data, path, list))


def extract_req_str_list(data: Any, path: str) -> List[str]:
    return _required(_extract_list_type(data, path, str))
