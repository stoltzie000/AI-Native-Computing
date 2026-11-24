`timescale 1ns/1ps
module tb_mxu_integer_epilogue_serial;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,start=0;
 reg [239:0] acc_flat='x;
 reg [159:0] weight_scale_flat='x;
 reg [31:0] activation_scale='x;
 wire ready,done;wire [159:0] result_flat;
 reg [47:0] accs[0:4];
 reg [31:0] weights[0:4],expected[0:4],scale[0:0];
 integer i;
 string case_a,case_b;
 mxu_integer_epilogue_serial dut(.*);
 task automatic load_case(input string directory);
  integer k;
  begin
   $readmemh({directory,"/expected.hex"},accs);
   $readmemh({directory,"/wscale.hex"},weights);
   $readmemh({directory,"/ascale.hex"},scale);
   $readmemh({directory,"/expected_fp32.hex"},expected);
   for(k=0;k<5;k=k+1) begin
    acc_flat[k*48+:48]=accs[k];
    weight_scale_flat[k*32+:32]=weights[k];
   end
   activation_scale=scale[0];
  end
 endtask
 task automatic run_job(input string directory,input integer job);
  integer cycles,k;
  begin
   load_case(directory);
   @(negedge clk);#1;
   if(!ready || done) $fatal(1,"not idle");
   start=1;
   @(negedge clk);start=0;
   // Mutation of external buses catches missing input latches.
   acc_flat=~acc_flat;weight_scale_flat=~weight_scale_flat;
   activation_scale=~activation_scale;
   cycles=0;
   while(!done && cycles<20) begin
     @(negedge clk);cycles=cycles+1;
   end
   if(!done || cycles!=11 || !ready) $fatal(1,"serial cycle/ready mismatch %0d",cycles);
   for(k=0;k<5;k=k+1)
    if(result_flat[k*32+:32]!==expected[k])
      $fatal(1,"serial FP32 mismatch job=%0d output=%0d got=%h expected=%h",
        job,k,result_flat[k*32+:32],expected[k]);
   $display("PASS_SERIAL_EPILOGUE job=%0d cycles=%0d outputs=5",job,cycles);
   @(negedge clk);
   if(done) $fatal(1,"duplicate done");
  end
 endtask
 initial begin
  if(!$value$plusargs("case_a=%s",case_a) ||
     !$value$plusargs("case_b=%s",case_b)) $fatal(1,"missing cases");
  repeat(3) @(negedge clk);#1;rst_n=1;
  run_job(case_a,1);run_job(case_b,2);
  $display("PASS_SERIAL_EPILOGUE_SUITE");$finish;
 end
 initial begin #100000;$fatal(1,"watchdog");end
endmodule
