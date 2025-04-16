import json
import yaml
import pathlib
import dataclasses


def load_file(path: str | pathlib.Path, file_type: str | None = None):
    path = pathlib.Path(path)
    if file_type is None:
        file_type = path.suffix[1:]
    if file_type == 'json':
        return json.loads(path.read_text())
    if file_type == 'jsonl':
        return [json.loads(line) for line in path.read_text().splitlines() if line]
    if file_type == 'yaml':
        return yaml.safe_load(path.read_text())
    if file_type == 'pkl':
        import pickle
        objs = []
        with path.open('rb') as f:
            while True:
                try:
                    objs.append(pickle.load(f))
                except EOFError:
                    break
        return tuple(objs)
    if file_type in {'txt', 'tsv', 'csv'}:
        return [line for line in path.read_text().splitlines() if line]
    raise ValueError(f'Unsupported file type: {file_type}')


def prettify(
        obj,
        indent: int | str | None = 2,
        ensure_ascii: bool = False,
        default=None,
        **kwargs,
) -> str:
    def _default(_obj):
        try:
            return _obj.__dict__
        except AttributeError:
            return str(_obj)

    return json.dumps(
        obj,
        indent=indent,
        ensure_ascii=ensure_ascii,
        default=default or _default,
        **kwargs,
    )


def dataclass_to_cleaned_dict(dataclass_instance: dataclasses.dataclass) -> dict:
    def clean_dict(d: dict) -> dict:
        if not isinstance(d, dict):
            return d
        result = {}
        for key, value in d.items():
            # If value is a dictionary, clean it recursively
            if isinstance(value, dict):
                cleaned = clean_dict(value)
                # Only add it if it's not empty after cleaning
                if cleaned:
                    result[key] = cleaned
            # If value is not None, add it to the result
            elif value is not None:
                result[key] = value
        return result

    dict_ = dataclasses.asdict(dataclass_instance)
    return clean_dict(dict_)
