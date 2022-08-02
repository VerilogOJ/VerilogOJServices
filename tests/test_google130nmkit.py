import requests  # https://requests.readthedocs.io/en/latest/
import json


def test_single_file():
    verilog_source = """
module inverter(
    input in,
    output out
);
    assign out = ~in;
endmodule
    """.strip()
    top_module = "inverter"
    request_data = {"verilog_sources": [verilog_source], "top_module": top_module}
    url = "http://166.111.223.67:1234"

    print("[request started]")
    response_origin = requests.post(
        url=url,
        data=json.dumps(request_data),
        headers={"Host": "verilogojservices.google130nmkit"},
    )
    print("[request ended]")

    print(f"[status_code] {response_origin.status_code}")

    if response_origin.status_code == 200:
        print("[SUCCEDDED]")
        response = json.loads(response_origin.content)

        print(f"[log]\n{response['log']}")

        print(f"[resources_report]\n{response['resources_report']}")
        print(f"[yosys_show_svg]\n{response['yosys_show_svg']}")
        print(f"[netlistsvg_default]\n{response['netlistsvg_default']}")
        print(f"[netlistsvg_google130nm]\n{response['netlistsvg_google130nm']}")
        print(f"[sta_report]\n{response['sta_report']}")
        print(f"[sdf_content]\n{response['sdf_content']}")

        with open("./temp/yosys_show_svg.svg", "w") as f:
            f.write(response["yosys_show_svg"])
        with open("./temp/netlistsvg_default.svg", "w") as f:
            f.write(response["netlistsvg_default"])
        with open("./temp/netlistsvg_google130nm.svg", "w") as f:
            f.write(response["netlistsvg_google130nm"])

    elif response_origin.status_code == 400:
        print("[FAILED]")
        response = json.loads(json.loads(response_origin.content)["detail"])

        print(f"[log] {response['log']}")

        print(f"[error] {response['error']}")
    else:
        print("[FAILED]")
        print(json.loads(response_origin.content))

    assert response_origin.status_code == 200
