from typing import Union, List
import subprocess
import os
import uuid
from datetime import datetime

from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel


app = FastAPI()


class ServiceRequest(BaseModel):
    verilog_sources: List[str] = Body(title="Verilog源文件，可以是多文件")
    top_module: str = Body(title="顶层模块的名称")
    library_type: str = Body(title="使用的元件库名称")  # google_130nm, yosys_ # TODO


class ServiceResponse(BaseModel):
    circuit_svg: str = Body(title="生成的元件库映射电路图")
    resources_report: str = Body(title="资源占用报告")
    log: str = Body(title="过程日志")


class ServiceError(BaseModel):
    error: str = Body(title="发生的错误信息")
    log: str = Body(title="过程日志")


@app.post(
    "/",
    # https://fastapi.tiangolo.com/advanced/additional-responses/
    responses={
        200: {"model": ServiceResponse, "description": "成功生成电路与资源占用报告"},
        400: {"model": ServiceError, "description": "程序内部出错"},
    },
)
def convert_verilog_sources_to_library_mapping_circuit(service_request: ServiceRequest):
    """上传Verilog源文件并指定使用的元件库（和顶层模块），生成电路图和资源占用报告。"""

    log_temp = f"""开始处理 {datetime.now().strftime("%Y/%m/%d, %H:%M:%S")}
请求：{service_request}"""
    log = log_temp
    print(log_temp)

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
    log_temp = f"""仿真软件已安装"""
    log += log_temp
    print(log_temp)

    # [保存用户上传的verilog源文件]

    processing_id = uuid.uuid4().hex
    base_path = (
        f"./temp/{processing_id}/"  # https://docs.python.org/3/library/uuid.html
    )
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

    log_temp = f"""Verilog源文件已保存"""
    log += log_temp
    print(log_temp)

    # [生成yosys脚本]

    mapping_circuit_svg_path = base_path + "mapping_circuit"
    yosys_script_content = f"""
    read -sv {" ".join(verilog_sources_path)}
    synth_xilinx -top {service_request.top_module}
    show -notitle -stretch -format svg -prefix {mapping_circuit_svg_path}
    """
    mapping_circuit_svg_path += ".svg"
    yosys_script_path = base_path + "verilog2mappingcircuit.ys"
    os.makedirs(os.path.dirname(yosys_script_path), exist_ok=True)
    with open(yosys_script_path, "w") as f:
        f.write(yosys_script_content)

    log_temp = f"""yosys脚本已生成"""
    log += log_temp
    print(log_temp)

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
                error=f"run yosys failed\n{completed_yosys.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )
    
    log_temp = f"""yosys脚本成功运行"""
    log += log_temp
    print(log_temp)

    # [读取svg并返回]

    with open(mapping_circuit_svg_path, "r") as f:
        mapping_circuit_svg_content = f.read()
    return ServiceResponse(
        circuit_svg=mapping_circuit_svg_content, resources_report="...TODO...", log=log
    )
