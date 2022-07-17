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

```sh
$ curl -H "Host: verilogojservices.service0" 166.111.223.67:1234
{"service_id":0}%
curl -H "Host: verilogojservices.verilogsources2netlistsvg" 166.111.223.67:1234
```

即可得到服务返回的结果
