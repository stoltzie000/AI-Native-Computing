`timescale 1ns/1ps
module tb_qact_recip_ref;
 logic [31:0] x=32'hffffffff;
 wire [31:0] y;
 reg [31:0] words[0:2047],expected[0:2047];
 integer i;string folder;
 qact_recip_pinned_ref dut(.x(x),.y(y));
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing folder");
  $readmemh({folder,"/recip-input.hex"},words);
  $readmemh({folder,"/recip-expected.hex"},expected);
  for(i=0;i<2048;i=i+1)begin
   x=words[i];#1;
   if(y!==expected[i])$fatal(1,"pinned reciprocal mismatch i=%0d x=%h actual=%h expected=%h",i,x,y,expected[i]);
  end
  $display("PASS_PINNED_RECIP_RTL vectors=2048");
  $finish;
 end
endmodule
