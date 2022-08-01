"""
思路：
以netlistsvg所给的skinfile[default](https://github.com/nturley/netlistsvg/blob/master/lib/default.svg)为基础
添加[Google130nm元件](https://github.com/google/skywater-pdk)
"""

import re
import json
import xml.etree.ElementTree as ET
import os

nelistsvg_google130nm_skin_content = ""
nelistsvg_google130nm_skin_path = "./google130nm_skin.svg"
path_cells = "./skywater-pdk-netlistsvg-only/libraries/sky130_fd_sc_hd/latest/cells/"

netlistsvg_default_skin_before = """
<svg  xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:s="https://github.com/nturley/netlistsvg"
  width="800" height="500">
  <s:properties>
    <s:layoutEngine
      org.eclipse.elk.layered.spacing.nodeNodeBetweenLayers="35"
      org.eclipse.elk.spacing.nodeNode= "35"
      org.eclipse.elk.layered.layering.strategy= "LONGEST_PATH"
    />
    <s:low_priority_alias val="$dff" />
  </s:properties>
<style>
svg {
  stroke:#000;
  fill:none;
}
text {
  fill:#000;
  stroke:none;
  font-size:10px;
  font-weight: bold;
  font-family: "Courier New", monospace;
}
line {
    stroke-linecap: round;
}
.nodelabel {
  text-anchor: middle;
}
.inputPortLabel {
  text-anchor: end;
}
.splitjoinBody {
  fill:#000;
}
</style>
"""

