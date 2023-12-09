from bson import ObjectId
from functools import wraps
from typing import Callable, Union

from .pyobjectid import PyObjectId

import re


def parse_data(func: Callable):
    """
    This parses the input and output of a call to the db, adding and removing object ids, allowing fastapi to easily parse the response
    """
    def wrapper(*args, **kwargs):
        args = tuple([_process_input(i) for i in list(args)])
        result = func(*args, **kwargs)

        process_result = _process_result(result)
        return process_result

    return wrapper


def is_object_id(string):
    pattern = r'^[0-9a-fA-F]{24}$'
    return bool(re.match(pattern, string))


def _process_input(data: Union[dict, list]):
    processed_data = {}
    if isinstance(data, list):
        processed_data = list(map(_process_input, iter(data)))

    elif isinstance(data, str) and is_object_id(data):
        processed_data = PyObjectId(data)

    elif isinstance(data, dict):
        for key, value in data.items():
            processed_data[key] = _process_input(value)

    return processed_data if processed_data else data


def _process_result(data: Union[dict, list]):
    """
    Recursively process a dictionary and return a new dictionary with all ObjectIds converted to strings.

    Args:
        data(dict || list): The dictionary to process.

    Returns:
        dict: The processed dictionary.
    """
    processed_data = {}
    if isinstance(data, list):
        processed_data = list(map(_process_result, iter(data)))

    elif isinstance(data, dict):
        processed_data = data.copy()
        for key, value in data.items():
            if isinstance(value, ObjectId):
                processed_data[key] = str(value)

            elif isinstance(value, dict):
                processed_data[key] = _process_result(value)

            elif isinstance(value, list):
                processed_data[key] = list(map(lambda x: _process_result(x), iter(value)))

    return processed_data if processed_data else data