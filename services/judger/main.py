from typing import Union
import subprocess
import os
from datetime import datetime

from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel

# ------------

# [wavedump.py]


from pyDigitalWaveTools.vcd.parser import VcdParser


class VcdSignalTraversalError(Exception):
    pass


class VcdSignalComparationError(Exception):
    pass


def find_signal_inst(data_obj, signal_path):
    components = signal_path.split("/")
    cur = data_obj
    for i in range(0, len(components) - 1):
        if cur["name"] != components[i]:
            raise VcdSignalTraversalError(
                "{} mismatch with {} while traversing {}".format(
                    cur["name"], components[i], signal_path
                )
            )

        if not "children" in cur.keys():
            raise VcdSignalTraversalError(
                "{} have no data k-v pair while traversing {}".format(
                    cur["name"], signal_path
                )
            )

        found = False
        for child in cur["children"]:
            if child["name"] == components[i + 1]:
                found = True
                cur = child
                break

        if not found:
            raise VcdSignalTraversalError(
                "{} have no children called {} while traversing {}".format(
                    cur["name"], components[i + 1], signal_path
                )
            )

    if cur["name"] != components[-1]:
        raise VcdSignalTraversalError(
            "{} mismatch with {} while traversing {}".format(
                cur["name"], components[-1], signal_path
            )
        )

    return cur


class VcdComparator:
    def compare_signals(self, ref, ud):
        # compare width
        if ref["type"]["width"] != ud["type"]["width"]:
            raise VcdSignalComparationError(
                "Signal {} have different width between ref ({}) and ud ({})".format(
                    ref["name"], ref["type"]["width"], ud["type"]["width"]
                )
            )

        # No need to compare sigType (reg/wire.. anything else?)

        # signal comparation
        # TODO: support for different types ('b0' with 'b000' or 'd0' or something...)

        # Since value change dump theoretically only generates data when changes
        # so direct diffing should work
        for i, val in enumerate(ref["data"]):
            if ud["data"][i] != val:
                raise VcdSignalComparationError(
                    "Signal {} have difference on time {} (ref={}, ud={})".format(
                        ref["name"], val[0], val, ud["data"][i]
                    )
                )

    def dump_hierarchy(self, data_obj):
        # TODO: only dump names
        print(data_obj.toJSON())

    def __init__(self, vcd_ref, vcd_ut, signal_names):
        """Initialize signals for comparation
        vcd_ref: the reference vcd file
        vcd_ut: the vcd file under test
        signal_names: the signal for comparation, uses "/" to express hierarchy.
                and the top module name shall also be included.
        """

        with open(vcd_ref) as vcd_ref_file:
            vcd = VcdParser()
            vcd.parse(vcd_ref_file)
            self.data_ref = vcd.scope.toJson()
            print(self.data_ref)

        with open(vcd_ut) as vcd_ut_file:
            vcd_ut = VcdParser()
            vcd_ut.parse(vcd_ut_file)
            self.data_ut = vcd_ut.scope.toJson()
            print(self.data_ut)

        # find all signals
        self.signals_ref = [find_signal_inst(self.data_ref, i) for i in signal_names]
        self.signals_ut = [find_signal_inst(self.data_ut, i) for i in signal_names]

    def compare(self):
        try:
            # compare all signals
            for i in range(0, len(self.signals_ref)):
                self.compare_signals(self.signals_ref[i], self.signals_ut[i])
            return (True, "No error")
        except VcdSignalComparationError as e:
            return (False, "{}".format(e))


# [vcd_main.py]

import json


class VcdSignalValueParseError(Exception):
    pass


