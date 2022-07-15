import requests  # https://requests.readthedocs.io/en/latest/
import json


with open("./inverter.v", "r") as f:
    verilog_source = f.read()
request_data = {"verilog_sources": [verilog_source], "top_module": "top"}

url = "http://127.0.0.1:8000"
response = requests.put(url=url, data=json.dumps(request_data))
print(response.status_code)
print(response.content)
result = json.loads(response.content)
print(result)
