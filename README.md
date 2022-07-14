# 使用nginx-proxy在同一端口多开服务

- [nginx-proxy](https://github.com/nginx-proxy/nginx-proxy)

## 部署

```sh
sudo docker compose up --detach --build
```

或

```sh
sudo docker compose down && git pull && sudo docker compose up --detach --build
```

## 成功部署

```sh
curl -H "Host: service0" 166.111.223.67:1234
curl -H "Host: service1" 166.111.223.67:1234
```

可以看到实现了通过同一个端口1234访问两个FastAPI服务service0和service1
