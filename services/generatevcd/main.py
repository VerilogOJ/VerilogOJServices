from typing import Union, List
import subprocess
import os
import uuid
from datetime import datetime

from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel

app = FastAPI()


class ServiceRequest(BaseModel):
    top_module: str = Body(title="顶层模块的名称")
    verilog_sources: List[str] = Body(title="Verilog源代码")
    testbench: str = Body(title="测试样例")


class ServiceResponse(BaseModel):
    log: str = Body(title="过程日志")
    vcd: str = Body(title="vvp生成的波形文件")


class ServiceError(BaseModel):
    error: str = Body(title="错误信息")
    log: str = Body(title="过程日志")


@app.post(
    "/",
    # https://fastapi.tiangolo.com/advanced/additional-responses/
    responses={
        200: {"model": ServiceResponse, "description": "判题结束"},
        400: {"model": ServiceError, "description": "程序内部出错"},
    },
)
def generate_vcd(service_request: ServiceRequest):
    """使用vvp仿真得到波形图"""

    log_temp = f"""开始处理 {datetime.now().strftime("%Y/%m/%d, %H:%M:%S")}\n"""
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
    if not program_exists("iverilog"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="iverilog not installed", log=log).json(),
        )
    if not program_exists("vvp"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="vvp(iverilog) not installed", log=log).json(),
        )

    log_temp = f"""仿真软件已安装\n"""
    log += log_temp
    print(log_temp)

    # [生成根文件夹]

    processing_id = uuid.uuid4().hex
    base_path = f"./temp/{processing_id}/"

    # [保存: 学生提交的Verilog 答案的Verilog testbench]

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

    testbench_path = base_path + "testbench.v"
    if service_request.testbench == "":
        raise HTTPException(
            status_code=400,
            detail=ServiceError(error="no testbench provided", log=log).json(),
        )
    os.makedirs(os.path.dirname(testbench_path), exist_ok=True)
    with open(testbench_path, "w") as f:
        f.write(service_request.testbench)

    log_temp = f"""提交文件已保存\n"""
    log += log_temp
    print(log_temp)

    # [生成yosys脚本]

    yosys_verilog_path = base_path + "netlist.json"
    yosys_script_content = f"""
read_verilog {" ".join(verilog_sources_path)} 
synth -top {service_request.top_module}
write_verilog {yosys_verilog_path}
    """.strip()
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
                error=f"run yosys failed\n{completed_yosys.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )


    # [跑仿真]

    simulation_program_path = base_path + "simulation_program"
    vcd_reference_path = base_path + "reference.vcd"
    completed_iverilog_reference = subprocess.run(
        [
            f"""iverilog {" ".join(verilog_sources_path)} {testbench_path} -D 'DUMP_FILE_NAME="{vcd_reference_path}"' -o {simulation_program_path}"""
        ],
        capture_output=True,
        shell=True,
    )
    print(f"""iverilog -D 'DUMP_FILE_NAME="{vcd_reference_path}"' -o {simulation_program_path} {" ".join(verilog_sources_path)} {testbench_path}""")
    log += completed_iverilog_reference.stdout.decode("utf-8") + "\n"
    print(log)
    completed_vvp_reference = subprocess.run(
        [f"vvp {simulation_program_path}"],
        capture_output=True,
        shell=True,
    )
    log += completed_vvp_reference.stdout.decode("utf-8") + "\n"
    if (
        completed_iverilog_reference.returncode != 0
        or completed_vvp_reference.returncode != 0
    ):
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"simulating failed\n{completed_iverilog_reference.stderr.decode('utf-8')}\n{completed_vvp_reference.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )

    log_temp = f"""仿真结束\n"""
    log += log_temp
    print(log_temp)

    with open(vcd_reference_path, "r") as f:
        vcd = f.read()
    return ServiceResponse(log=log, vcd=vcd)
