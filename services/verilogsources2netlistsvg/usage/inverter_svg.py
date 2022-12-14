import requests  # https://requests.readthedocs.io/en/latest/
import json

with open("./inverter.v", "r") as f:
    verilog_source = f.read()
request_data = {"verilog_sources": [verilog_source], "top_module": "top"}
url = "http://127.0.0.1:8000"

print("[request started]")
response_origin = requests.post(url=url, data=json.dumps(request_data))
print("[request ended]")
print(f"[status_code] {response_origin.status_code}")
response = json.loads(response_origin.content)

if response_origin.status_code == 200:
    # print(f"[successed] {json.dumps(response, ensure_ascii=False, indent=2)}")
    print(f"[successed]")
    print(f'[log] {response["log"]}')
    with open("./netlist.svg", "w") as f:
        f.write(response["netlist_svg"])
else:
    print(f"[failed]")
    print(f'[error] {response["error"]}')
    print(f'[log] {response["log"]}')
