from typing import Union, List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class RequestData(BaseModel):
    verilog_sources: List[str]
    top_module: str


class Response(BaseModel):
    log: str
    error: str
    netlist_svg: str


@app.put("/")
def convert_verilog_sources_to_netlist_svg(data: RequestData):
    # [步骤]
    # 使用yosys 解析verilog看其中是否有语法错误 生成json网表
    # 使用netlistsvg生成svg

    response = Response()
    return {"service_id": 1, "data": data}
