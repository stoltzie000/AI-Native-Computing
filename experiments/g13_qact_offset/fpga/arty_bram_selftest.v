`timescale 1ns/1ps
// Arty A7-100T fixed-workload demonstration. BTN0 restarts the 24-case
// sequence. LD4 and LD5 latch pass and failure respectively.
module arty_bram_selftest(input wire clk, reset_button, output reg passed, failed);
    (* ASYNC_REG = "TRUE" *) reg [1:0] reset_pipe = 2'b11;
    always @(posedge clk or posedge reset_button) begin
        if (reset_button) reset_pipe <= 2'b11;
        else reset_pipe <= {reset_pipe[0],1'b0};
    end
    wire rst_n = !reset_pipe[1];
    localparam INPUT_WORDS = 24*152, RESULT_WORDS = 24*5;
    reg [31:0] stimulus [0:INPUT_WORDS-1];
    reg [31:0] expected [0:RESULT_WORDS-1];
    initial begin
        $readmemh("frames.hex",stimulus);
        $readmemh("results.hex",expected);
    end
    reg [11:0] issued;
    reg [6:0] received;
    reg [2:0] lane;
    reg word_valid;
    reg [31:0] word, expected_word;
    reg [15:0] watchdog;
    wire running = rst_n && !passed && !failed;
    wire ready, valid, last;
    wire [31:0] result;
    wire can_issue = !word_valid || ready;
    wire next_word = running && can_issue && issued < INPUT_WORDS;
    wire [6:0] expected_address = running && valid && received < RESULT_WORDS-1
                                 ? received + 1'b1 : received;
    always @(posedge clk) begin
        if (next_word) word <= stimulus[issued];
        expected_word <= expected[expected_address];
    end
    qact_mxu_stream_bram dut(
        .clk(clk), .rst_n(rst_n), .input_valid(word_valid && running), .input_ready(ready),
        .input_data(word), .output_valid(valid), .output_ready(running),
        .output_data(result), .output_last(last)
    );
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            issued <= 0; received <= 0; lane <= 0; word_valid <= 0;
            passed <= 0; failed <= 0; watchdog <= 0;
        end else if (running) begin
            watchdog <= watchdog + 1'b1;
            if (can_issue) begin
                word_valid <= next_word;
                if (next_word) issued <= issued + 1'b1;
            end
            if (&watchdog)
                failed <= 1;
            else if (valid) begin
                if (result != expected_word || last != (lane == 4))
                    failed <= 1;
                else if (received == RESULT_WORDS-1) begin
                    if (issued == INPUT_WORDS && !word_valid) passed <= 1;
                    else failed <= 1;
                end else begin
                    received <= received + 1'b1;
                    lane <= lane == 4 ? 3'd0 : lane + 1'b1;
                end
            end
        end
    end
endmodule
