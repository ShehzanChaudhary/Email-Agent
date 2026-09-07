import json


def decode_json(text: str) -> dict:
    """
    Decodes the first JSON object found in a string, tolerating any stray
    text around it. Returns a dict with a critical-error marker if nothing
    valid could be decoded.
    """
    try:
        decoder = json.JSONDecoder()
        pos = 0
        json_objects = []

        while pos < len(text):
            try:
                obj, pos = decoder.raw_decode(text, pos)
                json_objects.append(obj)
            except json.JSONDecodeError:
                pos += 1

        return json_objects[0]
    except Exception:
        return {"system": "Critical error received"}
