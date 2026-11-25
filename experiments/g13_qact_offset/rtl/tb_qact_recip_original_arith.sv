`timescale 1ns/1ps
module tb_qact_recip_original_arith;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,start=0;reg [31:0] x='x;
 wire ready,done;wire [31:0] result;
 reg [31:0] xvec[0:2047],expected_words[0:2047];
 integer i,cycles,special,normal;string folder;
 qact_recip_serial_original_arith dut(.*);
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"fixtures");
  $readmemh({folder,"/recip-input.hex"},xvec);
  $readmemh({folder,"/recip-expected.hex"},expected_words);
  repeat(3)@(negedge clk);#1;rst_n=1;
  special=0;normal=0;
  for(i=0;i<2048;i=i+1)begin
   @(negedge clk);#1;
   if(!ready||done)$fatal(1,"not ready i=%0d",i);
   x=xvec[i];start=1;
   @(posedge clk);#1;
   start=0;x=~xvec[i];
   cycles=0;
   if(xvec[i][30:23]==0 || xvec[i][30:0]>=32'h7e800000)begin
    special=special+1;
    if(!done || result!==expected_words[i])$fatal(1,"special mismatch i=%0d",i);
   end else begin
    normal=normal+1;
    while(!done && cycles<20)begin @(posedge clk);#1;cycles=cycles+1;end
    if(!done || cycles!=11 || result!==expected_words[i])
     $fatal(1,"recip mismatch i=%0d x=%h got=%h expected=%h cycles=%0d",
        i,xvec[i],result,expected_words[i],cycles);
   end
   @(posedge clk);#1;
   if(done || !ready)$fatal(1,"duplicate done or stuck i=%0d",i);
  end
  @(negedge clk);#1;rst_n=0;#1;
  if(done||!ready||result!==0)$fatal(1,"reset failed");
  $display("PASS_RECIP_ORIGINAL_ARITH_RTL vectors=2048 normal=%0d special=%0d cycles_normal=11",normal,special);
  $finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
