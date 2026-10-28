from undoom.canonical import canonical_json
from undoom.models import CassetteEntry
from undoom.replay.cassette import Cassette


def test_key_order_and_float_noise_share_a_key() -> None:
    left = canonical_json({"b": 1, "a": 1.0})
    right = canonical_json({"a": 1.0000001, "b": 1})
    assert left == right
    assert canonical_json({"a": 2.0}) != canonical_json({"a": 1.0})


def test_cassette_consumes_duplicate_calls_in_order() -> None:
    cassette = Cassette(
        [
            CassetteEntry(name="lookup_order", arguments={"order_id": "1"}, result={"n": 1}),
            CassetteEntry(name="lookup_order", arguments={"order_id": "1"}, result={"n": 2}),
        ]
    )
    first = cassette.lookup("lookup_order", {"order_id": "1"})
    second = cassette.lookup("lookup_order", {"order_id": "1"})
    third = cassette.lookup("lookup_order", {"order_id": "1"})
    assert first is not None and first.result == {"n": 1}
    assert second is not None and second.result == {"n": 2}
    assert third is None
