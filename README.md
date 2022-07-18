# VerilogOjServices

该服务使用同一个端口（如1234）提供多个服务

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

### 默认服务测试

```sh
curl -H "Host: verilogojservices.service0" 166.111.223.67:1234
```

```
{"service_id":0}%
```

### 实际服务测试

```sh
curl -X POST 166.111.223.67:1234 -H "Host: verilogojservices.verilogsources2netlistsvg"  -H "Content-Type: application/json" --data '{"verilog_sources": ["module top(in, out);\ninput in;\noutput out;\nassign out = ~in;\nendmodule"],"top_module": "top"}' 
```

```
{"netlist_svg":"<svg ... </svg>\n","log":"开始处理2022/07/17, 13:46:53\n ... "}%
```

即可得到服务返回的结果

### 查看API文档

在Chrome安装[ModHeader插件](https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj)

添加一个Header为`Host` 值为服务名称如`verilogojservices.verilogsources2netlistsvg` （注意将ModHeader当前profile开启）

访问<166.111.223.67:1234/docs>即可看到对应服务的文档（使用完毕可以将ModHead中的profile暂停）

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
