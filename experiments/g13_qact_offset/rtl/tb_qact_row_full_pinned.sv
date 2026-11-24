`timescale 1ns/1ps
module tb_qact_row_full_pinned;
 reg [2047:0] x_flat='x;
 wire [511:0] q_flat;
 wire [39:0] offset_flat;
 wire [31:0] row_scale,row_inverse;
 reg [31:0] x_mem[0:2047],inv_expect[0:31],scale_expect[0:31];
 reg [7:0] q_expect[0:2047],d_expect[0:255];
 integer row,i;string folder;
 qact_row_full_pinned dut(.*);
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing fixtures");
  $readmemh({folder,"/x.hex"},x_mem);
  $readmemh({folder,"/inv.hex"},inv_expect);
  $readmemh({folder,"/scale.hex"},scale_expect);
  $readmemh({folder,"/q.hex"},q_expect);
  $readmemh({folder,"/d.hex"},d_expect);
  for(row=0;row<32;row=row+1)begin
   for(i=0;i<64;i=i+1)x_flat[i*32+:32]=x_mem[row*64+i];
   #10;
   if(row_inverse!==inv_expect[row] || row_scale!==scale_expect[row])
     $fatal(1,"row reciprocal or scale mismatch row=%0d inv=%h wanted=%h scale=%h wanted=%h",
     row,row_inverse,inv_expect[row],row_scale,scale_expect[row]);
   for(i=0;i<64;i=i+1)
     if(q_flat[i*8+:8]!==q_expect[row*64+i])
       $fatal(1,"QACT mismatch row=%0d lane=%0d got=%h want=%h",
         row,i,q_flat[i*8+:8],q_expect[row*64+i]);
   for(i=0;i<8;i=i+1)
     if(offset_flat[i*5+:5]!==d_expect[row*8+i])
       $fatal(1,"offset mismatch row=%0d group=%0d",row,i);
  end
  $display("PASS_FULL_QACT_PINNED_RTL rows=32 q=2048 offsets=256 scales=32 inverses=32");
  $finish;
 end
endmodule
