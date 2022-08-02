from typing import Union, List
import subprocess
import os
import uuid
from datetime import datetime

from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel

# ------------------------


class ServiceRequest(BaseModel):
    verilog_sources: List[str] = Body(title="Verilog源文件，可以是多文件")
    top_module: str = Body(title="顶层模块的名称")


class ServiceResponse(BaseModel):
    resources_report: str = Body(title="资源占用报告（yosys的log中提取得到）")
    yosys_show_svg: str = Body(title="元件库映射的电路图（yosys的show命令生成）")
    netlistsvg_default: str = Body(
        title="netlistsvg电路图（yosys的write_json命令结合netlistsvg工具的default_skin得到）"
    )
    netlistsvg_google130nm: str = Body(
        title="netlistsvg电路图（yosys的write_json命令结合提前手动生成的google130nm_skin得到）"
    )
    sta_report: str = Body(title="时序分析报告（opensta分析得到）")
    # sdf_content: str = Body(title="标准延时文件内容（opensta的write_sdf命令得到）")

    log: str = Body(title="过程日志")


class ServiceError(BaseModel):
    error: str = Body(title="发生的错误信息")

    log: str = Body(title="过程日志")


# ------------------------

app = FastAPI()


@app.post(
    path="/",
    # https://fastapi.tiangolo.com/advanced/additional-responses/
    summary="使用Google130nm元件库生成电路图、资源占用报告、时序分析",
    description="""上传Verilog源文件并指定使用的元件库（和顶层模块），使用Google130nm元件库生成电路图、资源占用报告、时序分析。
    """,
    responses={
        200: {"model": ServiceResponse, "description": "成功生成电路与资源占用报告。"},
        400: {
            "model": ServiceError,
            "description": '程序内部出错。使用`json.loads(json.loads(response_origin.content)["detail"])`取到`ServiceError`结构体。进一步取出`error`和`log`字段。',
        },
    },
)
def get_google130nm_analysis(service_request: ServiceRequest):
    log_temp = f"""开始处理 {datetime.now().strftime("%Y/%m/%d, %H:%M:%S")}
请求：{service_request}\n"""
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
    log_temp = f"""yosys已安装\n"""
    log += log_temp
    print(log_temp)

    if not program_exists("sta"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="opensta not installed", log=log).json(),
        )
    log_temp = f"""opensta已安装\n"""
    log += log_temp
    print(log_temp)

    if not program_exists("netlistsvg"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="netlistsvg not installed", log=log).json(),
        )
    log_temp = f"""netlistsvg已安装\n"""
    log += log_temp
    print(log_temp)

    # [保存用户上传的verilog源文件]

    processing_id = uuid.uuid4().hex  # https://docs.python.org/3/library/uuid.html
    base_path = f"./temp/{processing_id}/"
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

    log_temp = f"""Verilog源文件已保存\n"""
    log += log_temp
    print(log_temp)

    # [生成yosys脚本]

    output_info_path = base_path + "info.txt"
    google_130nm_lib_path = "./lib/sky130_fd_sc_hd__tt_025C_1v80.lib"

    yosys_show_svg_path = base_path + "circuit_bad"
    yosys_verilog_path = base_path + "module.v"
    yosys_json_path = base_path + "module.json"
    yosys_script_content = f"""
read -sv {" ".join(verilog_sources_path)}
synth -top {service_request.top_module}
read_liberty -lib {google_130nm_lib_path}
abc -liberty {google_130nm_lib_path}
tee -a {output_info_path} stat
show -notitle -stretch -format svg -prefix {yosys_show_svg_path}
write_verilog {yosys_verilog_path}
write_json {yosys_json_path}
    """.strip()
    yosys_show_svg_path += ".svg"

    yosys_script_path = base_path + "synth.ys"
    os.makedirs(os.path.dirname(yosys_script_path), exist_ok=True)
    with open(yosys_script_path, "w") as f:
        f.write(yosys_script_content)

    log_temp = f"""yosys脚本已生成\n"""
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

    log_temp = f"""yosys脚本成功运行\n"""
    log += log_temp
    print(log_temp)

    # [从yosys的标准输出中正则提取到资源占用情况]

    with open(output_info_path, "r") as f:
        resources_report = f.read().replace("5. Printing statistics.", "").strip()
    log_temp = f"""资源报告已提取\n"""
    log += log_temp
    print(log_temp)

    # [读取yosys`show`命令得到的svg]

    with open(yosys_show_svg_path, "r") as f:
        yosys_show_svg = f.read()

    # [netlistsvg]
    netlistsvg_default_path = base_path + "netlist_default.svg"
    netlistsvg_google130_path = base_path + "netlist_default.svg"
    google130nm_skin_path = "./google130nm/google130nm_skin.svg"
    completed_netlistsvg_default = subprocess.run(
        [
            "netlistsvg",
            f"{yosys_json_path}",
            "-o",
            f"{netlistsvg_default_path}",
        ],
        capture_output=True,
    )
    completed_netlistsvg_google130nm = subprocess.run(
        [
            "netlistsvg",
            f"{yosys_json_path}",
            "-o",
            f"{netlistsvg_google130_path}",
            "--skin",
            f"{google130nm_skin_path}",
        ],
        capture_output=True,
    )
    log += (
        completed_netlistsvg_default.stdout.decode("utf-8")
        + "\n"
        + completed_netlistsvg_google130nm.stdout.decode("utf-8")
    )
    if (
        completed_netlistsvg_default.returncode != 0
        or completed_netlistsvg_google130nm.returncode != 0
    ):
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"run netlistsvg failed {completed_netlistsvg_default.stderr.decode('utf-8')}\n{completed_netlistsvg_google130nm.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )
    log_temp = f"""netlistsvg已生成\n"""
    log += log_temp
    print(log_temp)

    # [读取netlistsvg]

    with open(netlistsvg_default_path, "r") as f:
        netlistsvg_default = f.read()
    with open(netlistsvg_google130_path, "r") as f:
        netlistsvg_google130nm = f.read()

    log_temp = f"""netlistsvg已提取\n"""
    log += log_temp
    print(log_temp)

    # [生成OpenSTA脚本]

    # sdf_path = base_path + "sta.sdf"
    google_130nm_lib_path = "./lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
    opensta_script_content = f"""
read_liberty {google_130nm_lib_path}
read_verilog {yosys_verilog_path}
link_design inverter

create_clock -name clk -period 10
set_input_delay -clock clk 0 {{*}}
set_output_delay -clock clk 0 {{*}}

report_checks
    """.strip()