netlistsvg_default_skin_after = """
<g s:type="mux" transform="translate(50, 50)" s:width="20" s:height="40">
    <s:alias val="$pmux"/>
    <s:alias val="$mux"/>
    <s:alias val="$_MUX_"/>

    <path d="M0,0 L20,10 L20,30 L0,40 Z" class="$cell_id"/>

    <text x="5" y="32" class="nodelabel $cell_id" s:attribute="">1</text>
    <text x="5" y="13" class="nodelabel $cell_id" s:attribute="">0</text>
    <g s:x="0" s:y="10" s:pid="A"/>
    <g s:x="0" s:y="30" s:pid="B"/>
    <g s:x="10" s:y="35" s:pid="S"/>
    <g s:x="20" s:y="20" s:pid="Y"/>
  </g>

  <g s:type="mux-bus" transform="translate(100, 50)" s:width="24" s:height="40">
    <s:alias val="$pmux-bus"/>
    <s:alias val="$mux-bus"/>
    <s:alias val="$_MUX_-bus"/>

    <path d="M0,0 L20,10 L20,30 L0,40 Z" class="$cell_id"/>
    <path d="M4,2 L4,0 L22,9 L22,31 L4,40 L4,38" class="$cell_id"/>
    <path d="M8,2 L8,0 L24,8 L24,32 L8,40 L8,38" class="$cell_id"/>

    <text x="5" y="32" class="nodelabel $cell_id" s:attribute="">1</text>
    <text x="5" y="13" class="nodelabel $cell_id" s:attribute="">0</text>
    <g s:x="-1" s:y="10" s:pid="A"/>
    <g s:x="-1" s:y="30" s:pid="B"/>
    <g s:x="12" s:y="38" s:pid="S"/>
    <g s:x="24.5" s:y="20" s:pid="Y"/>
  </g>

  <!-- and -->
  <g s:type="and" transform="translate(150,50)" s:width="30" s:height="25">
    <s:alias val="$and"/>
    <s:alias val="$logic_and"/>
    <s:alias val="$_AND_"/>
    <s:alias val="$reduce_and"/>

    <path d="M0,0 L0,25 L15,25 A15 12.5 0 0 0 15,0 Z" class="$cell_id"/>

    <g s:x="0" s:y="5" s:pid="A"/>
    <g s:x="0" s:y="20" s:pid="B"/>
    <g s:x="30" s:y="12.5" s:pid="Y"/>
  </g>
  <g s:type="nand" transform="translate(150,100)" s:width="30" s:height="25">
    <s:alias val="$nand"/>
    <s:alias val="$logic_nand"/>
    <s:alias val="$_NAND_"/>
    <s:alias val="$_ANDNOT_"/>

    <path d="M0,0 L0,25 L15,25 A15 12.5 0 0 0 15,0 Z" class="$cell_id"/>
    <circle cx="34" cy="12.5" r="3" class="$cell_id"/>

    <g s:x="0" s:y="5" s:pid="A"/>
    <g s:x="0" s:y="20" s:pid="B"/>
    <g s:x="36" s:y="12.5" s:pid="Y"/>
  </g>
  <g s:type="andnot" transform="translate(200,50)" s:width="30" s:height="25">
    <s:alias val="$_ANDNOT_"/>

    <path d="M0,0 L0,25 L15,25 A15 12.5 0 0 0 15,0 Z" class="$cell_id"/>
    <circle cx="-3" cy="20" r="3"/>

    <g s:x="0" s:y="5" s:pid="A"/>
    <g s:x="-6" s:y="20" s:pid="B"/>
    <!-- <path d="M -10,20 L -6,20"/> -->
    <g s:x="30" s:y="12.5" s:pid="Y"/>
  </g>

  <!-- or -->
  <g s:type="or" transform="translate(250,50)" s:width="30" s:height="25">
    <s:alias val="$or"/>
    <s:alias val="$logic_or"/>
    <s:alias val="$_OR_"/>
    <s:alias val="$reduce_or"/>
    <s:alias val="$reduce_bool"/>

    <path d="M0,0 A30 25 0 0 1 0,25 A30 25 0 0 0 30,12.5 A30 25 0 0 0 0,0" class="$cell_id"/>
 
    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="30" s:y="12.5" s:pid="Y"/>
  </g>
  <g s:type="reduce_nor" transform="translate(250, 100)" s:width="33" s:height="25">
    <s:alias val="$nor"/>
    <s:alias val="$reduce_nor"/>
    <s:alias val="$_NOR_"/>
    <s:alias val="$_ORNOT_"/>

    <path d="M0,0 A30 25 0 0 1 0,25 A30 25 0 0 0 30,12.5 A30 25 0 0 0 0,0" class="$cell_id"/>
    <circle cx="33" cy="12.5" r="3" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="36" s:y="12.5" s:pid="Y"/>
  </g>
  <g s:type="ornot" transform="translate(300,50)" s:width="30" s:height="25">
    <s:alias val="$_ORNOT_"/>

    <path d="M0,0 A30 25 0 0 1 0,25 A30 25 0 0 0 30,12.5 A30 25 0 0 0 0,0" class="$cell_id"/>
    <circle cx="-1" cy="20" r="3"/>
 
    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="-4" s:y="20" s:pid="B"/>
    <!-- <path d="M -8,20 L -4,20"/> -->
    <g s:x="30" s:y="12.5" s:pid="Y"/>
  </g>

  <!--xor -->
  <g s:type="reduce_xor" transform="translate(350, 50)" s:width="33" s:height="25">
    <s:alias val="$xor"/>
    <s:alias val="$reduce_xor"/>
    <s:alias val="$_XOR_"/>

    <path d="M3,0 A30 25 0 0 1 3,25 A30 25 0 0 0 33,12.5 A30 25 0 0 0 3,0" class="$cell_id"/>
    <path d="M0,0 A30 25 0 0 1 0,25" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="33" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="reduce_nxor" transform="translate(350, 100)" s:width="33" s:height="25">
    <s:alias val="$xnor"/>
    <s:alias val="$reduce_xnor"/>
    <s:alias val="$_XNOR_"/>

    <path d="M3,0 A30 25 0 0 1 3,25 A30 25 0 0 0 33,12.5 A30 25 0 0 0 3,0" class="$cell_id"/>
    <path d="M0,0 A30 25 0 0 1 0,25" class="$cell_id"/>
    <circle cx="36" cy="12.5" r="3" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="38" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="tribuf" transform="translate(550, 50)" s:width="15" s:height="30">
    <s:alias val="$tribuf"/>
    <s:alias val="$_TRIBUF_"/>

    <s:alias val="tribuf-bus"/>
    <s:alias val="$tribuf-bus"/>
    <s:alias val="$_TRIBUF_-bus"/>

    <path d="M0,0 L25,15 L0,30 Z" class="$cell_id"/>

    <g s:x="0" s:y="15" s:pid="A"/>
    <g s:x="11" s:y="6" s:pid="EN"/>
    <g s:x="25" s:y="15" s:pid="Y"/>
    <!-- <path d="M -5,15 L 0,15" /> -->
    <!-- <path d="M 11,0 L 11,6" /> -->
    <!-- <path d="M 30,15 L 25,15" /> -->
  </g>

  <!--buffer -->
  <g s:type="not" transform="translate(450,100)" s:width="30" s:height="20">
    <s:alias val="$_NOT_"/>
    <s:alias val="$not"/>
    <s:alias val="$logic_not"/>

    <path d="M0,0 L0,20 L20,10 Z" class="$cell_id"/>
    <circle cx="24" cy="10" r="3" class="$cell_id"/>

    <g s:x="-1" s:y="10" s:pid="A"/>
    <g s:x="27" s:y="10" s:pid="Y"/>
  </g>
  <g s:type="buf" transform="translate(450,50)" s:width="30" s:height="20">
    <s:alias val="$_BUF_"/>

    <path d="M0,0 L0,20 L20,10 Z" class="$cell_id"/>

    <g s:x="0" s:y="10" s:pid="A"/>
    <g s:x="20" s:y="10" s:pid="Y"/>
    <!-- <path d="M -5,10 L 0,10"/> -->
    <!-- <path d="M 25,10 L 20,10"/> -->
  </g>

  <g s:type="add" transform="translate(50, 150)" s:width="25" s:height="25">
    <s:alias val="$add"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="12.5" y2="12.5" class="$cell_id"/>
    <line x1="12.5" x2="12.5" y1="7.5" y2="17.5" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="26" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="pos" transform="translate(100, 150)" s:width="25" s:height="25">
    <s:alias val="$pos"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="12.5" y2="12.5" class="$cell_id"/>
    <line x1="12.5" x2="12.5" y1="7.5" y2="17.5" class="$cell_id"/>

    <g s:x="-1" s:y="12.5" s:pid="A"/>
    <g s:x="26" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="sub" transform="translate(150,150)" s:width="25" s:height="25">
    <s:alias val="$sub"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="12.5" y2="12.5" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="neg" transform="translate(200,150)" s:width="25" s:height="25">
    <s:alias val="$neg"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="12.5" y2="12.5" class="$cell_id"/>

    <g s:x="0" s:y="12.5" s:pid="A"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="eq" transform="translate(250,150)" s:width="25" s:height="25">
    <s:alias val="$eq"/>
    <s:alias val="$eqx"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="10" y2="10" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="15" y2="15" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="mul" transform="translate(300, 150)" s:width="25" s:height="25">
    <s:alias val="$mul"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="7.5"  x2="17.5" y1="7.5" y2="17.5" class="$cell_id"/>
    <line x1="17.5" x2="7.5"  y1="7.5" y2="17.5" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="26" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="div" transform="translate(350, 150)" s:width="25" s:height="25">
    <s:alias val="$div"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="15" x2="10"  y1="7.5" y2="17.5" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="26" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="mod" transform="translate(400, 150)" s:width="25" s:height="25">
    <s:alias val="$mod"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="15" x2="10"  y1="7.5" y2="17.5" class="$cell_id"/>
    <circle r="2" cx="8" cy="9" class="$cell_id"/>
    <circle r="2" cx="17" cy="16" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="26" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="pow" transform="translate(450, 150)" s:width="25" s:height="25">
    <s:alias val="$pow"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="10" x2="12.5"  y1="12" y2="6" class="$cell_id"/>
    <line x1="15" x2="12.5"  y1="12" y2="6" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="26" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="ne" transform="translate(500,150)" s:width="25" s:height="25">
    <s:alias val="$ne"/>
    <s:alias val="$nex"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="10" y2="10" class="$cell_id"/>
    <line x1="7.5" x2="17.5" y1="15" y2="15" class="$cell_id"/>
    <line x1="9" x2="16" y1="18" y2="7" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="lt" transform="translate(50,200)" s:width="25" s:height="25">
    <s:alias val="$lt"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="6" x2="17" y1="12"  y2="7" class="$cell_id"/>
    <line x1="6" x2="17" y1="12" y2="17" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="le" transform="translate(100,200)" s:width="25" s:height="25">
    <s:alias val="$le"/>

    <circle r="12.5" cx="12.5" cy="12.5" class="$cell_id"/>
    <line x1="6" x2="17" y1="11"  y2="6" class="$cell_id"/>
    <line x1="6" x2="17" y1="11" y2="16" class="$cell_id"/>
    <line x1="6" x2="17" y1="14" y2="19" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="ge" transform="translate(150,200)" s:width="25" s:height="25">
    <s:alias val="$ge"/>

    <circle r="12" cx="12" cy="12" class="$cell_id"/>
    <line x1="8" x2="19"  y1="6" y2="11" class="$cell_id"/>
    <line x1="8" x2="19" y1="16" y2="11" class="$cell_id"/>
    <line x1="8" x2="19" y1="19" y2="14" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="gt" transform="translate(200,200)" s:width="25" s:height="25">
    <s:alias val="$gt"/>

    <circle r="12" cx="12" cy="12" class="$cell_id"/>
    <line x1="8" x2="19"  y1="7" y2="12" class="$cell_id"/>
    <line x1="8" x2="19" y1="17" y2="12" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="shr" transform="translate(250,200)" s:width="25" s:height="25">
    <s:alias val="$shr"/>

    <circle r="12" cx="12" cy="12" class="$cell_id"/>
    <line x1="8" x2="13"  y1="7"  y2="12" class="$cell_id"/>
    <line x1="8" x2="13"  y1="17" y2="12" class="$cell_id"/>
    <line x1="14" x2="19" y1="7"  y2="12" class="$cell_id"/>
    <line x1="14" x2="19" y1="17" y2="12" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="shl" transform="translate(300,200)" s:width="25" s:height="25">
    <s:alias val="$shl"/>

    <circle r="12" cx="12" cy="12" class="$cell_id"/>
    <line x1="6" x2="11"  y1="12" y2="7"  class="$cell_id"/>
    <line x1="6" x2="11"  y1="12" y2="17" class="$cell_id"/>
    <line x1="12" x2="17" y1="12" y2="7"  class="$cell_id"/>
    <line x1="12" x2="17" y1="12" y2="17" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="sshr" transform="translate(350,200)" s:width="25" s:height="25">
    <s:alias val="$sshr"/>

    <circle r="12" cx="12" cy="12" class="$cell_id"/>
    <line x1="5"  x2="10" y1="7"  y2="12" class="$cell_id"/>
    <line x1="5"  x2="10" y1="17" y2="12" class="$cell_id"/>
    <line x1="11" x2="16" y1="7"  y2="12" class="$cell_id"/>
    <line x1="11" x2="16" y1="17" y2="12" class="$cell_id"/>
    <line x1="17" x2="22" y1="7"  y2="12" class="$cell_id"/>
    <line x1="17" x2="22" y1="17" y2="12" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="sshl" transform="translate(400,200)" s:width="25" s:height="25">
    <s:alias val="$sshl"/>

    <circle r="12" cx="12" cy="12" class="$cell_id"/>
    <line x1="3"  x2="8"   y1="12" y2="7"  class="$cell_id"/>
    <line x1="3"  x2="8"   y1="12" y2="17" class="$cell_id"/>
    <line x1="9"  x2="14" y1="12" y2="7"  class="$cell_id"/>
    <line x1="9"  x2="14" y1="12" y2="17" class="$cell_id"/>
    <line x1="15" x2="20" y1="12" y2="7"  class="$cell_id"/>
    <line x1="15" x2="20" y1="12" y2="17" class="$cell_id"/>

    <g s:x="2" s:y="5" s:pid="A"/>
    <g s:x="2" s:y="20" s:pid="B"/>
    <g s:x="25" s:y="12.5" s:pid="Y"/>
  </g>

  <g s:type="inputExt" transform="translate(50,250)" s:width="30" s:height="20">
    <text x="15" y="-4" class="nodelabel $cell_id" s:attribute="ref">input</text>
    <s:alias val="$_inputExt_"/>
    <path d="M0,0 L0,20 L15,20 L30,10 L15,0 Z" class="$cell_id"/>
    <g s:x="30" s:y="10" s:pid="Y"/>
  </g>

  <g s:type="constant" transform="translate(150,250)" s:width="30" s:height="20">
    <text x="15" y="-4" class="nodelabel $cell_id" s:attribute="ref">constant</text>

    <s:alias val="$_constant_"/>
    <rect width="30" height="20" class="$cell_id"/>

    <g s:x="31" s:y="10" s:pid="Y"/>
  </g>

  <g s:type="outputExt" transform="translate(250,250)" s:width="30" s:height="20">
    <text x="15" y="-4" class="nodelabel $cell_id" s:attribute="ref">output</text>
    <s:alias val="$_outputExt_"/>
    <path d="M30,0 L30,20 L15,20 L0,10 L15,0 Z" class="$cell_id"/>

    <g s:x="0" s:y="10" s:pid="A"/>
  </g>

  <g s:type="split" transform="translate(350,250)" s:width="5" s:height="40">
    <rect width="5" height="40" class="splitjoinBody" s:generic="body"/>
    <s:alias val="$_split_"/>

    <g s:x="0" s:y="20" s:pid="in"/>
    <g transform="translate(5, 10)" s:x="4" s:y="10" s:pid="out0">
      <text x="5" y="-4">hi:lo</text>
    </g>
    <g transform="translate(5, 30)" s:x="4" s:y="30" s:pid="out1">
      <text x="5" y="-4">hi:lo</text>
    </g>
  </g>

  <g s:type="join" transform="translate(450,250)" s:width="4" s:height="40">
    <rect width="5" height="40" class="splitjoinBody" s:generic="body"/>
    <s:alias val="$_join_"/>
    <g s:x="5" s:y="20"  s:pid="out"/>
    <g transform="translate(0, 10)" s:x="0" s:y="10" s:pid="in0">
      <text x="-3" y="-4" class="inputPortLabel">hi:lo</text>
    </g>
    <g transform="translate(0, 30)" s:x="0" s:y="30" s:pid="in1">
      <text x="-3" y="-4" class="inputPortLabel">hi:lo</text>
    </g>
  </g>

  <g s:type="dff" transform="translate(50,300)" s:width="30" s:height="40">
    <s:alias val="$dff"/>
    <s:alias val="$_DFF_"/>
    <s:alias val="$_DFF_P_"/>

    <s:alias val="$adff"/>
    <s:alias val="$_DFF_"/>
    <s:alias val="$_DFF_P_"/>

    <s:alias val="$sdff"/>
    <s:alias val="$_DFF_"/>
    <s:alias val="$_DFF_P_"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>
    <path d="M0,35 L5,30 L0,25" class="$cell_id"/>

    <g s:x="31" s:y="10" s:pid="Q"/>
    <g s:x="-1" s:y="30" s:pid="CLK"/>
    <g s:x="-1" s:y="30" s:pid="C"/>
    <g s:x="-1" s:y="10" s:pid="D"/>
    <g s:x="15" s:y="40" s:pid="ARST"/>
    <g s:x="15" s:y="40" s:pid="SRST"/>
  </g>

  <g s:type="dff-bus" transform="translate(100,300)" s:width="34" s:height="44">
    <s:alias val="$dff-bus"/>
    <s:alias val="$_DFF_-bus"/>
    <s:alias val="$_DFF_P_-bus"/>

    <s:alias val="adff-bus"/>
    <s:alias val="$adff-bus"/>
    <s:alias val="$_DFF_-bus"/>
    <s:alias val="$_DFF_P_-bus"/>

    <s:alias val="sdff-bus"/>
    <s:alias val="$sdff-bus"/>
    <s:alias val="$_DFF_-bus"/>
    <s:alias val="$_DFF_P_-bus"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>
    <path d="M0,35 L5,30 L0,25" class="$cell_id"/>
    <path d="M30,2 L32,2 L32,42 L2,42 L2,40" class="$cell_id"/>
    <path d="M32,4 L34,4 L34,44 L4,44 L4,42" class="$cell_id"/>

    <g s:x="35" s:y="10" s:pid="Q"/>
    <g s:x="-1" s:y="30" s:pid="CLK"/>
    <g s:x="-1" s:y="30" s:pid="C"/>
    <g s:x="-1" s:y="10" s:pid="D"/>
    <g s:x="17" s:y="44" s:pid="ARST"/>
    <g s:x="17" s:y="44" s:pid="SRST"/>
  </g>

  <g s:type="dffn" transform="translate(150,300)" s:width="30" s:height="40">
    <s:alias val="$dffn"/>
    <s:alias val="$_DFF_N_"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>
    <path d="M0,35 L5,30 L0,25" class="$cell_id"/>
    <circle cx="-3" cy="30" r="3" class="$cell_id"/>

    <g s:x="30" s:y="10" s:pid="Q"/>
    <g s:x="-6" s:y="30" s:pid="CLK"/>
    <g s:x="-6" s:y="30" s:pid="C"/>
    <g s:x="0" s:y="10" s:pid="D"/>
  </g>

  <g s:type="dffn-bus" transform="translate(200,300)" s:width="30" s:height="40">
    <s:alias val="$dffn-bus"/>
    <s:alias val="$_DFF_N_-bus"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>
    <path d="M0,35 L5,30 L0,25" class="$cell_id"/>
    <circle cx="-3" cy="30" r="3" class="$cell_id"/>
    <path d="M30,2 L32,2 L32,42 L2,42 L2,40" class="$cell_id"/>
    <path d="M32,4 L34,4 L34,44 L4,44 L4,42" class="$cell_id"/>

    <g s:x="35" s:y="10" s:pid="Q"/>
    <g s:x="-6" s:y="30" s:pid="CLK"/>
    <g s:x="-6" s:y="30" s:pid="C"/>
    <g s:x="0" s:y="10" s:pid="D"/>
  </g>

  <g s:type="dlatch" transform="translate(250,300)" s:width="30" s:height="40">
    <s:alias val="$dlatch"/>
    <s:alias val="$_DLATCH_"/>
    <s:alias val="adlatch"/>
    <s:alias val="$adlatch"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>

    <path d="M 1,35 H 4 V 25 h 5 v 10 h 3" class="$cell_id"/>

    <g s:x="30" s:y="10" s:pid="Q"/>
    <g s:x="0" s:y="10" s:pid="D"/>
    <g s:x="-1" s:y="30" s:pid="EN"/>
    <g s:x="15" s:y="40" s:pid="ARST"/>
  </g>

  <g s:type="dlatch-bus" transform="translate(300,300)" s:width="30" s:height="40">
    <s:alias val="$dlatch-bus"/>
    <s:alias val="$_DLATCH_-bus"/>
    <s:alias val="adlatch-bus"/>
    <s:alias val="$adlatch-bus"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>

    <path d="M 1,35 H 4 V 25 h 5 v 10 h 3" class="$cell_id"/>
    <path d="M30,2 L32,2 L32,42 L2,42 L2,40" class="$cell_id"/>
    <path d="M32,4 L34,4 L34,44 L4,44 L4,42" class="$cell_id"/>

    <g s:x="35" s:y="10" s:pid="Q"/>
    <g s:x="0" s:y="10" s:pid="D"/>
    <g s:x="-1" s:y="30" s:pid="EN"/>
    <g s:x="17" s:y="44" s:pid="ARST"/>
  </g>

  <g s:type="dlatchn" transform="translate(350,300)" s:width="30" s:height="40">
    <s:alias val="$dlatchn"/>
    <s:alias val="$_DLATCH_N_"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>

    <path d="M 1,25 H 4 V 35 H 9 V 25 h 3" class="$cell_id"/>

    <g s:x="30" s:y="10" s:pid="Q"/>
    <g s:x="0" s:y="10" s:pid="D"/>
    <g s:x="-1" s:y="30" s:pid="EN"/>
  </g>

  <g s:type="dlatchn-bus" transform="translate(400,300)" s:width="30" s:height="40">
    <s:alias val="$dlatchn-bus"/>
    <s:alias val="$_DLATCH_N_-bus"/>

    <rect width="30" height="40" x="0" y="0" class="$cell_id"/>

    <path d="M 1,25 H 4 V 35 H 9 V 25 h 3" class="$cell_id"/>
    <path d="M30,2 L32,2 L32,42 L2,42 L2,40" class="$cell_id"/>
    <path d="M32,4 L34,4 L34,44 L4,44 L4,42" class="$cell_id"/>

    <g s:x="35" s:y="10" s:pid="Q"/>
    <g s:x="0" s:y="10" s:pid="D"/>
    <g s:x="-1" s:y="30" s:pid="EN"/>
  </g>

  <g s:type="_AOI3_" transform="translate(50, 400)" s:width="66" s:height="40">
    <s:alias val="$_AOI3_"/>

    <path d="M0,0 L0,25 L15,25 A15 12.5 0 0 0 15,0 Z" class="$cell_id"/>
    <path d="M30,13 A30 25 0 0 1 30,38 A30 25 0 0 0 60,25.5 A30 25 0 0 0 30,13" class="$cell_id"/>
    <circle cx="63" cy="25.5" r="3" class="$cell_id"/>
    <path d="M0,32 L33,32" />
    <g s:x="0" s:y="5"  s:pid="A"/>
    <g s:x="0" s:y="20"  s:pid="B"/>
    <g s:x="0" s:y="32"  s:pid="C"/>
    <g s:x="66" s:y="25.5" s:pid="Y"/>
    <!-- <path d="M-5,5 L0,5"/> -->
    <!-- <path d="M-5,20 L0,20"/> -->
    <!-- <path d="M-5,32 L0,32"/> -->
    <!-- <path d="M 70,25.5 L 66,25.5"/> -->
  </g>

  <g s:type="_OAI3_" transform="translate(150, 400)" s:width="66" s:height="40">
    <s:alias val="$_OAI3_"/>

    <path d="M30,13 L30,38 L45,38 A15 12.5 0 0 0 45,13 Z" class="$cell_id"/>
    <path d="M0,0 A30 25 0 0 1 0,25 A30 25 0 0 0 30,12.5 A30 25 0 0 0 0,0" class="$cell_id"/>
    <circle cx="63" cy="25.5" r="3" class="$cell_id"/>
    <path d="M0,32 L30,32" />

    <g s:x="2" s:y="5"  s:pid="A"/>
    <g s:x="2" s:y="20"  s:pid="B"/>
    <g s:x="0" s:y="32"  s:pid="C"/>
    <g s:x="66" s:y="25.5" s:pid="Y"/>
    <!-- <path d="M-5,5 L2,5"/> -->
    <!-- <path d="M-5,20 L2,20"/> -->
    <!-- <path d="M-5,32 L0,32"/> -->
    <!-- <path d="M 70,25.5 L 66,25.5"/> -->
  </g>

  <!-- AOI4 -->

  <g s:type="_AOI4_" transform="translate(250, 400)" s:width="66" s:height="40">
    <s:alias val="$_AOI4_"/>

    <path d="M0,0 L0,25 L15,25 A15 12.5 0 0 0 15,0 Z" class="$cell_id"/>
    <path d="M0,25 L0,50 L15,50 A15 12.5 0 0 0 15,25 Z" class="$cell_id"/>
    <path d="M30,12.5 A30 25 0 0 1 30,37.5 A30 25 0 0 0 60,25.5 A30 25 0 0 0 30,12.5" class="$cell_id"/>
    <circle cx="63" cy="25.5" r="3" class="$cell_id"/>
    <g s:x="0" s:y="5"  s:pid="A"/>
    <g s:x="0" s:y="20"  s:pid="B"/>
    <g s:x="0" s:y="30"  s:pid="C"/>
    <g s:x="0" s:y="45"  s:pid="D"/>
    <g s:x="66" s:y="25.5" s:pid="Y"/>
    <!-- <path d="M-5,5 L0,5"/> -->
    <!-- <path d="M-5,20 L0,20"/> -->
    <!-- <path d="M-5,30 L0,30"/> -->
    <!-- <path d="M-5,45 L0,45"/> -->
    <!-- <path d="M 70,25.5 L 66,25.5"/> -->
  </g>

  <!-- OAI4 -->

  <g s:type="_OAI4_" transform="translate(350, 400)" s:width="66" s:height="40">
    <s:alias val="$_OAI4_"/>

    <path d="M30,13 L30,38 L45,38 A15 12.5 0 0 0 45,13 Z" class="$cell_id"/>
    <path d="M0,0 A30 25 0 0 1 0,25 A30 25 0 0 0 30,12.5 A30 25 0 0 0 0,0" class="$cell_id"/>
    <path d="M0,25 A30 25 0 0 1 0,50 A30 25 0 0 0 30,37.5 A30 25 0 0 0 0,25" class="$cell_id"/>
    <circle cx="63" cy="25.5" r="3" class="$cell_id"/>

    <g s:x="2" s:y="5"  s:pid="A"/>
    <g s:x="2" s:y="20"  s:pid="B"/>
    <g s:x="2" s:y="30"  s:pid="C"/>
    <g s:x="2" s:y="45"  s:pid="D"/>
    <g s:x="66" s:y="25.5" s:pid="Y"/>
    <!-- <path d="M-5,5 L2,5"/> -->
    <!-- <path d="M-5,20 L2,20"/> -->
    <!-- <path d="M-5,30 L2,30"/> -->
    <!-- <path d="M-5,45 L2,45"/> -->
    <!-- <path d="M 70,25.5 L 66,25.5"/> -->
  </g>

  <g s:type="generic" transform="translate(550,250)" s:width="30" s:height="40">

    <text x="15" y="-4" class="nodelabel $cell_id" s:attribute="ref">generic</text>
    <rect width="30" height="40" s:generic="body" class="$cell_id"/>

    <g transform="translate(30, 10)" s:x="30" s:y="10" s:pid="out0">
      <text x="5" y="-4" style="fill:#000; stroke:none" class="$cell_id">out0</text>
    </g>
    <g transform="translate(30, 30)" s:x="30" s:y="30" s:pid="out1">
      <text x="5" y="-4" style="fill:#000;stroke:none" class="$cell_id">out1</text>
    </g>
    <g transform="translate(0, 10)" s:x="0" s:y="10" s:pid="in0">
      <text x="-3" y="-4" class="inputPortLabel $cell_id">in0</text>
    </g>
    <g transform="translate(0, 30)" s:x="0" s:y="30" s:pid="in1">
      <text x="-3" y="-4" class="inputPortLabel $cell_id">in1</text>
    </g>
  </g>

</svg>
"""