class VcdConverter:
    def __init__(self, data_vcd):
        self.output = {"signal": []}
        self.data_vcd = data_vcd

    def emitWaveDict(self):
        return self.output

    def mergeWaveDict(self, wdict):
        self.output["signal"] += wdict["signal"]

    def emitWaveJson(self):
        return json.dumps(self.output)

    def parseValue(self, val_str):
        """Note: b111xx1 -> x"""
        if val_str[0] == "b":
            if val_str.find("x") != -1:
                return "x"
            return int(val_str[1:], base=2)
        elif len(val_str) == 1:
            if val_str[0] == "x":
                return "x"
            else:
                return int(val_str, base=2)
        else:
            raise VcdSignalValueParseError("Unknown value type")

    def toBinRepr(self, val, width):
        if val == "x":
            return "x" * width

        striped = bin(val)[2:]
        assert width >= len(striped)
        return "0" * (width - len(striped)) + striped

    def addToWaveJsonSeparate(self, signal_names, prefix=""):
        # find common time_max
        time_max = 0
        for signal_name in signal_names:
            sig_inst = find_signal_inst(self.data_vcd, signal_name)
            time_max = max(time_max, sig_inst["data"][-1][0])

        for signal_name in signal_names:
            sig_jsons = []
            sig_inst = find_signal_inst(self.data_vcd, signal_name)

            width = sig_inst["type"]["width"]
            # decompose
            for i in range(0, width):
                sig_jsons.append({})
                sig_jsons[i]["name"] = prefix + sig_inst["name"] + "[" + str(i) + "]"

            local_time_max = sig_inst["data"][-1][0]
            waves = ["" for i in range(0, width)]
            cur_step_ptr = 0

            # "x" or int or "SOME.."
            cur_wave = "SOMETHING_NEVER_HAPPEN"

            # TODO: Avoid multiple transitions at same timestep
            for i in range(0, local_time_max + 1):
                if sig_inst["data"][cur_step_ptr][0] > i:
                    # maintain current value
                    for i in range(0, width):
                        waves[i] += "."
                else:
                    new_wave = self.parseValue(sig_inst["data"][cur_step_ptr][1])
                    if new_wave == cur_wave:
                        waves[i] += "."
                    else:
                        # do bitwise comparation
                        if cur_wave == "SOMETHING_NEVER_HAPPEN":
                            # new_wave_bin[0] is MSB
                            new_wave_bin = self.toBinRepr(new_wave, width)
                            for i in range(0, width):
                                waves[i] += new_wave_bin[::-1][i]
                        else:
                            cur_wave_bin = self.toBinRepr(cur_wave, width)
                            new_wave_bin = self.toBinRepr(new_wave, width)

                            for i in range(0, width):
                                old = cur_wave_bin[::-1][i]
                                new = new_wave_bin[::-1][i]
                                if old != new:
                                    waves[i] += new
                                else:
                                    waves[i] += "."

                        cur_wave = new_wave

                    cur_step_ptr += 1

            for i in range(local_time_max, time_max + 1):
                for i in range(0, width):
                    waves[i] += "."

            for i in range(0, width):
                sig_jsons[i]["wave"] = waves[i]

            self.output["signal"] += sig_jsons

    def addToWaveJsonAggregated(self, signal_names, prefix=""):
        """Aggregated view, which uses '=' on every timeslice."""
        # find common time_max
        time_max = 0
        for signal_name in signal_names:
            sig_inst = find_signal_inst(self.data_vcd, signal_name)
            time_max = max(time_max, sig_inst["data"][-1][0])

        for signal_name in signal_names:
            sig_json = {}
            sig_inst = find_signal_inst(self.data_vcd, signal_name)
            sig_json["name"] = prefix + sig_inst["name"]

            # [0, time_max]
            local_time_max = sig_inst["data"][-1][0]
            wave = ""
            cur_step_ptr = 0
            cur_wave = "SOMETHING_NEVER_HAPPEN"
            data = []

            # TODO: Avoid multiple transitions at same timestep
            for i in range(0, local_time_max + 1):
                if sig_inst["data"][cur_step_ptr][0] > i:
                    # maintain current value
                    wave += "."
                else:
                    new_wave = self.parseValue(sig_inst["data"][cur_step_ptr][1])
                    if new_wave == cur_wave:
                        wave += "."
                    else:
                        wave += "="
                        data.append(new_wave)
                        cur_wave = new_wave

                    cur_step_ptr += 1

            for i in range(local_time_max, time_max + 1):
                wave += "."

            sig_json["wave"] = wave
            sig_json["data"] = data

            self.output["signal"].append(sig_json)


def vcd_main():
    from .wavedump import VcdComparator

    cmpr = VcdComparator(
        "./temp_uuid/reference.vcd",
        "./temp_uuid/student.vcd",
        ["root/testbench/x", "root/testbench/y"],
    )  # TODO 这里看起来是要放入信号的样子 这里testbench是testbench.v中模块的名称 之后的x和y是信号的名称
    ret, msg = cmpr.compare()
    print(msg)
    print("Ret status: {}".format(ret))
    return (ret, msg)


# [vcd_visual.py]


def vcd_visual():
    from pyDigitalWaveTools.vcd.parser import VcdParser

    with open("./temp_uuid/reference.vcd") as f:
        vcd = VcdParser()
        vcd.parse(f)
        data_reference = vcd.scope.toJson()

    with open("./temp_uuid/student.vcd") as f:
        vcd = VcdParser()
        vcd.parse(f)
        data_student = vcd.scope.toJson()

    vc_reference = VcdConverter(data_reference)
    vc_reference.addToWaveJsonSeparate(
        ["root/testbench/x", "root/testbench/y"], "reference_"
    )
    vc_reference.addToWaveJsonAggregated(
        ["root/testbench/x", "root/testbench/y"], "reference_"
    )

    vc_student = VcdConverter(data_student)
    vc_student.addToWaveJsonSeparate(["root/testbench/x", "root/testbench/y"], "your_")
    vc_student.addToWaveJsonAggregated(
        ["root/testbench/x", "root/testbench/y"], "your_"
    )

    vc_reference.mergeWaveDict(vc_student.emitWaveDict())
    out = vc_reference.emitWaveJson()

    with open("./temp_uuid/wave.json", "w") as f:
        f.write(out)


# ------------

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
def judge_student_code(service_request: ServiceRequest):
    """
    上传学生的Verilog代码、答案、testbench并指定顶层模块，返回判题结果和信号波形图
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
    if (
        completed_iverilog_reference.returncode != 0
        or completed_vvp_reference.returncode != 0
    ):
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
    if (
        completed_iverilog_student.returncode != 0
        or completed_vvp_student.returncode != 0
    ):
        raise HTTPException(
            status_code=400,
            detail=ServiceError(
                error=f"student code simulating failed\n{completed_iverilog_student.stderr.decode('utf-8')}\n{completed_vvp_student.stderr.decode('utf-8')}",
                log=log,
            ).json(),
        )

    # [判断波形图是否一致]

    ret, msg = vcd_main()
    is_correct = ret
    log += msg

    # [得到波形的WaveJSON wave.json]

    from . import vcd_visualize

    wave_json_path = base_path + "wave.json"
    vcd_visualize()  # TODO: 可变参数

    # [读取netlist.svg并返回]

    with open(wave_json_path, "r") as f:
        wave_json_content = f.read()
    return ServiceResponse(is_correct=is_correct, log=log, wavejson=wave_json_content)
