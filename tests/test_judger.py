import requests  # https://requests.readthedocs.io/en/latest/
import json


def test_single_file():
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
    """.strip()

    code_student = """
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
    """.strip()

    testbench = """
module testbench();
    reg [2:0] x;
    wire [7:0] y;
    decoder DUT(x, y);
    
    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars(0, x, y);
    end

    integer i;
    initial begin
        for (i = 0; i < 8; i = i + 1) begin
            #1 x = i;
        end
    end
endmodule
    """.strip()

    request_data = {
        "code_reference": code_reference,
        "code_student": code_student,
        "testbench": testbench,
        "top_module": "decoder",
    }
    url = "http://166.111.223.67:1234"

    print("[request started]")
    response_origin = requests.post(
        url=url,
        data=json.dumps(request_data),
        headers={"Host": "verilogojservices.judger"},
    )
    print("[request ended]")

    print(f"[status_code] {response_origin.status_code}")
    response = json.loads(response_origin.content)

    if response_origin.status_code == 200:
        print(f"[successed]")

        print(f'[is_correct] {response["is_correct"]}')
        print(f'[log] {response["log"]}')
        print(f'[wavejson] {response["wavejson"]}')
    else:
        print(f"[failed]")

        print(f'[error] {response["error"]}')
        print(f'[log] {response["log"]}')

    assert response_origin.status_code == 200
