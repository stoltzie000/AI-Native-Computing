`timescale 1ns/1ps
module tb_qact_group_offset_hier;
 reg [31:0] words[0:63];
 reg [4:0] expected[0:7];
 wire [2047:0] x_flat;
 wire [39:0] offset_flat;
 string case_dir;
 genvar i;
 generate for(i=0;i<64;i=i+1) begin: LANE
  assign x_flat[i*32+:32]=words[i];
 end endgenerate
 qact_group_offset_hier dut(.x_flat(x_flat),.offset_flat(offset_flat));
 integer k;
 initial begin
  if(!$value$plusargs("case=%s",case_dir)) $fatal(1,"missing case");
  $readmemh({case_dir,"/x.hex"},words);
  $readmemh({case_dir,"/d.hex"},expected);
  #10;
  for(k=0;k<8;k=k+1)
   if(offset_flat[k*5+:5]!==expected[k])
    $fatal(1,"offset mismatch case=%s group=%0d actual=%0d expected=%0d",case_dir,k,offset_flat[k*5+:5],expected[k]);
  $display("PASS_QACT_OFFSET_HIER_RTL case=%s groups=8",case_dir);
  $finish;
 end
endmodule
