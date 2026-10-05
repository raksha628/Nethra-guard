from assurance.hashing import canonical_json, sha256_text


def test_sha256_and_canonical_json():
    assert sha256_text("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'
