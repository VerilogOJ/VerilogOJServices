from typing import Union
import subprocess
import os
from datetime import datetime

from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel


app = FastAPI()


class ServiceRequest(BaseModel):
    code_reference: str = Body(title="题目答案的Verilog源文件")
    code_student: str = Body(title="学生提交的Verilog源文件")
    testbench: str = Body(title="测试样例的Verilog文件，单个testbench表示一个测试点")
    top_module: str = Body(title="顶层模块的名称，注意需要保证学生、答案的顶层模块和top_module相同")


class ServiceResponse(BaseModel):
    is_correct: bool = Body(title="判题结果 true表示此测试点通过 wrong表示此测试点未通过")
    log: str = Body(title="过程日志")
    wavejson: str = Body(title="学生模块和答案模块的波形图")


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
    if not program_exists("iverilog"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="iverilog not installed", log=log).json(),
        )

    # [保存: 学生提交的Verilog 答案的Verilog testbench]

    base_path = "./temp_uuid/"

    code_student_path = base_path + "code_student.v"
    if service_request.code_student == "":
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error="no verilog source provided (student)", log=log
            ).json(),
        )
    os.makedirs(os.path.dirname(code_student_path), exist_ok=True)
    with open(code_student_path, "w") as f:
        f.write(service_request.code_student)

    code_reference_path = base_path + "code_reference.v"
    if service_request.code_reference == "":
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error="no verilog source provided (reference)", log=log
            ).json(),
        )
    os.makedirs(os.path.dirname(code_reference_path), exist_ok=True)
    with open(code_reference_path, "w") as f:
        f.write(service_request.code_reference)

    testbench_path = base_path + "testbench.v"
    if service_request.code_reference == "":
        raise HTTPException(
            status_code=400,
            detail=ServiceError(error="no testbench provided", log=log).json(),
        )
    os.makedirs(os.path.dirname(testbench_path), exist_ok=True)
    with open(testbench_path, "w") as f:
        f.write(service_request.testbench)

    # [跑一遍参考的仿真]
    # iverilog ./temp_uuid/testbench.v ./temp_uuid/code_reference.v -o ./temp_uuid/simulation_program_reference
    # vvp ./temp_uuid/simulation_program_reference
    # mv out.vcd ./temp_uuid/reference.vcd

    simulation_program_reference_path = base_path + "simulation_program_reference"
    vcd_reference_path = base_path + "reference.vcd"
    completed_iverilog_reference = subprocess.run(
        [
            f"iverilog {code_reference_path} {testbench_path} -D 'DUMP_FILE_NAME=\"{vcd_reference_path}\"' -o {simulation_program_reference_path}",
        ],
        capture_output=True,
        shell=True,
    )
    log += completed_iverilog_reference.stdout.decode("utf-8")
    completed_vvp_reference = subprocess.run(
        [f"vvp {simulation_program_reference_path}"],
        capture_output=True,
        shell=True,
    )
    log += completed_vvp_reference.stdout.decode("utf-8")
    if completed_iverilog_reference.returncode != 0 or completed_vvp_reference.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"reference code simulating failed\n{completed_iverilog_reference.stderr.decode('utf-8')}\n{completed_vvp_reference.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )
    

    # [跑一遍学生的仿真]
    simulation_program_student_path = base_path + "simulation_program_student"
    vcd_student_path = base_path + "student.vcd"
    completed_iverilog_student = subprocess.run(
        [
            f"iverilog {code_student_path} {testbench_path}  -D 'DUMP_FILE_NAME=\"{vcd_student_path}\"' -o {simulation_program_student_path}"
        ],
        capture_output=True,
        shell=True,
    )
    log += completed_iverilog_student.stdout.decode("utf-8")
    completed_vvp_student = subprocess.run(
        [f"vvp {simulation_program_student_path}"],
        capture_output=True,
        shell=True,
    )
    log += completed_vvp_student.stdout.decode("utf-8")
    if completed_iverilog_student.returncode != 0 or completed_vvp_student.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"student code simulating failed\n{completed_iverilog_student.stderr.decode('utf-8')}\n{completed_vvp_student.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )

    # [判断波形图是否一致]

    from . import vcd_main

    ret, msg = vcd_main.main()
    is_correct = ret
    log += msg

    # [得到波形的WaveJSON wave.json]

    from . import vcd_visualize

    wave_json_path = base_path + "wave.json"
    vcd_visualize.main()  # TODO: 可变参数

    # [读取netlist.svg并返回]
    with open(wave_json_path, "r") as f:
        wave_json_content = f.read()
    return ServiceResponse(is_correct=is_correct, log=log, wavejson=wave_json_content)
