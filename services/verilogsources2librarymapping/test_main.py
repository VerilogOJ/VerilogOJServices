import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_read_main():
    verilog_source = """
module top(in, out);
    input in;
    output out;

    assign out = ~in;
endmodule
    """.strip()

    top_module = "top"
    library_type = "google_130nm"

    service_request = {
        "verilog_sources": [verilog_source],
        "top_module": top_module,
        "library_type": library_type,
    }
    response_origin = client.post("/", json=service_request)
    print(f"[response.status_code] {response_origin.status_code}")

    if response_origin.status_code == 200:
        print("[SUCCEDDED]")
        response = json.loads(response_origin.content)

        print(f"[log] {response['log']}")
        print(f"[circuit_svg] {response['circuit_svg']}")
        print(f"[resources_report] {response['resources_report']}")
    elif response_origin.status_code == 400:
        print("[FAILED]")
        response = json.loads(json.loads(response_origin.content)["detail"])

        print(f"[log] {response['log']}")
        print(f"[error] {response['error']}")
    else:
        print("[FAILED]")
        print(json.loads(response_origin.content))

    assert response_origin.status_code == 200
