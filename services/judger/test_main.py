import json

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_main():
#     decoder_reference = """
# module Zero(
#     output out
# );
#     assign out=0;
# endmodule
#     """.strip()

#     decoder_student = """
# module Zero(
#     output out
# );
#     assign out=0;
# endmodule
#     """.strip()

#     testbench = """
# module testbench();
#     wire out;
#     Zero myZero(y);

#     initial begin
#         $dumpfile(`DUMP_FILE_NAME);
#         $dumpvars;
#     end

#     initial begin
#         #1;
#     end
# endmodule
#     """.strip()

    decoder_reference = """
module decoder(
    input [2:0] x,
    output reg [7:0] y
);
    always @ (*) begin
        case (x)
        3'b000: y=8'b0000_0001;
        3'b001: y=8'b0000_0010;
        3'b010: y=8'b0000_0100;
        3'b011: y=8'b0000_1000;
        3'b100: y=8'b0001_0000;
        3'b101: y=8'b0010_0000;
        3'b110: y=8'b0100_0000;
        3'b111: y=8'b1000_0000;
        endcase
    end
endmodule
    """.strip()

    decoder_student = """
module decoder(
    input [2:0] x,
    output reg [7:0] y
);
    always @ (*) begin
        case (x)
        3'b000: y=8'b0000_0001;
        3'b001: y=8'b0000_0010;
        3'b010: y=8'b0000_0100;
        3'b011: y=8'b0000_1000;
        3'b100: y=8'b0001_0000;
        3'b101: y=8'b0010_0000;
        3'b110: y=8'b0100_0000;
        3'b111: y=8'b1000_0000;
        endcase
    end
endmodule
    """.strip()

    testbench = """
module testbench();
    reg [2:0] x;
    wire [7:0] y;
    decoder DUT(x, y);
    
    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars(0, x, y);
    end

    initial begin
        for (i = 0; i < 8; i = i + 1) begin
            #1 x = i;
        end
    end
endmodule
    """.strip()

    service_request = {
        "code_reference": decoder_reference,
        "code_student": decoder_student,
        "signal_names": ["x","y"],
        "testbench": testbench,
        "top_module": "decoder",
    }
    response = client.post("/", json=service_request)
    print(json.loads(response.content))
    assert response.status_code == 200
