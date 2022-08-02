import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_read_main():
    with open("./resources/decoder.v", "r") as f:
        decoder_v = f.read().strip()
    with open("./resources/decoder_testbench.v", "r") as f:
        decoder_testbench_v = f.read().strip()
    top_module = "decoder"

    service_request = {
        "verilog_sources": [decoder_v],
        "testbench": decoder_testbench_v,
        "top_module": top_module,
    }
    response_origin = client.post("/", json=service_request)
    
    if response_origin.status_code == 200:
        print(f"[SUCCEDDED]")
        response = json.loads(response_origin.content)

        print(f'[log] {response["log"]}')
        print(f'[vcd] {response["vcd"]}')
    elif response_origin.status_code == 400:
        print(f"[FAILED]")
        response = json.loads(json.loads(response_origin.content)["detail"])

        print(f'[error] {response["error"]}')
        # print(f'[log] {response["log"]}')
    else:
        print(f"[FAILED]")

        print("[error]" + json.loads(response_origin.content))

    assert response_origin.status_code == 200
