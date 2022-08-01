import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_read_main():
    with open("./resources/decoder.v", "r") as f:
        inverter_v = f.read().strip()

    service_request = {"verilog_sources": [inverter_v], "top_module": "decoder"}
    response_origin = client.post("/", json=service_request)

    response = json.loads(response_origin.content)
    assert response_origin.status_code == 200
    with open("./temp/netlist.svg", "w") as f:
        f.write(response["netlist_svg"])
