import requests  # https://requests.readthedocs.io/en/latest/
import json


def test():
    url = "http://127.0.0.1:8000"
    request_data = {"request": "request"}
    print("[request started]")
    response_origin = requests.post(url=url, data=json.dumps(request_data))
    print("[request ended]")

    print(f"[status_code] {response_origin.status_code}")
    response = json.loads(response_origin.content)
    print(f"[response] {response}")


if __name__ == "__main__":
    test()
