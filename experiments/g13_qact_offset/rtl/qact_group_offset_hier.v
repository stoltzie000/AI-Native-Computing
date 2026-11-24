`timescale 1ns/1ps
// Hierarchically reuse group maxima for whole-row offset calculation.
// Mathematical contract identical to qact_group_offset, no QACT reciprocal or quantizer.
module qact_group_offset_hier(input wire [2047:0] x_flat, output reg [39:0] offset_flat);
 reg [31:0] max_group[0:7];
 reg [31:0] row_max,word_abs;
 integer g,j,diff;
 always @* begin
  for(g=0;g<8;g=g+1) begin
   max_group[g]=0;
   for(j=0;j<8;j=j+1) begin
    word_abs={1'b0,x_flat[(g*8+j)*32+:31]};
    if(word_abs[30:23]==0)word_abs=0;
    if(word_abs>max_group[g])max_group[g]=word_abs;
   end
  end
  row_max=0;
  for(g=0;g<8;g=g+1)
   if(max_group[g]>row_max)row_max=max_group[g];
  offset_flat=0;
  for(g=0;g<8;g=g+1) begin
   if(max_group[g]==0)offset_flat[g*5+:5]=0;
   else begin
    diff=row_max[30:23]-max_group[g][30:23]-
           (max_group[g][22:0]>row_max[22:0]);
    if(diff<0)diff=0;
    if(diff>31)diff=31;
    offset_flat[g*5+:5]=diff[4:0];
   end
  end
 end
endmodule
