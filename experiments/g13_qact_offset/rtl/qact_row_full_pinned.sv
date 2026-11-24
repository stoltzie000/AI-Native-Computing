`timescale 1ns/1ps
// Complete combinational QACT mathematical reference with openTPU-pinned reciprocal.
// Original hierarchical offset and multiply/Q8 sub-blocks; NO original reciprocal RTL claim.
// External pinned arithmetic: FeSens/openTPU@d84db55712aba0d40811d7762cb052f05d55b7e5.
module qact_row_full_pinned(
 input wire [2047:0] x_flat,
 output wire [511:0] q_flat, output wire [39:0] offset_flat,
 output wire [31:0] row_scale, output wire [31:0] row_inverse
);
 reg [31:0] row_max,word_abs;
 integer i;
 always @* begin
  row_max=0;
  for(i=0;i<64;i=i+1)begin
   word_abs={1'b0,x_flat[i*32+:31]};
   if(word_abs[30:23]==0)word_abs=0;
   if(word_abs>row_max)row_max=word_abs;
  end
 end
 assign row_scale=(row_max==0)?32'h00000000:otpu_fp::fp_mul(row_max,32'h3c010204);
 assign row_inverse=(row_max==0)?32'h00000000:
       otpu_fp::fp_mul(32'h42fe0000,otpu_fp::fp_recip(row_max));
 qact_row_scaled_parallel row(.x_flat(x_flat),.row_inverse(row_inverse),
                                .q_flat(q_flat),.offset_flat(offset_flat));
endmodule
