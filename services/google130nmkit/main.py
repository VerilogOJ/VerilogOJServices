from typing import Union, List
import subprocess
import os
import uuid
import re
from datetime import datetime

from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel




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
        """
        Initialize signals for comparation
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


def vcd_visualize(
    vcd_file_path: str, signal_names: List[str]
) -> str:
    with open(vcd_file_path) as f:
        vcd = VcdParser()
        vcd.parse(f)
        data_reference = vcd.scope.toJson()

    vcd_converter = VcdConverter(data_reference)
    vcd_converter.addToWaveJsonSeparate(
        list(map(lambda name: f"root/testbench/{name}", signal_names)), "reference_"
    )
    vcd_converter.addToWaveJsonAggregated(
        list(map(lambda name: f"root/testbench/{name}", signal_names)), "reference_"
    )

    vcd_converter.mergeWaveDict(vcd_converter.emitWaveDict())
    out = vcd_converter.emitWaveJson()
    return out

# ------------------------

app = FastAPI()


class ServiceRequest(BaseModel):
    verilog_sources: List[str] = Body(title="Verilog源文件，可以是多文件")
    top_module: str = Body(title="顶层模块的名称")


class ServiceResponse(BaseModel):
    log: str = Body(title="过程日志")

    resources_report: str = Body(title="资源占用报告")
    circuit_svg: str = Body(title="元件库映射的电路图")
    circuit_netlistsvg: str = Body(title="元件库映射的netlistsvg电路图")
    sta_report: str = Body(title="时序分析报告")
    simulation_wavejson: str = Body(title="用Google130nm元件库映射后仿真得到的WaveJSON")


class ServiceError(BaseModel):
    log: str = Body(title="过程日志")

    error: str = Body(title="发生的错误信息")


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

    if not program_exists("iverilog"):
        raise HTTPException(
            status_code=404,
            detail=ServiceError(error="iverilog not installed", log=log).json(),
        )
    log_temp = f"""iverilog已安装\n"""
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

    log_temp = f"""Verilog源文件已保存\n"""
    log += log_temp
    print(log_temp)

    # [生成yosys脚本]

    output_info_path = base_path + "info.txt"
    google_130nm_lib_path = "./lib/sky130_fd_sc_hd__tt_025C_1v80.lib"

    circuit_svg_path = base_path + "circuit_bad"
    yosys_verilog_path = base_path + "module.v"
    yosys_json_path = base_path + "module.json"
    yosys_script_content = f"""
read -sv {" ".join(verilog_sources_path)}
synth -top {service_request.top_module}
read_liberty -lib {google_130nm_lib_path}
abc -liberty {google_130nm_lib_path}
tee -a {output_info_path} stat
show -notitle -stretch -format svg -prefix {circuit_svg_path}
write_verilog {yosys_verilog_path}
write_json {yosys_json_path}
    """.strip()
    circuit_svg_path += ".svg"

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

    with open(circuit_svg_path, "r") as f:
        circuit_svg_content = f.read()

        netlist_svg_path = base_path + "netlist.svg"
    completed_netlistsvg = subprocess.run(
        # https://github.com/nturley/netlistsvg#generating-input_json_file-with-yosys
        ["netlistsvg", yosys_json_path, "-o", netlist_svg_path],
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
    log_temp = f"""netlistsvg已生成\n"""
    log += log_temp
    print(log_temp)

    # [读取netlistsvg]

    with open(netlist_svg_path, "r") as f:
        circuit_netlistsvg_content = f.read()
    log_temp = f"""netlistsvg已提取\n"""
    log += log_temp
    print(log_temp)

    # [生成OpenSTA脚本]

    sdf_path = base_path + "sta.sdf"
    google_130nm_lib_path = "./lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
    opensta_script_content = f"""
read_liberty {google_130nm_lib_path}
read_verilog {yosys_verilog_path}
link_design inverter

create_clock -name clk -period 10
set_input_delay -clock clk 0 {{*}}
set_output_delay -clock clk 0 {{*}}

report_checks
write_sdf {sdf_path}
    """.strip()

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

    return ServiceResponse(
        log=log,

        resources_report=resources_report,
        circuit_svg=circuit_svg_content,
        circuit_netlistsvg=circuit_netlistsvg_content,
        sta_report=sta_report,
        simulation_wavejson="TODO 用iverilog和vvp 跑 Google130nm的.v、yosys生成的.v、sta生成的sdf 拿到仿真结果"
    )
