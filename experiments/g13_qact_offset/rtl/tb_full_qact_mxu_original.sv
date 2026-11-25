`timescale 1ns/1ps
module tb_full_qact_mxu_original;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,start=0;
 reg [2047:0] x_flat='x;
 reg [2559:0] w_flat='x;
 reg [79:0] dw_flat='x;
 reg [159:0] weight_scale_flat='x;
 wire ready,done;
 wire [239:0] acc_flat;
 wire [159:0] fp32_flat;
 wire [511:0] q_flat;
 wire [39:0] offset_flat;
 wire [31:0] activation_scale;
 wire [15:0] dropped_groups,consumed_groups;
 reg [31:0] xmem[0:63],wscale[0:4],ascale[0:0],fp_expect[0:4];
 reg [7:0] wmem[0:319],dwmem[0:9],q_expect[0:63],d_expect[0:7];
 reg [47:0] acc_expect[0:4];
 reg [15:0] drops_expect[0:0];
 integer k;
 string folder;
 qact_mxu_full_original dut(.*);
 initial begin
  if(!$value$plusargs("case=%s",folder))$fatal(1,"case fixture missing");
  $readmemh({folder,"/x_raw.hex"},xmem);
  $readmemh({folder,"/w.hex"},wmem);
  $readmemh({folder,"/dw.hex"},dwmem);
  $readmemh({folder,"/wscale.hex"},wscale);
  $readmemh({folder,"/ascale.hex"},ascale);
  $readmemh({folder,"/q.hex"},q_expect);
  $readmemh({folder,"/da.hex"},d_expect);
  $readmemh({folder,"/expected.hex"},acc_expect);
  $readmemh({folder,"/expected_fp32.hex"},fp_expect);
  $readmemh({folder,"/drops.hex"},drops_expect);
  for(k=0;k<64;k=k+1)x_flat[k*32+:32]=xmem[k];
  for(k=0;k<320;k=k+1)w_flat[k*8+:8]=wmem[k];
  for(k=0;k<10;k=k+1)dw_flat[k*8+:8]=dwmem[k];
  for(k=0;k<5;k=k+1)weight_scale_flat[k*32+:32]=wscale[k];
  repeat(3)@(negedge clk);#1;rst_n=1;
  @(negedge clk);start=1;
  @(negedge clk);start=0;
  x_flat='1;w_flat='0;dw_flat='1;weight_scale_flat='0;
  wait(done);#1;
  if(!ready || consumed_groups!==16'd40 || dropped_groups!==drops_expect[0])
   $fatal(1,"MXU counters mismatch got groups=%0d drops=%0d",consumed_groups,dropped_groups);
  if(activation_scale!==ascale[0])$fatal(1,"QACT scale mismatch");
  for(k=0;k<64;k=k+1)if(q_flat[k*8+:8]!==q_expect[k])
    $fatal(1,"QACT Q mismatch lane=%0d",k);
  for(k=0;k<8;k=k+1)if(offset_flat[k*5+:5]!==d_expect[k][4:0])
    $fatal(1,"QACT offset mismatch group=%0d",k);
  for(k=0;k<5;k=k+1)begin
   if(acc_flat[k*48+:48]!==acc_expect[k])
    $fatal(1,"integer accumulator mismatch out=%0d",k);
   if(fp32_flat[k*32+:32]!==fp_expect[k])
    $fatal(1,"FP32 epilogue mismatch out=%0d got=%h want=%h",k,fp32_flat[k*32+:32],fp_expect[k]);
  end
  @(posedge clk);#1;
  if(done)$fatal(1,"duplicate completion");
  $display("PASS_FULL_QACT_MXU_ORIGINAL case=%s q=64 offsets=8 outputs=5 groups=40",folder);
  $finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
