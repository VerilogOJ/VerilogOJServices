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
[successed] {
  "log": "16:39:15开始处理",
  "error": null,
  "netlist_svg": "<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xmlns:s=\"https://github.com/nturley/netlistsvg\" width=\"184\" height=\"54\">\n  <style>svg {\n    stroke:#000;\n    fill:none;\n  }\n  text {\n    fill:#000;\n    stroke:none;\n    font-size:10px;\n    font-weight: bold;\n    font-family: \"Courier New\", monospace;\n  }\n  .nodelabel {\n    text-anchor: middle;\n  }\n  .inputPortLabel {\n    text-anchor: end;\n  }\n  .splitjoinBody {\n    fill:#000;\n  }</style>\n  <g s:type=\"not\" transform=\"translate(77,22)\" s:width=\"30\" s:height=\"20\" id=\"cell_$auto$simplemap.cc:38:simplemap_not$75\">\n    <s:alias val=\"$_NOT_\"/>\n    <s:alias val=\"$not\"/>\n    <s:alias val=\"$logic_not\"/>\n    <path d=\"M0,0 L0,20 L20,10 Z\" class=\"cell_$auto$simplemap.cc:38:simplemap_not$75\"/>\n    <circle cx=\"23\" cy=\"10\" r=\"3\" class=\"cell_$auto$simplemap.cc:38:simplemap_not$75\"/>\n    <g s:x=\"0\" s:y=\"10\" s:pid=\"A\"/>\n    <g s:x=\"25\" s:y=\"10\" s:pid=\"Y\"/>\n  </g>\n  <g s:type=\"inputExt\" transform=\"translate(12,22)\" s:width=\"30\" s:height=\"20\" id=\"cell_in\">\n    <text x=\"15\" y=\"-4\" class=\"nodelabel cell_in\" s:attribute=\"ref\">in</text>\n    <s:alias val=\"$_inputExt_\"/>\n    <path d=\"M0,0 L0,20 L15,20 L30,10 L15,0 Z\" class=\"cell_in\"/>\n    <g s:x=\"28\" s:y=\"10\" s:pid=\"Y\"/>\n  </g>\n  <g s:type=\"outputExt\" transform=\"translate(142,22)\" s:width=\"30\" s:height=\"20\" id=\"cell_out\">\n    <text x=\"15\" y=\"-4\" class=\"nodelabel cell_out\" s:attribute=\"ref\">out</text>\n    <s:alias val=\"$_outputExt_\"/>\n    <path d=\"M30,0 L30,20 L15,20 L0,10 L15,0 Z\" class=\"cell_out\"/>\n    <g s:x=\"0\" s:y=\"10\" s:pid=\"A\"/>\n  </g>\n  <line x1=\"40\" x2=\"77\" y1=\"32\" y2=\"32\" class=\"net_2\"/>\n  <line x1=\"102\" x2=\"142\" y1=\"32\" y2=\"32\" class=\"net_3\"/>\n</svg>\n"
}
```

## 部署

请使用项目根目录下的`docker-compose.yml`部署
