import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_read_main():
    inverter_v = """
TODO
    """.strip()

    netlist_svg = """
TODO
    """.strip()

    service_request = {"TODO": [inverter_v], "TODO": "top"}
    response = client.post("/", json=service_request)
    print(json.loads(response.content))
    print(json.loads(response.content)["TODO"])
    assert response.status_code == 200
