`timescale 1ns/1ps
module tb_qact_row_clocked_original;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,start=0;reg [2047:0] x_flat='x;
 wire ready,done;wire [511:0] q_flat;wire [39:0] offset_flat;
 wire [31:0] row_scale,row_inverse;
 reg [31:0] x_mem[0:2047],scale_mem[0:31],inv_mem[0:31];
 reg [7:0] q_mem[0:2047],d_mem[0:255];
 integer row,i,cycles,special_count=0,normal_count=0;
 string folder;
 qact_row_clocked_original dut(.*);
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing fixture");
  $readmemh({folder,"/x.hex"},x_mem);
  $readmemh({folder,"/scale.hex"},scale_mem);
  $readmemh({folder,"/inv.hex"},inv_mem);
  $readmemh({folder,"/q.hex"},q_mem);
  $readmemh({folder,"/d.hex"},d_mem);
  repeat(3)@(negedge clk);#1;rst_n=1;
  for(row=0;row<32;row=row+1)begin
   @(negedge clk);#1;
   if(!ready || done)$fatal(1,"not idle");
   for(i=0;i<64;i=i+1)x_flat[i*32+:32]=x_mem[row*64+i];
   start=1;
   @(posedge clk);#1;start=0;x_flat='1;
   cycles=0;
   while(!done && cycles<120)begin @(posedge clk);#1;cycles=cycles+1;end
   if(!done || !ready)$fatal(1,"no completion row=%0d cycles=%0d",row,cycles);
   if(inv_mem[row]==0 && scale_mem[row]==0)begin
    special_count=special_count+1;
    if(cycles!=77)$fatal(1,"zero-row latency mismatch %0d",cycles);
   end else begin
    normal_count=normal_count+1;
    if(cycles!=88)$fatal(1,"normal-row latency mismatch row=%0d cycles=%0d",row,cycles);
   end
   if(row_scale!==scale_mem[row] || row_inverse!==inv_mem[row])
    $fatal(1,"QACT scale/inverse mismatch row=%0d scale=%h want=%h inv=%h want=%h",
      row,row_scale,scale_mem[row],row_inverse,inv_mem[row]);
   for(i=0;i<64;i=i+1)if(q_flat[i*8+:8]!==q_mem[row*64+i])
    $fatal(1,"Q8 mismatch row=%0d elem=%0d got=%h want=%h",
      row,i,q_flat[i*8+:8],q_mem[row*64+i]);
   for(i=0;i<8;i=i+1)
    if(offset_flat[i*5+:5]!==d_mem[row*8+i][4:0])
     $fatal(1,"group offset mismatch row=%0d group=%0d",row,i);
   @(posedge clk);#1;
   if(done)$fatal(1,"duplicate completion");
  end
  @(negedge clk);#1;rst_n=0;#1;
  if(!ready || done || row_scale!==0 || row_inverse!==0)
    $fatal(1,"reset contract failure");
  $display("PASS_QACT_CLOCKED_ORIGINAL rows=32 q=2048 offsets=256 normal=%0d special=%0d",normal_count,special_count);
  $finish;
 end
 initial begin #2000000;$fatal(1,"watchdog");end
endmodule
