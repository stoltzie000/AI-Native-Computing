`timescale 1ns/1ps
module tb_fp32_result_writeback;
 reg clk=0; always #5 clk=~clk;
 reg rst_n=0,result_valid=0,write_ready=0;
 reg [159:0] result_data=0;reg [63:0] result_addr=0;
 wire result_ready,write_valid,done; wire [511:0] write_data;
 wire [63:0] write_addr,write_mask;
 fp32_result_writeback dut(.*);
 integer j,k,accepted=0;reg [159:0] expected;
 always @(posedge clk) if(write_valid && write_ready) accepted=accepted+1;
 initial begin
  repeat(2) @(negedge clk);rst_n=1; #1; // allow continuous ready assignment to settle
  for(j=0;j<64;j=j+1) begin
   expected={32'h12345678+j,32'habcdef01-j,32'h80000000+j,32'h7fc00000,32'h3f800000+j};
   result_data=expected;result_addr=64'h1000+64*j;result_valid=1;
   if(!result_ready) $fatal(1,"input not ready");
   @(negedge clk);result_valid=0;result_data=~expected;result_addr=0;
   for(k=0;k<1+j%9;k=k+1) begin
    if(!write_valid || result_ready || done || write_data!=={352'b0,expected} ||
       write_addr!==(64'h1000+64*j) || write_mask!==64'hfffff)
      $fatal(1,"stalled payload mismatch");
    @(negedge clk);
   end
   write_ready=1;@(negedge clk);write_ready=0;
   if(!done || write_valid || !result_ready || accepted!=j+1) $fatal(1,"completion mismatch");
   @(negedge clk);if(done) $fatal(1,"duplicate done");
  end
  result_valid=1;@(negedge clk);result_valid=0;
  if(!write_valid) $fatal(1,"abort setup");
  rst_n=0;#1;if(write_valid || done) $fatal(1,"reset failed");
  @(negedge clk);rst_n=1;repeat(2) @(negedge clk);
  if(write_valid || done || accepted!=64) $fatal(1,"stale write");
  $display("PASS_WRITEBACK jobs=64 useful_bytes=1280 reset_abort=1");$finish;
 end
 initial begin #100000;$fatal(1,"watchdog");end
endmodule
