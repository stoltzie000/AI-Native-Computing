`timescale 1ns/1ps
// Two passes over a 64-word row: reduce maxima during input, then replay
// one synchronous RAM read per Q8 transfer. A stalled output holds its RAM word.
module qact_row_stream_bram(
    input wire clk, rst_n,
    input wire input_valid, output wire input_ready, input wire [31:0] input_data,
    output wire output_valid, input wire output_ready, output wire [7:0] output_data,
    output wire [1:0] output_kind, output wire output_last, output reg row_done
);
    localparam LOAD=0, START_RECIP=1, WAIT_RECIP=2, FACTORS=3, PRIME=4,
               SEND_Q=5, SEND_OFFSETS=6, SEND_SCALE=7;
    reg [2:0] state;
    reg [5:0] index;
    wire [2:0] group_index = index[2:0];
    reg [30:0] row_max, running_group_max;
    reg [30:0] group_max [0:7];
    reg [4:0] offsets [0:7];
    reg [31:0] factors [0:7];
    reg [31:0] scale, inverse;

    assign input_ready = state == LOAD;
    wire accept = rst_n && input_ready && input_valid;
    wire [30:0] magnitude = input_data[30:23] == 0 ? 31'd0 : input_data[30:0];
    wire [30:0] next_group_max = magnitude > running_group_max ? magnitude : running_group_max;
    wire [30:0] selected_max = group_max[group_index];
    // Both maxima are unsigned FTZ magnitudes. A nonzero group's maximum
    // cannot exceed the row maximum, so the adjusted difference is nonnegative.
    wire [8:0] exponent_gap = {1'b0,row_max[30:23]} - {1'b0,selected_max[30:23]}
                            - (selected_max[22:0] > row_max[22:0]);
    wire [4:0] group_offset = selected_max == 0 ? 5'd0 :
                              exponent_gap > 31 ? 5'd31 : exponent_gap[4:0];
    wire [7:0] power_exponent = 8'd127 + {3'd0,group_offset};

    (* ram_style = "block" *) reg [31:0] activation [0:63];
    reg [31:0] read_word;
    wire read_enable = state == PRIME || (state == SEND_Q && output_ready && index != 63);
    wire [5:0] read_address = state == PRIME ? 6'd0 : index + 6'd1;
    always @(posedge clk) begin
        if (accept)
            activation[index] <= input_data;
        if (read_enable)
            read_word <= activation[read_address];
    end

    wire recip_ready, recip_done;
    wire [31:0] reciprocal;
    qact_recip_serial_original_arith recip(
        .clk(clk), .rst_n(rst_n), .start(state == START_RECIP),
        .x({1'b0,row_max}), .ready(recip_ready), .done(recip_done), .result(reciprocal)
    );

    reg [31:0] mult_a, mult_b;
    always @* begin
        case (state)
            START_RECIP: begin mult_a = {1'b0,row_max}; mult_b = 32'h3c010204; end
            WAIT_RECIP:  begin mult_a = reciprocal; mult_b = 32'h42fe0000; end
            FACTORS:     begin mult_a = inverse; mult_b = {1'b0,power_exponent,23'd0}; end
            default:     begin mult_a = read_word; mult_b = factors[index[5:3]]; end
        endcase
    end
    wire [31:0] product;
    wire signed [7:0] q;
    fp32_mul_ftz shared_mul(.a(mult_a), .b(mult_b), .y(product));
    qact_q8_rne quant(.x(product), .q(q));

    assign output_valid = state == SEND_Q || state == SEND_OFFSETS || state == SEND_SCALE;
    assign output_kind = state == SEND_OFFSETS ? 2'd1 : state == SEND_SCALE ? 2'd2 : 2'd0;
    assign output_data = state == SEND_OFFSETS ? {3'd0,offsets[group_index]} :
                         state == SEND_SCALE ? scale[index[1:0]*8+:8] : q;
    assign output_last = state == SEND_SCALE && index == 3;

    // Every group entry is overwritten before use, even following an aborted row.
    always @(posedge clk) begin
        if (accept && index[2:0] == 7)
            group_max[index[5:3]] <= next_group_max;
        if (state == FACTORS) begin
            offsets[group_index] <= group_offset;
            factors[group_index] <= product;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= LOAD;
            index <= 0;
            row_max <= 0;
            running_group_max <= 0;
            row_done <= 0;
            scale <= 0;
            inverse <= 0;
        end else begin
            row_done <= 0;
            case (state)
                LOAD: if (accept) begin
                    if (magnitude > row_max)
                        row_max <= magnitude;
                    running_group_max <= index[2:0] == 7 ? 31'd0 : next_group_max;
                    index <= index + 1'b1;
                    if (index == 63)
                        state <= START_RECIP;
                end
                START_RECIP: if (recip_ready) begin
                    scale <= product;
                    state <= WAIT_RECIP;
                end
                WAIT_RECIP: if (recip_done) begin
                    inverse <= product;
                    state <= FACTORS;
                end
                FACTORS: begin
                    index <= index + 1'b1;
                    if (group_index == 7) begin
                        index <= 0;
                        state <= PRIME;
                    end
                end
                PRIME: state <= SEND_Q;
                SEND_Q: if (output_ready) begin
                    index <= index + 1'b1;
                    if (index == 63)
                        state <= SEND_OFFSETS;
                end
                SEND_OFFSETS: if (output_ready) begin
                    index <= index + 1'b1;
                    if (group_index == 7) begin
                        index <= 0;
                        state <= SEND_SCALE;
                    end
                end
                SEND_SCALE: if (output_ready) begin
                    index <= index + 1'b1;
                    if (output_last) begin
                        row_done <= 1;
                        row_max <= 0;
                        index <= 0;
                        state <= LOAD;
                    end
                end
            endcase
        end
    end
endmodule