def convert_google130nm_schematicsvg_to_netlistsvgskin(cell_folder: str = "./") -> str:
    prefix_s = "{https://github.com/nturley/netlistsvg}"
    prefix_xlink = "{http://www.w3.org/2000/svg}"

    cell_folder = cell_folder
    definition_json_path = cell_folder + "definition.json"
    with open(definition_json_path, "r") as f:
        definition_json = f.read()
    definition_dict = json.loads(definition_json)
    cell_prefix = definition_dict["file_prefix"]
    schematic_svg_path = cell_folder + cell_prefix + ".schematic.svg"

    tree = ET.parse(schematic_svg_path)
    root = tree.getroot()

    result = ""

    for child in root:
        # print(child.tag, child.attrib)
        if child.tag == f"{prefix_xlink}g":
            if (
                child.attrib[f"{prefix_s}type"] == "outputExt"
                or child.attrib[f"{prefix_s}type"] == "inputExt"
            ):
                # print(child.findall("*"))
                transform_text = child.get("transform")
                print("transform_text", transform_text)

                transform_x = float(
                    re.search(r"(?<=\().*(?=,)", transform_text).group()
                )
                transform_y = float(
                    re.search(r"(?<=,).*(?=\))", transform_text).group()
                )
                print(f"transform ({transform_x}, {transform_y})")

                port_name = child.find(f"{prefix_xlink}text").text
                print("port_name", port_name)

                original_position = child.find(f"{prefix_xlink}g")
                absolute_x = float(original_position.get(f"{prefix_s}x")) + transform_x
                absolute_y = float(original_position.get(f"{prefix_s}y")) + transform_y
                print(f"absolute ({absolute_x},{absolute_y})")

                result += f"""<g s:x="{absolute_x}" s:y="{absolute_y}" s:pid="{port_name}" />"""
            else:
                result += ET.tostring(child, encoding="unicode")

        elif child.tag == f"{prefix_xlink}line":
            result += ET.tostring(child, encoding="unicode")

    print("--------------")
    for i in range(20):
        result += f"""<s:alias val="{cell_prefix}_{i}" />"""
    result = (
        f"""<g s:type="{cell_prefix}" s:width="{root.get("width")}" s:height="{root.get("height")}">"""
        + result
        + "</g>"
    )

    # 否则不会显示
    result = result.replace('<ns0:line xmlns:ns0="http://www.w3.org/2000/svg"', "<line")
    result = result.replace('xmlns:ns0="http://www.w3.org/2000/svg"', "")
    result = result.replace('xmlns:ns1="https://github.com/nturley/netlistsvg"', "")
    result = result.replace("ns0:", "")
    result = result.replace("ns1:", "s:")

    # 解决id报错的问题 换成s:pid
    result = result.replace(" id=", " s:pid=")

    print(result)

    return result

# deal with macOS .DS_Store file
if os.path.exists(path_cells + ".DS_Store"):
    os.remove(path_cells + ".DS_Store")

folder_names = os.listdir(path_cells)
# 移去没有逻辑电路图的cell
for no_schematic_svg in [
    "einvp",
    "lpflow_bleeder",
    "conb",
    "einvn",
    "ebufn",
    "macro_sparecell",
]:
    folder_names.remove(no_schematic_svg)
print(f"有{len(folder_names)}个文件夹", folder_names)

nelistsvg_google130nm_skin_content += netlistsvg_default_skin_before
i = 0
for folder_name in folder_names:
    nelistsvg_google130nm_skin_content += (
        convert_google130nm_schematicsvg_to_netlistsvgskin(
            cell_folder=path_cells + folder_name + "/"
        )
    )
    i += 1
    print(f"【{i}/{len(folder_names)}】")
nelistsvg_google130nm_skin_content += netlistsvg_default_skin_after

with open(nelistsvg_google130nm_skin_path, "w") as f:
    f.write(nelistsvg_google130nm_skin_content)