# write_sdf {sdf_path}

    opensta_script_path = base_path + "sta.txt"
    os.makedirs(os.path.dirname(opensta_script_path), exist_ok=True)
    with open(opensta_script_path, "w") as f:
        f.write(opensta_script_content)

    log_temp = f"""OpenSTA脚本已生成\n"""
    log += log_temp
    print(log_temp)

    # [执行OpenSTA脚本]

    completed_sta = subprocess.run(
        [f"sta -no_splash -exit {opensta_script_path}"],
        capture_output=True,
        shell=True,
    )  # https://docs.python.org/3/library/subprocess.html#subprocess.run
    log += completed_sta.stdout.decode("utf-8")
    if completed_sta.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"run sta failed\n{completed_sta.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )

    log_temp = f"""OpenSTA脚本成功运行\n"""
    log += log_temp
    print(log_temp)

    # [拿到sta分析结果]

    sta_report = completed_sta.stdout.decode("utf-8")

    log_temp = f"""取得时序分析结果\n"""
    log += log_temp
    print(log_temp)

    # [拿到sdf文件内容]

    # with open(sdf_path, "r") as f:
    #     sdf_content = f.read()

    # log_temp = f"""取得sdf内容\n"""
    # log += log_temp
    # print(log_temp)

    return ServiceResponse(
        log=log,
        resources_report=resources_report,
        yosys_show_svg=yosys_show_svg,
        netlistsvg_default=netlistsvg_default,
        netlistsvg_google130nm=netlistsvg_google130nm,
        sta_report=sta_report,
        # sdf_content=sdf_content,
    )
