`timescale 1ns/1ps
module tb_fp32_addsub_ftz #(parameter BALANCED_NORMALIZE=0);
 reg [31:0] a='x,b='x;
 reg subtract='x;
 wire [31:0] y;
 reg [31:0] avec[0:8191],bvec[0:8191],expected[0:8191];
 reg [0:0] operations[0:8191];
 integer i;string folder;
 fp32_addsub_ftz #(.BALANCED_NORMALIZE(BALANCED_NORMALIZE)) dut(.a(a),.b(b),.subtract(subtract),.y(y));
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing fixture path");
  $readmemh({folder,"/a.hex"},avec);$readmemh({folder,"/b.hex"},bvec);
  $readmemh({folder,"/op.hex"},operations);
  $readmemh({folder,"/expected.hex"},expected);
  for(i=0;i<8192;i=i+1)begin
   a=avec[i];b=bvec[i];subtract=operations[i];#1;
   if(y!==expected[i])
    $fatal(1,"FP32 addsub mismatch i=%0d a=%h b=%h sub=%b actual=%h want=%h",i,a,b,subtract,y,expected[i]);
  end
  $display("PASS_FP32_ADDSUB_RTL vectors=8192 add=4096 sub=4096");
  $finish;
 end
endmodule
