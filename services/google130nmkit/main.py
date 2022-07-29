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


def vcd_visualize(vcd_file_path: str, signal_names: List[str]) -> str:
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





# ------------------------


class ServiceRequest(BaseModel):
    verilog_sources: List[str] = Body(title="Verilog源文件，可以是多文件")
    testbench: str = Body(title="测试样例的Verilog文件", description="顶层模块的名称必须为`testbench`")
    # top_module: str = Body(title="顶层模块的名称")
    signal_names: List[str] = Body(
        title="需要进行波形显示的信号名称", description="指testbench中模块的信号名称"
    )


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

    # [保存上传的testbench]

    testbench_path = base_path + "testbench.v"
    if service_request.testbench == "":
        raise HTTPException(
            status_code=400,
            detail=ServiceError(error="no testbench provided", log=log).json(),
        )
    os.makedirs(os.path.dirname(testbench_path), exist_ok=True)
    with open(testbench_path, "w") as f:
        f.write(service_request.testbench)

    log_temp = f"""testbench已保存\n"""
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

    # [后仿 iverilog无法实现时序仿真 准备尝试verilator]

#     # [iverilog生成]

#     vcd_path = base_path + "vcd.vcd"
#     simulation_program_path = base_path + "simulation_program"

#     iverilog_command = f"""
# iverilog -g2012 \\
# -I ./google130nm/sky130_fd_sc_hd/latest/cells/a2111o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a2111oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a211o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a211oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a21bo -I ./google130nm/sky130_fd_sc_hd/latest/cells/a21boi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a21o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a21oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a221o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a221oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a222oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a22o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a22oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a311o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a311oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a31o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a31oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a32o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a32oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/a41o -I ./google130nm/sky130_fd_sc_hd/latest/cells/a41oi -I ./google130nm/sky130_fd_sc_hd/latest/cells/and2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/and2b -I ./google130nm/sky130_fd_sc_hd/latest/cells/and3 -I ./google130nm/sky130_fd_sc_hd/latest/cells/and3b -I ./google130nm/sky130_fd_sc_hd/latest/cells/and4 -I ./google130nm/sky130_fd_sc_hd/latest/cells/and4b -I ./google130nm/sky130_fd_sc_hd/latest/cells/and4bb -I ./google130nm/sky130_fd_sc_hd/latest/cells/a.py -I ./google130nm/sky130_fd_sc_hd/latest/cells/buf -I ./google130nm/sky130_fd_sc_hd/latest/cells/bufbuf -I ./google130nm/sky130_fd_sc_hd/latest/cells/bufinv -I ./google130nm/sky130_fd_sc_hd/latest/cells/clkbuf -I ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s15 -I ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s18 -I ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s25 -I ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s50 -I ./google130nm/sky130_fd_sc_hd/latest/cells/clkinv -I ./google130nm/sky130_fd_sc_hd/latest/cells/clkinvlp -I ./google130nm/sky130_fd_sc_hd/latest/cells/conb -I ./google130nm/sky130_fd_sc_hd/latest/cells/decap -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfbbn -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfbbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfrbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfrtn -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfrtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfsbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfstp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfxbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dfxtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/diode -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlclkp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlrbn -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlrbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtn -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlxbn -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlxbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlxtn -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlxtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlygate4sd1 -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlygate4sd2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlygate4sd3 -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlymetal6s2s -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlymetal6s4s -I ./google130nm/sky130_fd_sc_hd/latest/cells/dlymetal6s6s -I ./google130nm/sky130_fd_sc_hd/latest/cells/ebufn -I ./google130nm/sky130_fd_sc_hd/latest/cells/edfxbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/edfxtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/einvn -I ./google130nm/sky130_fd_sc_hd/latest/cells/einvp -I ./google130nm/sky130_fd_sc_hd/latest/cells/fa -I ./google130nm/sky130_fd_sc_hd/latest/cells/fah -I ./google130nm/sky130_fd_sc_hd/latest/cells/fahcin -I ./google130nm/sky130_fd_sc_hd/latest/cells/fahcon -I ./google130nm/sky130_fd_sc_hd/latest/cells/fill -I ./google130nm/sky130_fd_sc_hd/latest/cells/ha -I ./google130nm/sky130_fd_sc_hd/latest/cells/inv -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_bleeder -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkbufkapwr -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkinvkapwr -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_decapkapwr -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso0n -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso0p -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso1n -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso1p -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputisolatch -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrc -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrckapwr -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_hl_isowell_tap -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_isowell -I ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_isowell_tap -I ./google130nm/sky130_fd_sc_hd/latest/cells/macro_sparecell -I ./google130nm/sky130_fd_sc_hd/latest/cells/maj3 -I ./google130nm/sky130_fd_sc_hd/latest/cells/mux2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/mux2i -I ./google130nm/sky130_fd_sc_hd/latest/cells/mux4 -I ./google130nm/sky130_fd_sc_hd/latest/cells/nand2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/nand2b -I ./google130nm/sky130_fd_sc_hd/latest/cells/nand3 -I ./google130nm/sky130_fd_sc_hd/latest/cells/nand3b -I ./google130nm/sky130_fd_sc_hd/latest/cells/nand4 -I ./google130nm/sky130_fd_sc_hd/latest/cells/nand4b -I ./google130nm/sky130_fd_sc_hd/latest/cells/nand4bb -I ./google130nm/sky130_fd_sc_hd/latest/cells/nor2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/nor2b -I ./google130nm/sky130_fd_sc_hd/latest/cells/nor3 -I ./google130nm/sky130_fd_sc_hd/latest/cells/nor3b -I ./google130nm/sky130_fd_sc_hd/latest/cells/nor4 -I ./google130nm/sky130_fd_sc_hd/latest/cells/nor4b -I ./google130nm/sky130_fd_sc_hd/latest/cells/nor4bb -I ./google130nm/sky130_fd_sc_hd/latest/cells/o2111a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o2111ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o211a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o211ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o21a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o21ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o21ba -I ./google130nm/sky130_fd_sc_hd/latest/cells/o21bai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o221a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o221ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o22a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o22ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o311a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o311ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o31a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o31ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o32a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o32ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/o41a -I ./google130nm/sky130_fd_sc_hd/latest/cells/o41ai -I ./google130nm/sky130_fd_sc_hd/latest/cells/or2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/or2b -I ./google130nm/sky130_fd_sc_hd/latest/cells/or3 -I ./google130nm/sky130_fd_sc_hd/latest/cells/or3b -I ./google130nm/sky130_fd_sc_hd/latest/cells/or4 -I ./google130nm/sky130_fd_sc_hd/latest/cells/or4b -I ./google130nm/sky130_fd_sc_hd/latest/cells/or4bb -I ./google130nm/sky130_fd_sc_hd/latest/cells/probec_p -I ./google130nm/sky130_fd_sc_hd/latest/cells/probe_p -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfbbn -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfbbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrtn -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfsbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfstp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfxbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdfxtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sdlclkp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sedfxbp -I ./google130nm/sky130_fd_sc_hd/latest/cells/sedfxtp -I ./google130nm/sky130_fd_sc_hd/latest/cells/tap -I ./google130nm/sky130_fd_sc_hd/latest/cells/tapvgnd -I ./google130nm/sky130_fd_sc_hd/latest/cells/tapvgnd2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/tapvpwrvgnd -I ./google130nm/sky130_fd_sc_hd/latest/cells/xnor2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/xnor3 -I ./google130nm/sky130_fd_sc_hd/latest/cells/xor2 -I ./google130nm/sky130_fd_sc_hd/latest/cells/xor3 \\
# -I ./google130nm/sky130_fd_sc_hd/latest/models/seperate_folders.py -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_nsr -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_nsr_pp_pg_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_p -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_p_pp_pg_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_pr -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_pr_pp_pg_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_ps -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dff_ps_pp_pg_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dlatch_lp -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dlatch_lp_pp_pg_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dlatch_p -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dlatch_p_pp_pg_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dlatch_pr -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_dlatch_pr_pp_pg_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_mux_2to1 -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_mux_2to1_n -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_mux_4to2 -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_pwrgood_l_pp_g -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_pwrgood_l_pp_pg -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_pwrgood_l_pp_pg_s -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_pwrgood_pp_g -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_pwrgood_pp_p -I ./google130nm/sky130_fd_sc_hd/latest/models/udp_pwrgood_pp_pg \\
# ./google130nm/sky130_fd_sc_hd/latest/cells/a2111o/sky130_fd_sc_hd__a2111o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2111o/sky130_fd_sc_hd__a2111o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2111o/sky130_fd_sc_hd__a2111o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2111oi/sky130_fd_sc_hd__a2111oi_0.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2111oi/sky130_fd_sc_hd__a2111oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2111oi/sky130_fd_sc_hd__a2111oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2111oi/sky130_fd_sc_hd__a2111oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a211o/sky130_fd_sc_hd__a211o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a211o/sky130_fd_sc_hd__a211o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a211o/sky130_fd_sc_hd__a211o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a211oi/sky130_fd_sc_hd__a211oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a211oi/sky130_fd_sc_hd__a211oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a211oi/sky130_fd_sc_hd__a211oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21bo/sky130_fd_sc_hd__a21bo_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21bo/sky130_fd_sc_hd__a21bo_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21bo/sky130_fd_sc_hd__a21bo_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21boi/sky130_fd_sc_hd__a21boi_0.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21boi/sky130_fd_sc_hd__a21boi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21boi/sky130_fd_sc_hd__a21boi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21boi/sky130_fd_sc_hd__a21boi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21o/sky130_fd_sc_hd__a21o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21o/sky130_fd_sc_hd__a21o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21o/sky130_fd_sc_hd__a21o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21oi/sky130_fd_sc_hd__a21oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21oi/sky130_fd_sc_hd__a21oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a21oi/sky130_fd_sc_hd__a21oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a221o/sky130_fd_sc_hd__a221o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a221o/sky130_fd_sc_hd__a221o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a221o/sky130_fd_sc_hd__a221o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a221oi/sky130_fd_sc_hd__a221oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a221oi/sky130_fd_sc_hd__a221oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a221oi/sky130_fd_sc_hd__a221oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a222oi/sky130_fd_sc_hd__a222oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a22o/sky130_fd_sc_hd__a22o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a22o/sky130_fd_sc_hd__a22o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a22o/sky130_fd_sc_hd__a22o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a22oi/sky130_fd_sc_hd__a22oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a22oi/sky130_fd_sc_hd__a22oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a22oi/sky130_fd_sc_hd__a22oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2o/sky130_fd_sc_hd__a2bb2o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2o/sky130_fd_sc_hd__a2bb2o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2o/sky130_fd_sc_hd__a2bb2o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2oi/sky130_fd_sc_hd__a2bb2oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2oi/sky130_fd_sc_hd__a2bb2oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a2bb2oi/sky130_fd_sc_hd__a2bb2oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a311o/sky130_fd_sc_hd__a311o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a311o/sky130_fd_sc_hd__a311o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a311o/sky130_fd_sc_hd__a311o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a311oi/sky130_fd_sc_hd__a311oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a311oi/sky130_fd_sc_hd__a311oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a311oi/sky130_fd_sc_hd__a311oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a31o/sky130_fd_sc_hd__a31o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a31o/sky130_fd_sc_hd__a31o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a31o/sky130_fd_sc_hd__a31o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a31oi/sky130_fd_sc_hd__a31oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a31oi/sky130_fd_sc_hd__a31oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a31oi/sky130_fd_sc_hd__a31oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a32o/sky130_fd_sc_hd__a32o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a32o/sky130_fd_sc_hd__a32o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a32o/sky130_fd_sc_hd__a32o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a32oi/sky130_fd_sc_hd__a32oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a32oi/sky130_fd_sc_hd__a32oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a32oi/sky130_fd_sc_hd__a32oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a41o/sky130_fd_sc_hd__a41o_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a41o/sky130_fd_sc_hd__a41o_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a41o/sky130_fd_sc_hd__a41o_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/a41oi/sky130_fd_sc_hd__a41oi_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/a41oi/sky130_fd_sc_hd__a41oi_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/a41oi/sky130_fd_sc_hd__a41oi_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/and2/sky130_fd_sc_hd__and2_0.v ./google130nm/sky130_fd_sc_hd/latest/cells/and2/sky130_fd_sc_hd__and2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/and2/sky130_fd_sc_hd__and2_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/and2/sky130_fd_sc_hd__and2_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/and2b/sky130_fd_sc_hd__and2b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/and2b/sky130_fd_sc_hd__and2b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/and2b/sky130_fd_sc_hd__and2b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/and3/sky130_fd_sc_hd__and3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/and3/sky130_fd_sc_hd__and3_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/and3/sky130_fd_sc_hd__and3_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/and3b/sky130_fd_sc_hd__and3b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/and3b/sky130_fd_sc_hd__and3b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/and3b/sky130_fd_sc_hd__and3b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4/sky130_fd_sc_hd__and4_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4/sky130_fd_sc_hd__and4_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4/sky130_fd_sc_hd__and4_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4b/sky130_fd_sc_hd__and4b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4b/sky130_fd_sc_hd__and4b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4b/sky130_fd_sc_hd__and4b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4bb/sky130_fd_sc_hd__and4bb_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4bb/sky130_fd_sc_hd__and4bb_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/and4bb/sky130_fd_sc_hd__and4bb_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/buf/sky130_fd_sc_hd__buf_12.v ./google130nm/sky130_fd_sc_hd/latest/cells/buf/sky130_fd_sc_hd__buf_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/buf/sky130_fd_sc_hd__buf_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/buf/sky130_fd_sc_hd__buf_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/buf/sky130_fd_sc_hd__buf_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/buf/sky130_fd_sc_hd__buf_6.v ./google130nm/sky130_fd_sc_hd/latest/cells/buf/sky130_fd_sc_hd__buf_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/bufbuf/sky130_fd_sc_hd__bufbuf_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/bufbuf/sky130_fd_sc_hd__bufbuf_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/bufinv/sky130_fd_sc_hd__bufinv_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/bufinv/sky130_fd_sc_hd__bufinv_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkbuf/sky130_fd_sc_hd__clkbuf_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkbuf/sky130_fd_sc_hd__clkbuf_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkbuf/sky130_fd_sc_hd__clkbuf_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkbuf/sky130_fd_sc_hd__clkbuf_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkbuf/sky130_fd_sc_hd__clkbuf_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s15/sky130_fd_sc_hd__clkdlybuf4s15_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s15/sky130_fd_sc_hd__clkdlybuf4s15_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s18/sky130_fd_sc_hd__clkdlybuf4s18_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s18/sky130_fd_sc_hd__clkdlybuf4s18_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s25/sky130_fd_sc_hd__clkdlybuf4s25_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s25/sky130_fd_sc_hd__clkdlybuf4s25_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s50/sky130_fd_sc_hd__clkdlybuf4s50_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkdlybuf4s50/sky130_fd_sc_hd__clkdlybuf4s50_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkinv/sky130_fd_sc_hd__clkinv_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkinv/sky130_fd_sc_hd__clkinv_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkinv/sky130_fd_sc_hd__clkinv_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkinv/sky130_fd_sc_hd__clkinv_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkinv/sky130_fd_sc_hd__clkinv_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkinvlp/sky130_fd_sc_hd__clkinvlp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/clkinvlp/sky130_fd_sc_hd__clkinvlp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/conb/sky130_fd_sc_hd__conb_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/decap/sky130_fd_sc_hd__decap_12.v ./google130nm/sky130_fd_sc_hd/latest/cells/decap/sky130_fd_sc_hd__decap_3.v ./google130nm/sky130_fd_sc_hd/latest/cells/decap/sky130_fd_sc_hd__decap_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/decap/sky130_fd_sc_hd__decap_6.v ./google130nm/sky130_fd_sc_hd/latest/cells/decap/sky130_fd_sc_hd__decap_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfbbn/sky130_fd_sc_hd__dfbbn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfbbn/sky130_fd_sc_hd__dfbbn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfbbp/sky130_fd_sc_hd__dfbbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfrbp/sky130_fd_sc_hd__dfrbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfrbp/sky130_fd_sc_hd__dfrbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfrtn/sky130_fd_sc_hd__dfrtn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfrtp/sky130_fd_sc_hd__dfrtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfrtp/sky130_fd_sc_hd__dfrtp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfrtp/sky130_fd_sc_hd__dfrtp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfsbp/sky130_fd_sc_hd__dfsbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfsbp/sky130_fd_sc_hd__dfsbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfstp/sky130_fd_sc_hd__dfstp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfstp/sky130_fd_sc_hd__dfstp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfstp/sky130_fd_sc_hd__dfstp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfxbp/sky130_fd_sc_hd__dfxbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfxbp/sky130_fd_sc_hd__dfxbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfxtp/sky130_fd_sc_hd__dfxtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfxtp/sky130_fd_sc_hd__dfxtp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dfxtp/sky130_fd_sc_hd__dfxtp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/diode/sky130_fd_sc_hd__diode_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlclkp/sky130_fd_sc_hd__dlclkp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlclkp/sky130_fd_sc_hd__dlclkp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlclkp/sky130_fd_sc_hd__dlclkp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrbn/sky130_fd_sc_hd__dlrbn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrbn/sky130_fd_sc_hd__dlrbn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrbp/sky130_fd_sc_hd__dlrbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrbp/sky130_fd_sc_hd__dlrbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtn/sky130_fd_sc_hd__dlrtn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtn/sky130_fd_sc_hd__dlrtn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtn/sky130_fd_sc_hd__dlrtn_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtp/sky130_fd_sc_hd__dlrtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtp/sky130_fd_sc_hd__dlrtp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlrtp/sky130_fd_sc_hd__dlrtp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlxbn/sky130_fd_sc_hd__dlxbn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlxbn/sky130_fd_sc_hd__dlxbn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlxbp/sky130_fd_sc_hd__dlxbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlxtn/sky130_fd_sc_hd__dlxtn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlxtn/sky130_fd_sc_hd__dlxtn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlxtn/sky130_fd_sc_hd__dlxtn_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlxtp/sky130_fd_sc_hd__dlxtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlygate4sd1/sky130_fd_sc_hd__dlygate4sd1_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlygate4sd2/sky130_fd_sc_hd__dlygate4sd2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlygate4sd3/sky130_fd_sc_hd__dlygate4sd3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlymetal6s2s/sky130_fd_sc_hd__dlymetal6s2s_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlymetal6s4s/sky130_fd_sc_hd__dlymetal6s4s_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/dlymetal6s6s/sky130_fd_sc_hd__dlymetal6s6s_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/ebufn/sky130_fd_sc_hd__ebufn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/ebufn/sky130_fd_sc_hd__ebufn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/ebufn/sky130_fd_sc_hd__ebufn_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/ebufn/sky130_fd_sc_hd__ebufn_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/edfxbp/sky130_fd_sc_hd__edfxbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/edfxtp/sky130_fd_sc_hd__edfxtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvn/sky130_fd_sc_hd__einvn_0.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvn/sky130_fd_sc_hd__einvn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvn/sky130_fd_sc_hd__einvn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvn/sky130_fd_sc_hd__einvn_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvn/sky130_fd_sc_hd__einvn_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvp/sky130_fd_sc_hd__einvp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvp/sky130_fd_sc_hd__einvp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvp/sky130_fd_sc_hd__einvp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/einvp/sky130_fd_sc_hd__einvp_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/fa/sky130_fd_sc_hd__fa_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/fa/sky130_fd_sc_hd__fa_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/fa/sky130_fd_sc_hd__fa_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/fah/sky130_fd_sc_hd__fah_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/fahcin/sky130_fd_sc_hd__fahcin_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/fahcon/sky130_fd_sc_hd__fahcon_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/fill/sky130_fd_sc_hd__fill_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/fill/sky130_fd_sc_hd__fill_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/fill/sky130_fd_sc_hd__fill_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/fill/sky130_fd_sc_hd__fill_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/ha/sky130_fd_sc_hd__ha_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/ha/sky130_fd_sc_hd__ha_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/ha/sky130_fd_sc_hd__ha_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/inv/sky130_fd_sc_hd__inv_12.v ./google130nm/sky130_fd_sc_hd/latest/cells/inv/sky130_fd_sc_hd__inv_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/inv/sky130_fd_sc_hd__inv_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/inv/sky130_fd_sc_hd__inv_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/inv/sky130_fd_sc_hd__inv_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/inv/sky130_fd_sc_hd__inv_6.v ./google130nm/sky130_fd_sc_hd/latest/cells/inv/sky130_fd_sc_hd__inv_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_bleeder/sky130_fd_sc_hd__lpflow_bleeder_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkbufkapwr/sky130_fd_sc_hd__lpflow_clkbufkapwr_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkbufkapwr/sky130_fd_sc_hd__lpflow_clkbufkapwr_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkbufkapwr/sky130_fd_sc_hd__lpflow_clkbufkapwr_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkbufkapwr/sky130_fd_sc_hd__lpflow_clkbufkapwr_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkbufkapwr/sky130_fd_sc_hd__lpflow_clkbufkapwr_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkinvkapwr/sky130_fd_sc_hd__lpflow_clkinvkapwr_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkinvkapwr/sky130_fd_sc_hd__lpflow_clkinvkapwr_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkinvkapwr/sky130_fd_sc_hd__lpflow_clkinvkapwr_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkinvkapwr/sky130_fd_sc_hd__lpflow_clkinvkapwr_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_clkinvkapwr/sky130_fd_sc_hd__lpflow_clkinvkapwr_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_decapkapwr/sky130_fd_sc_hd__lpflow_decapkapwr_12.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_decapkapwr/sky130_fd_sc_hd__lpflow_decapkapwr_3.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_decapkapwr/sky130_fd_sc_hd__lpflow_decapkapwr_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_decapkapwr/sky130_fd_sc_hd__lpflow_decapkapwr_6.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_decapkapwr/sky130_fd_sc_hd__lpflow_decapkapwr_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso0n/sky130_fd_sc_hd__lpflow_inputiso0n_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso0p/sky130_fd_sc_hd__lpflow_inputiso0p_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso1n/sky130_fd_sc_hd__lpflow_inputiso1n_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputiso1p/sky130_fd_sc_hd__lpflow_inputiso1p_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_inputisolatch/sky130_fd_sc_hd__lpflow_inputisolatch_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrc/sky130_fd_sc_hd__lpflow_isobufsrc_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrc/sky130_fd_sc_hd__lpflow_isobufsrc_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrc/sky130_fd_sc_hd__lpflow_isobufsrc_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrc/sky130_fd_sc_hd__lpflow_isobufsrc_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrc/sky130_fd_sc_hd__lpflow_isobufsrc_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_isobufsrckapwr/sky130_fd_sc_hd__lpflow_isobufsrckapwr_16.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_hl_isowell_tap/sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_hl_isowell_tap/sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_hl_isowell_tap/sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_isowell/sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_isowell_tap/sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_tap_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_isowell_tap/sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_tap_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/lpflow_lsbuf_lh_isowell_tap/sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_tap_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/maj3/sky130_fd_sc_hd__maj3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/maj3/sky130_fd_sc_hd__maj3_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/maj3/sky130_fd_sc_hd__maj3_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux2/sky130_fd_sc_hd__mux2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux2/sky130_fd_sc_hd__mux2_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux2/sky130_fd_sc_hd__mux2_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux2/sky130_fd_sc_hd__mux2_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux2i/sky130_fd_sc_hd__mux2i_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux2i/sky130_fd_sc_hd__mux2i_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux2i/sky130_fd_sc_hd__mux2i_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux4/sky130_fd_sc_hd__mux4_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux4/sky130_fd_sc_hd__mux4_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/mux4/sky130_fd_sc_hd__mux4_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand2/sky130_fd_sc_hd__nand2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand2/sky130_fd_sc_hd__nand2_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand2/sky130_fd_sc_hd__nand2_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand2/sky130_fd_sc_hd__nand2_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand2b/sky130_fd_sc_hd__nand2b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand2b/sky130_fd_sc_hd__nand2b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand2b/sky130_fd_sc_hd__nand2b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand3/sky130_fd_sc_hd__nand3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand3/sky130_fd_sc_hd__nand3_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand3/sky130_fd_sc_hd__nand3_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand3b/sky130_fd_sc_hd__nand3b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand3b/sky130_fd_sc_hd__nand3b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand3b/sky130_fd_sc_hd__nand3b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4/sky130_fd_sc_hd__nand4_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4/sky130_fd_sc_hd__nand4_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4/sky130_fd_sc_hd__nand4_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4b/sky130_fd_sc_hd__nand4b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4b/sky130_fd_sc_hd__nand4b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4b/sky130_fd_sc_hd__nand4b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4bb/sky130_fd_sc_hd__nand4bb_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4bb/sky130_fd_sc_hd__nand4bb_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nand4bb/sky130_fd_sc_hd__nand4bb_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor2/sky130_fd_sc_hd__nor2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor2/sky130_fd_sc_hd__nor2_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor2/sky130_fd_sc_hd__nor2_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor2/sky130_fd_sc_hd__nor2_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor2b/sky130_fd_sc_hd__nor2b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor2b/sky130_fd_sc_hd__nor2b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor2b/sky130_fd_sc_hd__nor2b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor3/sky130_fd_sc_hd__nor3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor3/sky130_fd_sc_hd__nor3_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor3/sky130_fd_sc_hd__nor3_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor3b/sky130_fd_sc_hd__nor3b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor3b/sky130_fd_sc_hd__nor3b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor3b/sky130_fd_sc_hd__nor3b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4/sky130_fd_sc_hd__nor4_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4/sky130_fd_sc_hd__nor4_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4/sky130_fd_sc_hd__nor4_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4b/sky130_fd_sc_hd__nor4b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4b/sky130_fd_sc_hd__nor4b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4b/sky130_fd_sc_hd__nor4b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4bb/sky130_fd_sc_hd__nor4bb_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4bb/sky130_fd_sc_hd__nor4bb_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/nor4bb/sky130_fd_sc_hd__nor4bb_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2111a/sky130_fd_sc_hd__o2111a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2111a/sky130_fd_sc_hd__o2111a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2111a/sky130_fd_sc_hd__o2111a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2111ai/sky130_fd_sc_hd__o2111ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2111ai/sky130_fd_sc_hd__o2111ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2111ai/sky130_fd_sc_hd__o2111ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o211a/sky130_fd_sc_hd__o211a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o211a/sky130_fd_sc_hd__o211a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o211a/sky130_fd_sc_hd__o211a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o211ai/sky130_fd_sc_hd__o211ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o211ai/sky130_fd_sc_hd__o211ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o211ai/sky130_fd_sc_hd__o211ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21a/sky130_fd_sc_hd__o21a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21a/sky130_fd_sc_hd__o21a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21a/sky130_fd_sc_hd__o21a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21ai/sky130_fd_sc_hd__o21ai_0.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21ai/sky130_fd_sc_hd__o21ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21ai/sky130_fd_sc_hd__o21ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21ai/sky130_fd_sc_hd__o21ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21ba/sky130_fd_sc_hd__o21ba_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21ba/sky130_fd_sc_hd__o21ba_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21ba/sky130_fd_sc_hd__o21ba_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21bai/sky130_fd_sc_hd__o21bai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21bai/sky130_fd_sc_hd__o21bai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o21bai/sky130_fd_sc_hd__o21bai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o221a/sky130_fd_sc_hd__o221a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o221a/sky130_fd_sc_hd__o221a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o221a/sky130_fd_sc_hd__o221a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o221ai/sky130_fd_sc_hd__o221ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o221ai/sky130_fd_sc_hd__o221ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o221ai/sky130_fd_sc_hd__o221ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o22a/sky130_fd_sc_hd__o22a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o22a/sky130_fd_sc_hd__o22a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o22a/sky130_fd_sc_hd__o22a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o22ai/sky130_fd_sc_hd__o22ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o22ai/sky130_fd_sc_hd__o22ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o22ai/sky130_fd_sc_hd__o22ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2a/sky130_fd_sc_hd__o2bb2a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2a/sky130_fd_sc_hd__o2bb2a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2a/sky130_fd_sc_hd__o2bb2a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2ai/sky130_fd_sc_hd__o2bb2ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2ai/sky130_fd_sc_hd__o2bb2ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o2bb2ai/sky130_fd_sc_hd__o2bb2ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o311a/sky130_fd_sc_hd__o311a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o311a/sky130_fd_sc_hd__o311a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o311a/sky130_fd_sc_hd__o311a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o311ai/sky130_fd_sc_hd__o311ai_0.v ./google130nm/sky130_fd_sc_hd/latest/cells/o311ai/sky130_fd_sc_hd__o311ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o311ai/sky130_fd_sc_hd__o311ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o311ai/sky130_fd_sc_hd__o311ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o31a/sky130_fd_sc_hd__o31a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o31a/sky130_fd_sc_hd__o31a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o31a/sky130_fd_sc_hd__o31a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o31ai/sky130_fd_sc_hd__o31ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o31ai/sky130_fd_sc_hd__o31ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o31ai/sky130_fd_sc_hd__o31ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o32a/sky130_fd_sc_hd__o32a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o32a/sky130_fd_sc_hd__o32a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o32a/sky130_fd_sc_hd__o32a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o32ai/sky130_fd_sc_hd__o32ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o32ai/sky130_fd_sc_hd__o32ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o32ai/sky130_fd_sc_hd__o32ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o41a/sky130_fd_sc_hd__o41a_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o41a/sky130_fd_sc_hd__o41a_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o41a/sky130_fd_sc_hd__o41a_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/o41ai/sky130_fd_sc_hd__o41ai_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/o41ai/sky130_fd_sc_hd__o41ai_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/o41ai/sky130_fd_sc_hd__o41ai_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/or2/sky130_fd_sc_hd__or2_0.v ./google130nm/sky130_fd_sc_hd/latest/cells/or2/sky130_fd_sc_hd__or2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/or2/sky130_fd_sc_hd__or2_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/or2/sky130_fd_sc_hd__or2_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/or2b/sky130_fd_sc_hd__or2b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/or2b/sky130_fd_sc_hd__or2b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/or2b/sky130_fd_sc_hd__or2b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/or3/sky130_fd_sc_hd__or3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/or3/sky130_fd_sc_hd__or3_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/or3/sky130_fd_sc_hd__or3_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/or3b/sky130_fd_sc_hd__or3b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/or3b/sky130_fd_sc_hd__or3b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/or3b/sky130_fd_sc_hd__or3b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4/sky130_fd_sc_hd__or4_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4/sky130_fd_sc_hd__or4_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4/sky130_fd_sc_hd__or4_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4b/sky130_fd_sc_hd__or4b_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4b/sky130_fd_sc_hd__or4b_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4b/sky130_fd_sc_hd__or4b_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4bb/sky130_fd_sc_hd__or4bb_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4bb/sky130_fd_sc_hd__or4bb_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/or4bb/sky130_fd_sc_hd__or4bb_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/probec_p/sky130_fd_sc_hd__probec_p_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/probe_p/sky130_fd_sc_hd__probe_p_8.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfbbn/sky130_fd_sc_hd__sdfbbn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfbbn/sky130_fd_sc_hd__sdfbbn_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfbbp/sky130_fd_sc_hd__sdfbbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrbp/sky130_fd_sc_hd__sdfrbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrbp/sky130_fd_sc_hd__sdfrbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrtn/sky130_fd_sc_hd__sdfrtn_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrtp/sky130_fd_sc_hd__sdfrtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrtp/sky130_fd_sc_hd__sdfrtp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfrtp/sky130_fd_sc_hd__sdfrtp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfsbp/sky130_fd_sc_hd__sdfsbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfsbp/sky130_fd_sc_hd__sdfsbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfstp/sky130_fd_sc_hd__sdfstp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfstp/sky130_fd_sc_hd__sdfstp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfstp/sky130_fd_sc_hd__sdfstp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfxbp/sky130_fd_sc_hd__sdfxbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfxbp/sky130_fd_sc_hd__sdfxbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfxtp/sky130_fd_sc_hd__sdfxtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfxtp/sky130_fd_sc_hd__sdfxtp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdfxtp/sky130_fd_sc_hd__sdfxtp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdlclkp/sky130_fd_sc_hd__sdlclkp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdlclkp/sky130_fd_sc_hd__sdlclkp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sdlclkp/sky130_fd_sc_hd__sdlclkp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/sedfxbp/sky130_fd_sc_hd__sedfxbp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sedfxbp/sky130_fd_sc_hd__sedfxbp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sedfxtp/sky130_fd_sc_hd__sedfxtp_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/sedfxtp/sky130_fd_sc_hd__sedfxtp_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/sedfxtp/sky130_fd_sc_hd__sedfxtp_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/tap/sky130_fd_sc_hd__tap_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/tap/sky130_fd_sc_hd__tap_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/tapvgnd/sky130_fd_sc_hd__tapvgnd_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/tapvgnd2/sky130_fd_sc_hd__tapvgnd2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/tapvpwrvgnd/sky130_fd_sc_hd__tapvpwrvgnd_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/xnor2/sky130_fd_sc_hd__xnor2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/xnor2/sky130_fd_sc_hd__xnor2_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/xnor2/sky130_fd_sc_hd__xnor2_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/xnor3/sky130_fd_sc_hd__xnor3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/xnor3/sky130_fd_sc_hd__xnor3_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/xnor3/sky130_fd_sc_hd__xnor3_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/xor2/sky130_fd_sc_hd__xor2_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/xor2/sky130_fd_sc_hd__xor2_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/xor2/sky130_fd_sc_hd__xor2_4.v ./google130nm/sky130_fd_sc_hd/latest/cells/xor3/sky130_fd_sc_hd__xor3_1.v ./google130nm/sky130_fd_sc_hd/latest/cells/xor3/sky130_fd_sc_hd__xor3_2.v ./google130nm/sky130_fd_sc_hd/latest/cells/xor3/sky130_fd_sc_hd__xor3_4.v \\
# {yosys_verilog_path} {testbench_path} \\
# -s testbench \\
# -D 'DUMP_FILE_NAME="{vcd_path}"' \\
# -o {simulation_program_path}
# """.strip()

