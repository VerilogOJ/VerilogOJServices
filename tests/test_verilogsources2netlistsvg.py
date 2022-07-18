import requests  # https://requests.readthedocs.io/en/latest/
import json


def test_single_file():
    verilog_source = """
    module top(in, out);
        input in;
        output out;

        assign out = ~in;
    endmodule
    """
    request_data = {"verilog_sources": [verilog_source], "top_module": "top"}
    url = "http://166.111.223.67:1234"

    print("[request started]")
    response_origin = requests.post(
        url=url,
        data=json.dumps(request_data),
        headers={"Host": "verilogojservices.verilogsources2netlistsvg"},
    )
    print("[request ended]")

    print(f"[status_code] {response_origin.status_code}")
    response = json.loads(response_origin.content)

    if response_origin.status_code == 200:
        print(f"[successed]")

        print(f'[log] {response["log"]}')
        print(f'[svg] {response["netlist_svg"]}')
    else:
        print(f"[failed]")

        print(f'[error] {response["error"]}')
        print(f'[log] {response["log"]}')

    assert response_origin.status_code == 200