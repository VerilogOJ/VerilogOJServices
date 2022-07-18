# VerilogOJ服务 verilogsources2netlistsvg

## 简介

将多verilog源文件转为netlistsvg

## 开发

```sh
pip3 install -r requirements.txt
sudo apt install yosys iverilog # on macOS `brew install yosys icarus-verilog`
uvicorn main:app --reload
```

查看[服务文档](http://localhost:8000/docs)

### 测试

```sh
pip3 install pytest # or conda install pytest
pytest
```

## 部署

请使用项目根目录下的`docker-compose.yml`部署
