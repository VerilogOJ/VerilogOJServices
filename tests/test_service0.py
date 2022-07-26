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

    if response_origin.status_code == 200:
        print(f"[SUCCEDDED]")
        response = json.loads(response_origin.content)

        print(f'[service_id] {response["service_id"]}')
    elif response_origin.status_code == 400:
        print(f"[FAILED]")
        response = json.loads(json.loads(response_origin.content)["detail"])

        print(f'[error] {response["error"]}')
        print(f'[log] {response["log"]}')
    else:
        print(f"[FAILED]")

    assert response_origin.status_code == 200
