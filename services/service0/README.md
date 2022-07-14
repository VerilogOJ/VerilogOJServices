# FastAPI尝试

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/)

## development

```sh
pip3 install -r requirements.txt

uvicorn main:app --reload
```

<http://localhost:8000> & <http://localhost:8000/docs>

## production

```sh
sudo docker build -t service0 .
sudo docker run --detach --name service0test --publish 1234:80 service0
```

<http://server_ip:1234> & <http://server_ip:1234/docs>
