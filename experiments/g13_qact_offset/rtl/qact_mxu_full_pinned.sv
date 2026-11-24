`timescale 1ns/1ps
// Full mathematical G1.3 QACT -> INT48 MXU -> FP32 epilogue.
// QACT reciprocal uses pinned openTPU external arithmetic, not an original design.
// Inputs are stable/latching at start. No memory PHY, DMA or actual AI model.
module qact_mxu_full_pinned(
 input wire clk,rst_n,start,
 input wire [2047:0] x_flat,
 input wire [2559:0] w_flat,
 input wire [79:0] dw_flat,
 input wire [159:0] weight_scale_flat,
 output wire ready,output reg done,
 output wire [239:0] acc_flat,
 output wire [159:0] fp32_flat,
 output wire [511:0] q_flat,
 output wire [39:0] offset_flat,
 output wire [31:0] activation_scale,
 output wire [15:0] dropped_groups,consumed_groups
);
 localparam IDLE=2'd0,LAUNCH=2'd1,RUN=2'd2;
 reg [1:0] state;
 reg [2047:0] x_hold;
 reg [2559:0] w_hold;
 reg [79:0] dw_hold;
 reg [159:0] scale_hold;
 wire [31:0] inverse_reference;
 wire [63:0] da_flat;
 wire core_ready,core_done;
 genvar k;
 generate for(k=0;k<8;k=k+1)begin:OFFSET
  assign da_flat[k*8+:8]={3'b000,offset_flat[k*5+:5]};
 end endgenerate
 qact_row_full_pinned qact(.x_flat(x_hold),.q_flat(q_flat),
  .offset_flat(offset_flat),.row_scale(activation_scale),
  .row_inverse(inverse_reference));
 exact_mxu_int8_core core(.clk(clk),.rst_n(rst_n),.start(state==LAUNCH),
  .q_flat(q_flat),.w_flat(w_hold),.da_flat(da_flat),.dw_flat(dw_hold),
  .ready(core_ready),.done(core_done),.acc_flat(acc_flat),
  .dropped_groups(dropped_groups),.consumed_groups(consumed_groups));
 mxu_integer_epilogue epilogue(.acc_flat(acc_flat),
  .weight_scale_flat(scale_hold),.activation_scale(activation_scale),
  .result_flat(fp32_flat));
 assign ready=(state==IDLE);
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;done<=0;
   x_hold<=0;w_hold<=0;dw_hold<=0;scale_hold<=0;
  end else begin
   done<=0;
   case(state)
    IDLE:if(start)begin
     x_hold<=x_flat;w_hold<=w_flat;dw_hold<=dw_flat;
     scale_hold<=weight_scale_flat;state<=LAUNCH;
    end
    LAUNCH:if(core_ready)state<=RUN;
    RUN:if(core_done)begin done<=1;state<=IDLE;end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
