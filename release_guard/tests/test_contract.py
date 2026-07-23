import json
from pathlib import Path

from release_guard.guard import REQUIRED_J_FIELDS

ROOT = Path(__file__).parents[1]

def test_versioned_contracts_exist():
    for name in ("proposal-v1.json", "confirmation-v1.json", "execution-receipt-v1.json", "j-manifest-v1.json"):
        data=json.loads((ROOT/"schemas"/name).read_text(encoding="utf-8"))
        assert data["$schema"].startswith("https://json-schema.org/")

def test_j_contract_matches_runtime_gate():
    schema=json.loads((ROOT/"schemas"/"j-manifest-v1.json").read_text(encoding="utf-8"))
    assert schema["properties"]["rows"]["items"]["required"] == list(REQUIRED_J_FIELDS)
