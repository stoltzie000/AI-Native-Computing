`timescale 1ns/1ps
module tb_qact_serial_abort;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,start=0;reg [2047:0] x_flat='x;
 reg [31:0] row_inverse=32'hffffffff;
 wire ready,done;wire [511:0] q_flat;wire [39:0] offset_flat;
 reg [31:0] xmem[0:2047],imem[0:31];
 reg [7:0] qexpect[0:2047],dexpect[0:255];
 string folder;integer i;
 qact_row_scaled_serial dut(.*);
 task automatic launch(input integer row);
  begin
   wait(ready);@(negedge clk);#1;
   for(i=0;i<64;i=i+1)x_flat[i*32+:32]=xmem[row*64+i];
   row_inverse=imem[row];start=1;
   @(negedge clk);#1;start=0;x_flat='1;row_inverse=0;
  end
 endtask
 task automatic finish(input integer row);
  integer k;
  begin
   wait(done);#1;
   if(!ready)$fatal(1,"ready missing on completion");
   for(k=0;k<64;k=k+1)
    if(q_flat[k*8+:8]!==qexpect[row*64+k])
     $fatal(1,"recovery quant mismatch row=%0d elem=%0d",row,k);
   for(k=0;k<8;k=k+1)
    if(offset_flat[k*5+:5]!==dexpect[row*8+k])
     $fatal(1,"recovery offset mismatch row=%0d group=%0d",row,k);
   @(posedge clk);#1;
   if(done)$fatal(1,"duplicate completion");
  end
 endtask
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing folder");
  $readmemh({folder,"/x.hex"},xmem);$readmemh({folder,"/inv.hex"},imem);
  $readmemh({folder,"/q.hex"},qexpect);$readmemh({folder,"/d.hex"},dexpect);
  repeat(3)@(negedge clk);#1;rst_n=1;
  launch(1);
  wait(dut.state==2'd2 && dut.idx==16);
  @(negedge clk);#1;rst_n=0;#1;
  if(!ready || done || q_flat!==0 || offset_flat!==0)
   $fatal(1,"aborted output survived reset");
  repeat(3)@(negedge clk);#1;rst_n=1;
  repeat(3)@(negedge clk);
  if(done || !ready)$fatal(1,"stale done after reset");
  launch(3);
  wait(dut.state==2'd2 && dut.idx==10);
  @(negedge clk);#1;start=1;
  @(negedge clk);#1;start=0;
  finish(3);
  launch(1);
  finish(1);
  $display("PASS_QACT_SERIAL_RESET aborted=1 completed=2 stale=0");
  $finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
