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
cd test
python3 inverter_test.py
```

尝试发起服务 如果服务没问题 应该会输出下面的结果 并在`test/`文件夹内保存`netlist.svg`文件 用浏览器打开即可看到反相器的组合逻辑电路

```
[request started]
[request ended]
[status_code] 200
[successed]
[log] 16:54:38 开始处理
 /----------------------------------------------------------------------------\
 |                                                                            |
 |  yosys -- Yosys Open SYnthesis Suite                                       |

......

7.9. Finished OPT passes. (There is nothing left to do.)

8. Executing JSON backend.

End of script. Logfile hash: 58c97783f0, CPU: user 0.03s system 0.01s
Yosys 0.13 (git sha1 UNKNOWN, clang 13.0.0 -fPIC -Os)
Time spent: 46% 3x read_verilog (0 sec), 17% 6x opt_expr (0 sec), ...
```

## 部署

请使用项目根目录下的`docker-compose.yml`部署