#     completed_iverilog = subprocess.run(
#         [iverilog_command],
#         capture_output=True,
#         shell=True,
#     )
#     log += completed_iverilog.stdout.decode("utf-8")
#     if completed_iverilog.returncode != 0:
#         raise HTTPException(
#             status_code=400,
#             detail=ServiceError(
#                 error=f"run iverilog failed\n{completed_iverilog.stderr.decode('utf-8')}",
#                 log=log,
#             ).json(),
#         )

#     # [vvp跑仿真]

#     completed_vvp = subprocess.run(
#         [f"vvp {simulation_program_path}"],
#         capture_output=True,
#         shell=True,
#     )
#     log += completed_vvp.stdout.decode("utf-8")
#     if completed_vvp.returncode != 0:
#         raise HTTPException(
#             status_code=400,
#             detail=ServiceError(
#                 error=f"run vvp failed\n{completed_vvp.stderr.decode('utf-8')}",
#                 log=log,
#             ).json(),
#         )




    return ServiceResponse(
        log=log,
        resources_report=resources_report,
        circuit_svg=circuit_svg_content,
        circuit_netlistsvg=circuit_netlistsvg_content,
        sta_report=sta_report,
        simulation_wavejson="TODO 用iverilog和vvp 跑 Google130nm的.v、yosys生成的.v、sta生成的sdf 拿到仿真结果",
    )
