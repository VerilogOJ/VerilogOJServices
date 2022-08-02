import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_main():
    top_module = "population_count"
    signal_names = ["in", "out"]
    code_reference = """
module population_count(
    input [2:0] in,
    output [1:0] out
);
    assign out = in[2] + in[1] + in[0];
endmodule
    """

    code_student = code_reference

    testbench = """
module testbench();
    reg [2:0] in;
    wire [1:0] out;
    population_count PopCount(in, out);
    
    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars;
    end

    integer i;
    initial begin
        for (i = 0; i < 8; i = i + 1) begin
            #1 in = i;
        end
    end
endmodule
    """

    request_data = {
        "top_module": top_module,
        "signal_names": signal_names,
        "code_reference": code_reference,
        "code_student": code_student,
        "testbench": testbench,
    }

    response_origin = client.post("/", json=request_data)
    print(f"[status_code] {response_origin.status_code}")

    if response_origin.status_code == 200:
        print(f"[SUCCEDDED]")
        response = json.loads(response_origin.content)

        print(f'[is_correct] {response["is_correct"]}')
        print(f'[log] {response["log"]}')
        print(f'[wavejson] {response["wavejson"]}')
    elif response_origin.status_code == 400:
        print(f"[FAILED]")
        response = json.loads(json.loads(response_origin.content)["detail"])

        print(f'[error] {response["error"]}')
        print(f'[log] {response["log"]}')
    else:
        print(f"[FAILED]")

        print("[error]" + str(response_origin.content))

    assert response_origin.status_code == 200
