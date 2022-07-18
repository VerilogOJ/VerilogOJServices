# VerilogOJ服务 judger

## 简介

通过testbench对学生提交的Verilog代码和答案进行测试，输出波形一样则代表学生提交的代码正确。

## 开发

```sh
pip3 install -r requirements.txt && pip3 install -e pyDigitalWaveTools 
sudo apt install yosys iverilog # 此服务以Ubuntu20.04为准 macOS上通过brew安装的icarus-verilog的-o参数有问题
uvicorn main:app --reload
```

查看[服务文档](http://localhost:8000/docs)

### 测试

```sh
pip3 install pytest # or conda install pytest
pytest -s test_main.py
```
