# VerilogOjServices

- [nginx-proxy Documentation](https://github.com/nginx-proxy/nginx-proxy)

## 服务部署


### 初次部署

按需修改`.env`中的环境变量

```sh
git clone git@git.tsinghua.edu.cn:yang-xj19/verilogojservices.git && cd verilogojservices
sudo docker compose up --detach --build
```

### 更新服务

```sh
sudo docker compose down
git pull && sudo docker compose up --detach --build
```

## 成功部署

服务器上执行（或将`localhost`改为服务器ip后在本地执行）

TODO 更新 如何在浏览器访问到有host的docs/文件夹

```sh
$ curl -H "Host: verilogojservices.service0" localhost:1234
curl -H "Host: verilogojservices.verilogsources2netlistsvg" localhost:1234
```

即可得到服务返回的结果
