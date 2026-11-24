module qact_scaled_q8(input wire [31:0] x,inv_group,output wire [31:0] scaled,output wire signed [7:0] q);
 fp32_mul_ftz mult(.a(x),.b(inv_group),.y(scaled));
 qact_q8_rne quant(.x(scaled),.q(q));
endmodule
