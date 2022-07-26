# VerilogOJ服务 verilogsources2librarymapping

## 简介

将多verilog源文件转为元件库映射之后的电路图，并生成资源占用报告。

## 开发

```sh
pip3 install -r requirements.txt
sudo apt install yosys # or `brew install yosys` on macOS

uvicorn main:app --reload
```

查看[服务文档](http://localhost:8000/docs)

### 测试

```sh
pip3 install pytest # or conda install pytest
pytest -s test_main.py
```

- 注：项目没有`__init__.py`会使得`pytest`报错。
- 参考：https://fastapi.tiangolo.com/tutorial/testing/?h=test
