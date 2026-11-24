`timescale 1ns/1ps
// G1.3 integer accumulator epilogue for 5 outputs. No QACT hardware.
// Exact upstream MM order: fp32(acc)*weight_scale*(activation_scale*2^-16).
module mxu_integer_epilogue(
  input wire [239:0] acc_flat,
  input wire [159:0] weight_scale_flat,
  input wire [31:0] activation_scale,
  output wire [159:0] result_flat
);
  wire [31:0] activation_factor;
  fp32_mul_ftz activation_pow2(
    .a(activation_scale),.b(32'h37800000),.y(activation_factor)
  );
  genvar i;
  generate for(i=0;i<5;i=i+1) begin: OUT
    wire [31:0] integer_float,scaled_weight;
    int48_to_fp32_rne convert(
      .integer_in(acc_flat[i*48+:48]),.y(integer_float)
    );
    fp32_mul_ftz weight_mul(
      .a(integer_float),.b(weight_scale_flat[i*32+:32]),
      .y(scaled_weight)
    );
    fp32_mul_ftz activation_mul(
      .a(scaled_weight),.b(activation_factor),
      .y(result_flat[i*32+:32])
    );
  end endgenerate
endmodule
