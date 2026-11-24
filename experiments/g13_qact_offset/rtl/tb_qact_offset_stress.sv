`timescale 1ns/1ps
module tb_qact_offset_stress;
reg [2047:0] x_flat='x;
wire [39:0] original,optimized;
reg [31:0] words[0:32767];reg [4:0] expected[0:4095];
integer row,k;string folder;
qact_group_offset old_dut(.x_flat(x_flat),.offset_flat(original));
qact_group_offset_hier new_dut(.x_flat(x_flat),.offset_flat(optimized));
initial begin
 if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing folder");
 $readmemh({folder,"/x.hex"},words);$readmemh({folder,"/d.hex"},expected);
 for(row=0;row<512;row=row+1) begin
  for(k=0;k<64;k=k+1)x_flat[k*32+:32]=words[row*64+k];
  #1;
  for(k=0;k<8;k=k+1)
   if(original[k*5+:5]!==expected[row*8+k] || optimized[k*5+:5]!==expected[row*8+k])
    $fatal(1,"stress mismatch row=%0d group=%0d old=%0d hier=%0d want=%0d",row,k,original[k*5+:5],optimized[k*5+:5],expected[row*8+k]);
 end
 $display("PASS_QACT_OFFSET_STRESS cases=512 offsets=4096");$finish;
end
endmodule
