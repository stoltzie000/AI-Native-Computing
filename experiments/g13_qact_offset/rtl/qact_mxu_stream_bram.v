`timescale 1ns/1ps
// One frame: 80 little-endian weight words, 3 offset words (10 bytes
// plus 2 pad bytes), 5 weight scales, then 64 raw FP32 activations.
// The result is five FP32 beats. One frame in flight; reset cancels it.
module qact_mxu_stream_bram(
    input wire clk, rst_n,
    input wire input_valid, output wire input_ready, input wire [31:0] input_data,
    output wire output_valid, input wire output_ready,
    output wire [31:0] output_data, output wire output_last
);
    localparam HEADER=0, ACTIVATIONS=1, COLLECT=2, LAUNCH_MXU=3, WAIT_MXU=4,
               LAUNCH_EPILOGUE=5, WAIT_EPILOGUE=6, RESULTS=7;
    reg [2:0] state;
    reg [6:0] index;
    reg [2559:0] weights;
    reg [95:0] weight_offsets;
    reg [159:0] weight_scales;
    reg [511:0] codes;
    reg [63:0] activation_offsets;
    reg [31:0] activation_scale;
    wire q_input_ready, q_valid, q_last;
    wire [1:0] q_kind;
    wire [7:0] q_data;
    wire collecting = state == COLLECT;
    qact_row_stream_bram qact(
        .clk(clk), .rst_n(rst_n), .input_valid(state == ACTIVATIONS && input_valid),
        .input_ready(q_input_ready), .input_data(input_data), .output_valid(q_valid),
        .output_ready(collecting), .output_data(q_data), .output_kind(q_kind),
        .output_last(q_last), .row_done()
    );
    assign input_ready = state == HEADER || (state == ACTIVATIONS && q_input_ready);
    wire accept = rst_n && input_ready && input_valid;

    // All payload registers are completely filled before their consumer starts.
    always @(posedge clk) begin
        if (state == HEADER && accept) begin
            if (index < 80)
                weights <= {input_data,weights[2559:32]};
            else if (index < 83)
                weight_offsets <= {input_data,weight_offsets[95:32]};
            else
                weight_scales <= {input_data,weight_scales[159:32]};
        end
        if (collecting && q_valid) begin
            case (q_kind)
                0: codes <= {q_data,codes[511:8]};
                1: activation_offsets <= {q_data,activation_offsets[63:8]};
                2: activation_scale <= {q_data,activation_scale[31:8]};
            endcase
        end
    end

    wire mxu_ready, mxu_done, epilogue_ready, epilogue_done;
    wire [239:0] accumulators;
    wire [15:0] dropped_groups, consumed_groups;
    wire [159:0] results;
    exact_mxu_int8_core mxu(
        .clk(clk), .rst_n(rst_n), .start(state == LAUNCH_MXU),
        .q_flat(codes), .w_flat(weights), .da_flat(activation_offsets), .dw_flat(weight_offsets[79:0]),
        .ready(mxu_ready), .done(mxu_done), .acc_flat(accumulators),
        .dropped_groups(dropped_groups), .consumed_groups(consumed_groups)
    );
    mxu_integer_epilogue_serial epilogue(
        .clk(clk), .rst_n(rst_n), .start(state == LAUNCH_EPILOGUE), .acc_flat(accumulators),
        .weight_scale_flat(weight_scales), .activation_scale(activation_scale),
        .ready(epilogue_ready), .done(epilogue_done), .result_flat(results)
    );
    assign output_valid = state == RESULTS;
    assign output_data = results[index[2:0]*32+:32];
    assign output_last = output_valid && index == 4;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= HEADER;
            index <= 0;
        end else begin
            case (state)
                HEADER: if (accept) begin
                    if (index == 87) begin
                        index <= 0;
                        state <= ACTIVATIONS;
                    end else index <= index + 1'b1;
                end
                ACTIVATIONS: if (accept) begin
                    if (index == 63) begin
                        index <= 0;
                        state <= COLLECT;
                    end else index <= index + 1'b1;
                end
                COLLECT: if (q_valid && q_last) state <= LAUNCH_MXU;
                LAUNCH_MXU: if (mxu_ready) state <= WAIT_MXU;
                WAIT_MXU: if (mxu_done) state <= LAUNCH_EPILOGUE;
                LAUNCH_EPILOGUE: if (epilogue_ready) state <= WAIT_EPILOGUE;
                WAIT_EPILOGUE: if (epilogue_done) state <= RESULTS;
                RESULTS: if (output_ready) begin
                    if (output_last) begin
                        index <= 0;
                        state <= HEADER;
                    end else index <= index + 1'b1;
                end
            endcase
        end
    end
endmodule
