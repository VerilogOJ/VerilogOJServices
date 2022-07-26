import requests  # https://requests.readthedocs.io/en/latest/
import json


def test_single_file():
    code_reference = """
module Zero(
    output out
);
    assign out=0;
endmodule
    """

    code_student = """
module Zero(
    output out
);
    assign out=0;
endmodule
    """

    testbench = """
module testbench();
    wire out;
    Zero myZero(out);

    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars;
    end

    initial begin
        #1;
    end
endmodule
    """

    request_data = {
        "code_reference": code_reference,
        "code_student": code_student,
        "signal_names": ["out"],
        "testbench": testbench,
        "top_module": "Zero",
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
