module testbench();
    reg [2:0] x;
    wire [7:0] y;
    decoder DUT(x, y);

    initial begin
        $dumpfile(`DUMP_FILE_NAME);
        $dumpvars;
    end

    integer i;
    initial begin
        for (i = 0; i < 8; i = i + 1) begin
            #1 x = i;
        end
    end
endmodule
