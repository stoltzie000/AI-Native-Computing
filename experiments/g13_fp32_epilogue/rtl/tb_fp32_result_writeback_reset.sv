`timescale 1ns/1ps
module tb_fp32_result_writeback_reset;
  reg clk=0;always #5 clk=~clk;
  reg rst_n=0,result_valid=0,write_ready=0;
  reg [159:0] result_data=0;reg [63:0] result_addr=0;
  wire result_ready,write_valid,done;wire [511:0] write_data;
  wire [63:0] write_addr,write_mask;
  integer accepted=0;
  fp32_result_writeback dut(.*);
  always @(posedge clk) if(write_valid && write_ready) accepted=accepted+1;
  task automatic send(input [159:0] data,input [63:0] addr);
    begin
      @(negedge clk); #1;
      if(!result_ready || done || write_valid) $fatal(1,"not ready before input");
      result_data=data;result_addr=addr;result_valid=1;
      @(negedge clk);result_valid=0;result_data=~data;result_addr=0;
      #1;
      if(!write_valid || write_data!=={352'b0,data} || write_addr!==addr || write_mask!==64'hfffff)
        $fatal(1,"capture mismatch");
    end
  endtask
  task automatic stalled(input [159:0] data,input [63:0] addr,input integer cycles);
    integer i;
    begin
      for(i=0;i<cycles;i=i+1) begin
        @(negedge clk);#1;
        if(!write_valid || result_ready || done || write_ready ||
           write_data!=={352'b0,data} || write_addr!==addr || write_mask!==64'hfffff)
           $fatal(1,"output changed while stalled");
      end
    end
  endtask
  task automatic take_write(input integer expected_count);
    begin
      @(negedge clk);write_ready=1;
      @(posedge clk);#1;
      if(accepted!=expected_count || !done || write_valid || !result_ready)
         $fatal(1,"acceptance/completion mismatch");
      @(negedge clk);write_ready=0;
      @(posedge clk);#1;
      if(done || write_valid) $fatal(1,"duplicate write completion");
    end
  endtask
  initial begin
    repeat(3) @(negedge clk);#1;rst_n=1;#1;
    send(160'h000000013f8000007fc000008000000012345678,64'h1000);
    stalled(160'h000000013f8000007fc000008000000012345678,64'h1000,8);
    @(negedge clk);#1;rst_n=0;#1;
    if(write_valid || done || result_ready || accepted!=0)
      $fatal(1,"stalled write not cancelled on async reset");
    repeat(3) @(negedge clk);#1;rst_n=1;#1;
    if(!result_ready || write_valid || done) $fatal(1,"stale write after reset");
    repeat(5) @(negedge clk);
    if(accepted!=0 || write_valid || done) $fatal(1,"write resurrected");
    send(160'h0123456789abcdef00112233445566778899aabb,64'h2000);
    stalled(160'h0123456789abcdef00112233445566778899aabb,64'h2000,5);
    take_write(1);
    @(negedge clk);#1;rst_n=0;#1;
    if(write_valid || done) $fatal(1,"accepted write replayed after reset");
    repeat(2) @(negedge clk);#1;rst_n=1;#1;
    send(160'hffffffff00000000000000017f8000003f800000,64'h3000);
    stalled(160'hffffffff00000000000000017f8000003f800000,64'h3000,3);
    take_write(2);
    if(accepted!=2) $fatal(1,"total accepted count wrong");
    $display("PASS_WRITEBACK_RESET cancelled=1 accepted=2 stale=0");$finish;
  end
  initial begin #100000;$fatal(1,"watchdog");end
endmodule
