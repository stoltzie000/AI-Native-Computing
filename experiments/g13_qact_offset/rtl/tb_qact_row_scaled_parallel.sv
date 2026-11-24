`timescale 1ns/1ps
module tb_qact_row_scaled_parallel;
 reg [2047:0] x_flat='x;reg [31:0] row_inverse=32'hffffffff;
 wire [511:0] q_flat;wire [39:0] offset_flat;
 reg [31:0] x_mem[0:2047],inv_mem[0:31];
 reg [7:0] q_expect[0:2047],d_expect[0:255];
 integer row,i;string folder;
 qact_row_scaled_parallel dut(.x_flat(x_flat),.row_inverse(row_inverse),.q_flat(q_flat),.offset_flat(offset_flat));
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing folder");
  $readmemh({folder,"/x.hex"},x_mem);$readmemh({folder,"/inv.hex"},inv_mem);
  $readmemh({folder,"/q.hex"},q_expect);$readmemh({folder,"/d.hex"},d_expect);
  for(row=0;row<32;row=row+1)begin
   for(i=0;i<64;i=i+1)x_flat[i*32+:32]=x_mem[row*64+i];
   row_inverse=inv_mem[row];#10;
   for(i=0;i<64;i=i+1) if(q_flat[i*8+:8]!==q_expect[row*64+i])
     $fatal(1,"row QACT mismatch row=%0d element=%0d got=%h want=%h",row,i,q_flat[i*8+:8],q_expect[row*64+i]);
   for(i=0;i<8;i=i+1)if(offset_flat[i*5+:5]!==d_expect[row*8+i])
     $fatal(1,"row offset mismatch row=%0d group=%0d",row,i);
  end
  $display("PASS_QACT_ROW_SCALED_RTL rows=32 q=2048 offsets=256");
  $finish;
 end
endmodule
