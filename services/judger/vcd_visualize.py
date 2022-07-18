#!/usr/bin/env python3
import sys


def main():
    from pyDigitalWaveTools.vcd.parser import VcdParser
    from .wavedump import VcdConverter

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


if __name__ == "__main__":
    main()
