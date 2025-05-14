from jsonfinder import has_json, jsonfinder


def is_json(text: str) -> bool:
    return has_json(text)


def sanitize_json(text: str) -> str:
    for start, end, obj in jsonfinder(text):
        if obj is not None:
            return obj
    return None
