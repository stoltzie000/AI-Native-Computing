`timescale 1ns/1ps
module tb_qact_row_scaled_serial;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,start=0;
 reg [2047:0] x_flat='x;
 reg [31:0] row_inverse=32'hffffffff;
 wire ready,done;wire [511:0] q_flat;wire [39:0] offset_flat;
 reg [31:0] xmem[0:2047],imem[0:31];
 reg [7:0] qexpect[0:2047],dexpect[0:255];
 string folder;integer row,i,active_cycles=0;
 qact_row_scaled_serial dut(.*);
 always @(posedge clk)if(rst_n && !ready) active_cycles=active_cycles+1;
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing folder");
  $readmemh({folder,"/x.hex"},xmem);$readmemh({folder,"/inv.hex"},imem);
  $readmemh({folder,"/q.hex"},qexpect);$readmemh({folder,"/d.hex"},dexpect);
  repeat(3)@(negedge clk);#1;rst_n=1;
  for(row=0;row<32;row=row+1)begin
   wait(ready);@(negedge clk);#1;
   for(i=0;i<64;i=i+1)x_flat[i*32+:32]=xmem[row*64+i];
   row_inverse=imem[row];start=1;active_cycles=0;
   @(negedge clk);#1;start=0;x_flat='1;row_inverse=0;
   wait(done);#1;
   if(!ready || active_cycles!=73)
    $fatal(1,"serial completion timing row=%0d cycles=%0d",row,active_cycles);
   for(i=0;i<64;i=i+1)if(q_flat[i*8+:8]!==qexpect[row*64+i])
    $fatal(1,"serial QACT mismatch row=%0d elem=%0d got=%h want=%h",row,i,q_flat[i*8+:8],qexpect[row*64+i]);
   for(i=0;i<8;i=i+1)if(offset_flat[i*5+:5]!==dexpect[row*8+i])
    $fatal(1,"serial offset mismatch row=%0d group=%0d",row,i);
   @(posedge clk);#1;
   if(done)$fatal(1,"duplicate done pulse");
  end
  @(negedge clk);#1;rst_n=0;#1;
  if(done || !ready || q_flat!==0)$fatal(1,"reset did not clear outputs");
  $display("PASS_QACT_SERIAL rows=32 q=2048 offsets=256 cycles=73");
  $finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
