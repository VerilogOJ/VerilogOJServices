# VerilogOJ服务 verilogsources2netlistsvg

## 简介

将多verilog源文件转为netlistsvg

## 开发

```sh
pip3 install -r requirements.txt
npm install -g netlistsvg
sudo apt install yosys # or `brew install yosys` on macOS
uvicorn main:app --reload
```

查看[服务文档](http://localhost:8000/docs)

### 测试

```sh
pip3 install pytest # or conda install pytest
pytest
```

```
============ test session starts =============
platform darwin -- Python 3.9.5, pytest-7.1.2, pluggy-1.0.0
rootdir: /Users/yangxijie/Downloads/INTERNSHIP/VerilogOJ/PROJECT/MAIN/VerilogOJServices/services/verilogsources2netlistsvg
plugins: anyio-3.6.1
collected 1 item                             

test_main.py .                         [100%]

============= 1 passed in 0.73s ==============
```

- 注：项目没有`__init__.py`会使得`pytest`报错。
- 参考：https://fastapi.tiangolo.com/tutorial/testing/?h=test

## 部署

请使用项目根目录下的`docker-compose.yml`部署
