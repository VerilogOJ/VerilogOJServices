import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_main():
    top_module = "decoder"
    signal_names = ["x", "y"]
    code_reference = """
module decoder(
    input [2:0] x,
    output reg [7:0] y
);
    always @ (*) begin
        case (x)
        3'b000: y=8'b0000_0001;
        3'b001: y=8'b0000_0010;
        3'b010: y=8'b0000_0100;
        3'b011: y=8'b0000_1000;
        3'b100: y=8'b0001_0000;
        3'b101: y=8'b0010_0000;
        3'b110: y=8'b0100_0000;
        3'b111: y=8'b1000_0000;
        endcase
    end
endmodule
    """

    code_student = code_reference

    testbench = """
module testbench();
    reg [2:0] x;
    wire [7:0] y;
    decoder DUT(x, y);
    
    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars;
    end

    integer i;
    initial begin
        for (i = 0; i < 8; i = i + 1) begin
            #1 x = i;
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
