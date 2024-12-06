import dataclasses


@dataclasses.dataclass
class DatasetItem:
    system: str
    instruction: str
    input: str
    output: str
    corrected: str | None = None
    has_error: bool | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class Template:

    @classmethod
    def process_string(cls, string: str) -> DatasetItem:
        raise NotImplementedError
