from typing import Union, List
import subprocess
import os
from datetime import datetime

from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel


app = FastAPI()


class ServiceRequest(BaseModel):
    verilog_sources: List[str] = Body(title="Verilog源文件，可以是多文件")
    top_module: str = Body(title="顶层模块的名称")


class ServiceResponse(BaseModel):
    netlist_svg: Union[str, None] = Body(title="用netlistsvg生成的逻辑电路图")
    log: str = Body(title="过程日志")


class ServiceError(BaseModel):
    error: Union[str, None] = Body(title="发生的错误信息")
    log: str = Body(title="过程日志")


@app.post(
    "/",
    # https://fastapi.tiangolo.com/advanced/additional-responses/
    responses={
        200: {"model": ServiceResponse, "description": "成功转为svg"},
        400: {"model": ServiceError, "description": "程序内部出错"},
    },
)
def convert_verilog_sources_to_netlist_svg(service_request: ServiceRequest):
    """
    上传Verilog源文件并制定顶层模块，返回逻辑电路图svg
    """

    print(f"start with request {service_request}")
    log = "开始处理" + datetime.now().strftime("%Y/%m/%d, %H:%M:%S")

    # [判断宿主机程序存在]

    def program_exists(program_name: str) -> Union[str, None]:
        """Check whether `name` is on PATH and marked as executable."""
        from shutil import which

        return which(program_name) is not None

    if not program_exists("yosys"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="yosys not installed", log=log).json(),
        )
    if not program_exists("netlistsvg"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="netlistsvg not installed", log=log).json(),
        )

    # [保存用户上传的verilog源文件]
    base_path = "./temp/"
    verilog_sources_folder = "verilog_sources/"
    if service_request.verilog_sources.count == 0:
        raise HTTPException(
            status_code=400,
            detail=ServiceError(error="no verilog sources provided", log=log).json(),
        )
    verilog_sources_path = []
    for i, verilog_source in enumerate(service_request.verilog_sources):
        verilog_source_path = base_path + verilog_sources_folder + str(i) + ".v"
        verilog_sources_path.append(verilog_source_path)
        os.makedirs(os.path.dirname(verilog_source_path), exist_ok=True)
        with open(verilog_source_path, "w") as f:
            f.write(verilog_source)

    # [生成yosys脚本]
    netlist_json_path = base_path + "netlist.json"
    yosys_script_content = f"""
    read -sv {" ".join(verilog_sources_path)}
    hierarchy -top {service_request.top_module}
    proc; opt; techmap; opt
    write_json {netlist_json_path}
    """
    yosys_script_path = base_path + "verilog2netlistsvg.ys"
    os.makedirs(os.path.dirname(yosys_script_path), exist_ok=True)
    with open(yosys_script_path, "w") as f:
        f.write(yosys_script_content)

    # [运行yosys脚本]
    completed_yosys = subprocess.run(
        [f"yosys {yosys_script_path}"],  # 注意这里块不能分开写 否则yosys会进入交互模式
        capture_output=True,
        shell=True,
    )  # https://docs.python.org/3/library/subprocess.html#subprocess.run
    log += completed_yosys.stdout.decode("utf-8")
    if completed_yosys.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"run yosys failed {completed_yosys.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )

    # [运行netlistsvg]
    netlist_svg_path = base_path + "netlist.svg"
    completed_netlistsvg = subprocess.run(
        ["netlistsvg", netlist_json_path, "-o", netlist_svg_path],
        capture_output=True,
    )
    log += completed_netlistsvg.stdout.decode("utf-8")
    if completed_netlistsvg.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"run netlistsvg failed {completed_netlistsvg.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )

    # [读取netlist.svg并返回]
    with open(netlist_svg_path, "r") as f:
        netlist_svg_content = f.read()
    return ServiceResponse(log=log, netlist_svg=netlist_svg_content)
