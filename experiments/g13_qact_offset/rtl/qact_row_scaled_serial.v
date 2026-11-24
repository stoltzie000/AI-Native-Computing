`timescale 1ns/1ps
// One shared FP32 multiplier for 8 group factors + 64 activation products.
// External row inverse; 72 arithmetic issue cycles plus completion cycle.
module qact_row_scaled_serial(
 input wire clk,rst_n,start,input wire [2047:0] x_flat,
 input wire [31:0] row_inverse,
 output wire ready,output reg done,
 output reg [511:0] q_flat,output reg [39:0] offset_flat
);
 localparam IDLE=2'd0,GROUP=2'd1,DATA=2'd2,COMPLETE=2'd3;
 reg [1:0] state;
 reg [6:0] idx;
 reg [2047:0] held_input;
 reg [31:0] held_inverse;
 reg [31:0] factors[0:7];
 wire [39:0] computed_offsets;
 qact_group_offset_hier off(.x_flat(x_flat),.offset_flat(computed_offsets));
 wire [4:0] d=offset_flat[idx*5+:5];
 wire [7:0] exp_pow=8'd127+{3'b000,d};
 wire [31:0] pow2={1'b0,exp_pow,23'b0};
 wire [31:0] operand_a=(state==GROUP)?held_inverse:held_input[idx*32+:32];
 wire [31:0] operand_b=(state==GROUP)?pow2:factors[idx/8];
 wire [31:0] product;
 wire signed [7:0] quantized;
 fp32_mul_ftz mult(.a(operand_a),.b(operand_b),.y(product));
 qact_q8_rne quant(.x(product),.q(quantized));
 assign ready=(state==IDLE);
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;idx<=0;done<=0;
   held_input<=0;held_inverse<=0;q_flat<=0;offset_flat<=0;
  end else begin
   done<=0;
   case(state)
    IDLE:if(start)begin
     held_input<=x_flat;held_inverse<=row_inverse;offset_flat<=computed_offsets;
     idx<=0;q_flat<=0;state<=GROUP;
    end
    GROUP:begin
     factors[idx]<=product;
     if(idx==7)begin idx<=0;state<=DATA;end
     else idx<=idx+1'b1;
    end
    DATA:begin
     q_flat[idx*8+:8]<=quantized;
     if(idx==63)begin idx<=0;state<=COMPLETE;end
     else idx<=idx+1'b1;
    end
    COMPLETE:begin done<=1;state<=IDLE;end
    default:begin state<=IDLE;idx<=0;end
   endcase
  end
 end
endmodule
