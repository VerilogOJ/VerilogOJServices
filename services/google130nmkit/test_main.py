import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_main():
    verilog_source = """
module inverter(in, out);
    input in;
    output out;

    assign out = ~in;
endmodule
    """.strip()

    testbench = """
`timescale 1ns / 1ps

module testbench();
    reg in;
    wire out;
    inverter inverter(in, out);

    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars;
    end

    initial begin
        in = 0; #1
        in = 1; #1 
        in = 0; #1 
        $finish;
    end
endmodule
    """.strip()

    top_module = "inverter"

    service_request = {
        "verilog_sources": [verilog_source],
        "top_module": top_module,
        "testbench": testbench,
    }
    response_origin = client.post("/", json=service_request)
    print(f"[response.status_code] {response_origin.status_code}")

    if response_origin.status_code == 200:
        print("[SUCCEDDED]")
        response = json.loads(response_origin.content)

        print(f"[log]\n{response['log']}")
        print(f"[resources_report]\n{response['resources_report']}")
        print(f"[circuit_svg]\n{response['circuit_svg']}")
        print(f"[sta_report]\n{response['sta_report']}")
        print(f"[simulation_wavejson]\n{response['simulation_wavejson']}")

        with open("./temp/circuit.svg", "w") as f:
            f.write(response["circuit_svg"])

    elif response_origin.status_code == 400:
        print("[FAILED]")
        response = json.loads(json.loads(response_origin.content)["detail"])

        print(f"[log] {response['log']}")
        print(f"[error] {response['error']}")
    else:
        print("[FAILED]")
        print(json.loads(response_origin.content))

    assert response_origin.status_code == 200
