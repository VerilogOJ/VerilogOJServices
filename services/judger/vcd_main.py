#!/usr/bin/env python3
import sys

def main():
    from .wavedump import VcdComparator
    cmpr = VcdComparator("./temp_uuid/reference.vcd", "./temp_uuid/student.vcd", ['root/testbench/x', 'root/testbench/y']) # TODO 这里看起来是要放入信号的样子 这里testbench是testbench.v中模块的名称 之后的x和y是信号的名称
    ret, msg = cmpr.compare()
    print(msg)
    print("Ret status: {}".format(ret))
    return (ret, msg)

# if __name__ == "__main__":
#     ret, msg = main()
    
#     sys.exit(0 if ret is True else 1)
