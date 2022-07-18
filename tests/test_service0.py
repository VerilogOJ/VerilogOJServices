import requests  # https://requests.readthedocs.io/en/latest/
import json


def test_get():
    request_data = {}
    url = "http://166.111.223.67:1234"

    print("[request started]")
    response_origin = requests.get(
        url=url,
        headers={"Host": "verilogojservices.service0"},
    )
    print("[request ended]")

    print(f"[status_code] {response_origin.status_code}")
    response = json.loads(response_origin.content)

    if response_origin.status_code == 200:
        print(f"[successed]")

        print(f'[service_id] {response["service_id"]}')
    else:
        print(f"[failed]")

        print(f"[response] {response}")

    assert response_origin.status_code == 200
