import requests  # https://requests.readthedocs.io/en/latest/
import json

with open("./inverter.v", "r") as f:
    verilog_source = f.read()
request_data = {"verilog_sources": [verilog_source], "top_module": "top"}
url = "http://127.0.0.1:8000"

print("[request started]")
response_origin = requests.put(url=url, data=json.dumps(request_data))
print("[request ended]")
print(f"[status_code] {response_origin.status_code}")
if response_origin.status_code == 200:
    response = json.loads(response_origin.content)
    print(f"[successed] {json.dumps(response, ensure_ascii=False, indent=2)}")
    with open("./netlist.svg", "w") as f:
        f.write(response["netlist_svg"])
else:
    print(f"[failed] {response_origin.content}")
