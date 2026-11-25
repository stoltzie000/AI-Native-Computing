`timescale 1ns/1ps
// Time-multiplexed five-output signed-INT48 to FP32 RNE/FTZ epilogue.
// One integer converter and one binary32 FTZ multiplier; 11 active cycles/job.
// This is a research resource-sharing candidate, not a physical clock claim.
module mxu_integer_epilogue_serial #(parameter PREFETCH_CONVERSION=0)(
 input wire clk,rst_n,start,
 input wire [239:0] acc_flat,input wire [159:0] weight_scale_flat,
 input wire [31:0] activation_scale,
 output wire ready,output reg done,output reg [159:0] result_flat
);
 localparam IDLE=2'd0, FACTOR=2'd1, WEIGHT=2'd2, ACTIVATE=2'd3;
 reg [1:0] state;
 reg [2:0] idx;
 reg [239:0] acc_latched;
 reg [159:0] weight_latched;
 reg [31:0] activation_latched,factor,intermediate;
 reg [47:0] selected_acc;
 reg [31:0] selected_weight;
 always @* begin
  case(idx)
   0: begin selected_acc=acc_latched[47:0];selected_weight=weight_latched[31:0];end
   1: begin selected_acc=acc_latched[95:48];selected_weight=weight_latched[63:32];end
   2: begin selected_acc=acc_latched[143:96];selected_weight=weight_latched[95:64];end
   3: begin selected_acc=acc_latched[191:144];selected_weight=weight_latched[127:96];end
   4: begin selected_acc=acc_latched[239:192];selected_weight=weight_latched[159:128];end
   default: begin selected_acc=0;selected_weight=0;end
  endcase
 end
 wire [31:0] integer_float,weight_operand,mul_result;
 wire [47:0] conversion_input;
 generate if(PREFETCH_CONVERSION)begin: PREFETCH
  reg [47:0] following_acc;
  reg [31:0] converted;
  always @* begin
   case(idx)
    0: following_acc=acc_latched[95:48];
    1: following_acc=acc_latched[143:96];
    2: following_acc=acc_latched[191:144];
    3: following_acc=acc_latched[239:192];
    default: following_acc=0;
   endcase
  end
  // FACTOR overlaps lane 0 conversion. Each ACTIVATE overlaps conversion
  // of the following lane. WEIGHT always consumes a completed conversion.
  assign conversion_input=(state==FACTOR)?acc_latched[47:0]:following_acc;
  always @(posedge clk)
   if(state==FACTOR || (state==ACTIVATE && idx<4)) converted<=integer_float;
  assign weight_operand=converted;
 end else begin: DIRECT
  assign conversion_input=selected_acc;
  assign weight_operand=integer_float;
 end endgenerate
 wire [31:0] mul_a=(state==FACTOR)?activation_latched:
                    (state==WEIGHT)?weight_operand:intermediate;
 wire [31:0] mul_b=(state==FACTOR)?32'h37800000:
                    (state==WEIGHT)?selected_weight:factor;
 int48_to_fp32_rne convert(.integer_in(conversion_input),.y(integer_float));
 fp32_mul_ftz multiplier(.a(mul_a),.b(mul_b),.y(mul_result));
 assign ready=(state==IDLE);
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin
    state<=IDLE;idx<=0;acc_latched<=0;weight_latched<=0;
    activation_latched<=0;factor<=0;intermediate<=0;
    result_flat<=0;done<=0;
  end else begin
    done<=0;
    case(state)
     IDLE: if(start) begin
       acc_latched<=acc_flat;
       weight_latched<=weight_scale_flat;
       activation_latched<=activation_scale;
       idx<=0;
       state<=FACTOR;
     end
     FACTOR: begin factor<=mul_result;state<=WEIGHT;end
     WEIGHT: begin intermediate<=mul_result;state<=ACTIVATE;end
     ACTIVATE: begin
       result_flat[idx*32+:32]<=mul_result;
       if(idx==4) begin state<=IDLE;done<=1;end
       else begin idx<=idx+1'b1;state<=WEIGHT;end
     end
     default: state<=IDLE;
    endcase
  end
 end
endmodule
