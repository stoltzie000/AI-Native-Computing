`timescale 1ns/1ps
// Original clocked reciprocal-to-QACT orchestration, pinned external FP32 arithmetic.
// 64 raw FP32 inputs latched once. No external inverse input.
// 11-cycle (normal) Newton controller + 73-cycle serial QACT row engine.
// Not a complete DRAM-backed accelerator; not independently authored FP32 add/mul.
module qact_row_clocked_pinned(
 input wire clk,rst_n,start,input wire [2047:0] x_flat,
 output wire ready,output reg done,
 output wire [511:0] q_flat,output wire [39:0] offset_flat,
 output reg [31:0] row_scale,row_inverse
);
 localparam IDLE=3'd0,START_RECIP=3'd1,WAIT_RECIP=3'd2,
            START_QUANT=3'd3,WAIT_QUANT=3'd4;
 reg [2:0] state;
 reg [2047:0] x_hold;
 reg [31:0] row_max,absv;
 integer i;
 always @*begin
  row_max=0;
  for(i=0;i<64;i=i+1)begin
   absv={1'b0,x_hold[i*32+:31]};
   if(absv[30:23]==0)absv=0;
   if(absv>row_max)row_max=absv;
  end
 end
 wire rec_ready,rec_done,quant_ready,quant_done;
 wire [31:0] reciprocal;
 wire [31:0] inverse_value,scale_value;
 fp32_mul_ftz inverse_mul(.a(reciprocal),.b(32'h42fe0000),.y(inverse_value));
 fp32_mul_ftz scale_mul(.a(row_max),.b(32'h3c010204),.y(scale_value));
 qact_recip_serial_pinned rec(.clk(clk),.rst_n(rst_n),
   .start(state==START_RECIP),.x(row_max),
   .ready(rec_ready),.done(rec_done),.result(reciprocal));
 qact_row_scaled_serial quant(.clk(clk),.rst_n(rst_n),
   .start(state==START_QUANT),.x_flat(x_hold),.row_inverse(row_inverse),
   .ready(quant_ready),.done(quant_done),.q_flat(q_flat),
   .offset_flat(offset_flat));
 assign ready=(state==IDLE);
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;done<=0;x_hold<=0;row_inverse<=0;row_scale<=0;
  end else begin
   done<=0;
   case(state)
    IDLE:if(start)begin x_hold<=x_flat;state<=START_RECIP;end
    START_RECIP:if(rec_ready)state<=WAIT_RECIP;
    WAIT_RECIP:if(rec_done)begin
     row_inverse<=inverse_value;row_scale<=scale_value;
     state<=START_QUANT;
    end
    START_QUANT:if(quant_ready)state<=WAIT_QUANT;
    WAIT_QUANT:if(quant_done)begin done<=1;state<=IDLE;end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
