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
curl -H "Host: verilogojservices.service0" 166.111.223.67:1234
```

```
{"service_id":0}%
```

```sh
curl -X POST 166.111.223.67:8000 -H "Host: verilogojservices.verilogsources2netlistsvg"  -H "Content-Type: application/json" --data '{"verilog_sources": ["module top(in, out);\ninput in;\noutput out;\nassign out = ~in;\nendmodule"],"top_module": "top"}' 
```

即可得到服务返回的结果

## 部署失败

查看正在运行的容器

```sh
sudo docker ps -a
```

如果服务容器意外退出，使用

```sh
sudo docker logs <container_id>
```

查看部署中的错误。
