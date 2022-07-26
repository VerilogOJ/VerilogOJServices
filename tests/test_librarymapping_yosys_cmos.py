import requests  # https://requests.readthedocs.io/en/latest/
import json

def test_read_main():
    verilog_source = """
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

    top_module = "decoder"
    library_type = "yosys_cmos"

    request_data = {
        "verilog_sources": [verilog_source],
        "top_module": top_module,
        "library_type": library_type,
    }
    url = "http://166.111.223.67:1234"

    print("[request started]")
    response_origin = requests.post(
        url=url,
        data=json.dumps(request_data),
        headers={"Host": "verilogojservices.verilogsources2librarymapping"},
    )
    print("[request ended]")

    if response_origin.status_code == 200:
        print("[SUCCEDDED]")
        response = json.loads(response_origin.content)

        print(f"[log] {response['log']}")
        print(f"[circuit_svg] {response['circuit_svg']}")
        print(f"[resources_report] {response['resources_report']}")

        with open("./temp/circuit_yosys_cmos.svg", "w") as f:
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
