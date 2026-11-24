`timescale 1ns/1ps
// 64-value QACT research candidate with externally supplied row inverse.
// Reuses hierarchical group offsets; 8 group factors + 64 lane multiply/Q8.
module qact_row_scaled_parallel(
 input wire [2047:0] x_flat,input wire [31:0] row_inverse,
 output wire [511:0] q_flat,output wire [39:0] offset_flat
);
 wire [31:0] group_factor[0:7];
 qact_group_offset_hier off(.x_flat(x_flat),.offset_flat(offset_flat));
 genvar g,i;
 generate for(g=0;g<8;g=g+1) begin:GROUP
  wire [4:0] shift=offset_flat[g*5+:5];
  wire [7:0] exponent=8'd127+{3'b000,shift};
  wire [31:0] pow2={1'b0,exponent,23'b0};
  fp32_mul_ftz groupmul(.a(row_inverse),.b(pow2),.y(group_factor[g]));
 end
 for(i=0;i<64;i=i+1)begin:LANE
  wire [31:0] scaled;
  fp32_mul_ftz product(.a(x_flat[i*32+:32]),.b(group_factor[i/8]),.y(scaled));
  qact_q8_rne quant(.x(scaled),.q(q_flat[i*8+:8]));
 end endgenerate
endmodule
