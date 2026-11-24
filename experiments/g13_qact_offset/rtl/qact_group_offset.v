`timescale 1ns/1ps
// QACT D=32 group=8 exponent-offset stage only; NOT full quantizer.
module qact_group_offset(input wire [2047:0] x_flat,output reg [39:0] offset_flat);
 integer i,g,j,diff;
 reg [31:0] row_max,group_max,word_abs;
 always @* begin
  row_max=0;
  for(i=0;i<64;i=i+1) begin
   word_abs={1'b0,x_flat[i*32+:31]};
   if(word_abs[30:23]==0) word_abs=0;
   if(word_abs>row_max) row_max=word_abs;
  end
  offset_flat=0;
  for(g=0;g<8;g=g+1) begin
   group_max=0;
   for(j=0;j<8;j=j+1) begin
    word_abs={1'b0,x_flat[(g*8+j)*32+:31]};
    if(word_abs[30:23]==0) word_abs=0;
    if(word_abs>group_max) group_max=word_abs;
   end
   if(group_max==0) offset_flat[g*5+:5]=0;
   else begin
    diff=row_max[30:23]-group_max[30:23]-(group_max[22:0]>row_max[22:0]);
    if(diff<0) diff=0;
    if(diff>31) diff=31;
    offset_flat[g*5+:5]=diff[4:0];
   end
  end
 end
endmodule
