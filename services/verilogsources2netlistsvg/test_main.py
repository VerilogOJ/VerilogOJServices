import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_read_main():
    inverter_v = """
module top(in, out);
    input in;
    output out;

    assign out = ~in;
endmodule
    """.strip()

    netlist_svg = """
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:s="https://github.com/nturley/netlistsvg" width="184" height="54">
  <style>svg {
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
  .nodelabel {
    text-anchor: middle;
  }
  .inputPortLabel {
    text-anchor: end;
  }
  .splitjoinBody {
    fill:#000;
  }</style>
  <g s:type="not" transform="translate(77,22)" s:width="30" s:height="20" id="cell_$auto$simplemap.cc:38:simplemap_not$75">
    <s:alias val="$_NOT_"/>
    <s:alias val="$not"/>
    <s:alias val="$logic_not"/>
    <path d="M0,0 L0,20 L20,10 Z" class="cell_$auto$simplemap.cc:38:simplemap_not$75"/>
    <circle cx="23" cy="10" r="3" class="cell_$auto$simplemap.cc:38:simplemap_not$75"/>
    <g s:x="0" s:y="10" s:pid="A"/>
    <g s:x="25" s:y="10" s:pid="Y"/>
  </g>
  <g s:type="inputExt" transform="translate(12,22)" s:width="30" s:height="20" id="cell_in">
    <text x="15" y="-4" class="nodelabel cell_in" s:attribute="ref">in</text>
    <s:alias val="$_inputExt_"/>
    <path d="M0,0 L0,20 L15,20 L30,10 L15,0 Z" class="cell_in"/>
    <g s:x="28" s:y="10" s:pid="Y"/>
  </g>
  <g s:type="outputExt" transform="translate(142,22)" s:width="30" s:height="20" id="cell_out">
    <text x="15" y="-4" class="nodelabel cell_out" s:attribute="ref">out</text>
    <s:alias val="$_outputExt_"/>
    <path d="M30,0 L30,20 L15,20 L0,10 L15,0 Z" class="cell_out"/>
    <g s:x="0" s:y="10" s:pid="A"/>
  </g>
  <line x1="40" x2="77" y1="32" y2="32" class="net_2"/>
  <line x1="102" x2="142" y1="32" y2="32" class="net_3"/>
</svg>
    """.strip()

    service_request = {"verilog_sources": [inverter_v], "top_module": "top"}
    response = client.post("/", json=service_request)
    assert response.status_code == 200
    assert json.loads(response.content)["netlist_svg"].strip() == netlist_svg
