# VerilogOjServices

该服务使用[nginx-proxy](https://github.com/nginx-proxy/nginx-proxy)在同一个端口（如1234）提供多个服务

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

### 命令行测试

#### 默认服务测试

```sh
curl -X GET http://166.111.223.67:1234 -H "Host: verilogojservices.service0"
```

```
{"service_id":0}%
```

#### 实际服务测试

```sh
curl -X POST http://166.111.223.67:1234 -H "Host: verilogojservices.verilogsources2netlistsvg"  -H "Content-Type: application/json" --data '{"verilog_sources": ["module top(in, out);\ninput in;\noutput out;\nassign out = ~in;\nendmodule"],"top_module": "top"}'
```

```
{"netlist_svg":"<svg ... </svg>\n","log":"开始处理2022/07/17, 13:46:53\n ... "}%
```

### pytest测试

> 该测试方法会测试服务器的部署情况。想要独立测试某个服务，请查看各服务的`README.md`。

```sh
pytest tests # 执行`tests/`中的所有测试
pytest tests -s # 执行`tests/`中的所有测试 并进行标准输出
```

### 查看API文档

在Chrome安装[ModHeader插件](https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj)

添加一个Header为`Host` 值为服务名称如`verilogojservices.verilogsources2netlistsvg` （注意将ModHeader当前profile开启）

访问<166.111.223.67:1234/docs>即可看到对应服务的文档（使用完毕可以将ModHead中的profile暂停）

## 部署失败

> 注：有时部署失败是网络问题，可以重新`docker compose up`一下

查看正在运行的容器

```sh
sudo docker ps -a
```

如果服务容器意外退出，使用

```sh
sudo docker logs <container_id>
```

查看部署中的错误。

## Open Source Projects

- [YAVGroup/Verilog-OJ](https://github.com/YAVGroup/Verilog-OJ) [AGPL-3.0 license](https://github.com/YAVGroup/Verilog-OJ/blob/master/LICENSE)
- [Nic30/pyDigitalWaveTools](https://github.com/Nic30/pyDigitalWaveTools) [MIT license](https://github.com/Nic30/pyDigitalWaveTools/blob/master/LICENSE)
