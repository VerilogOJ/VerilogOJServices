import requests  # https://requests.readthedocs.io/en/latest/
import json


def test_single_file():
    top_module = "four_bit_counter"
    signal_names = ["clk", "reset", "q"]
    code_reference = """
module four_bit_counter(
    input clk,
    input reset,     
    output [3:0] q
);
    always@(posedge clk) begin
        if(!reset)
            q <= q + 1'b1;
        else
            q <= 4'b0;
    end
endmodule
    """.strip()
    code_student = code_reference

    testbench = """
module testbench();
    reg clk;
    reg reset;
    wire [3:0] q;
    four_bit_counter FBC(clk, reset, q);
    
    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars;
    end

    initial begin
        clk = 0; reset = 1;
        #3 reset = ~reset;
        #7 reset = ~reset;
        #3 reset = ~reset;
    end

    always begin
        #1 clk = ~clk;
    end
endmodule
    """.strip()

    request_data = {
        "code_reference": code_reference,
        "code_student": code_student,
        "signal_names": signal_names,
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

        print("[error]" + json.loads(response_origin.content))

    assert response_origin.status_code == 200


if __name__ == "__main__":
    test_single_file()
