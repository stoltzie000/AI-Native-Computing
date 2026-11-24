`timescale 1ns/1ps
module tb_fp32_arithmetic;
  reg [31:0] a='x,b='x;
  wire [31:0] result;
  reg [47:0] n='x;
  wire [31:0] conv;
  reg [31:0] aa[0:2047],bb[0:2047],mm[0:2047],ii_want[0:2047];
  reg [47:0] ii[0:2047];
  integer idx;
  string random_dir;

  fp32_mul_ftz dut_mul(.a(a),.b(b),.y(result));
  int48_to_fp32_rne dut_int(.integer_in(n),.y(conv));
  initial begin
    if(!$value$plusargs("random=%s",random_dir))
      $fatal(1,"missing random fixture path");
    $readmemh({random_dir,"/mul_a.hex"},aa);
    $readmemh({random_dir,"/mul_b.hex"},bb);
    $readmemh({random_dir,"/mul_expected.hex"},mm);
    $readmemh({random_dir,"/int48_in.hex"},ii);
    $readmemh({random_dir,"/int48_expected.hex"},ii_want);
    for(idx=0;idx<2048;idx=idx+1) begin
      a=aa[idx];b=bb[idx];n=ii[idx];#1;
      if(result!==mm[idx])
        $fatal(1,"FP32 FTZ mul mismatch row=%0d a=%h b=%h got=%h expected=%h",
               idx,a,b,result,mm[idx]);
      if(conv!==ii_want[idx])
        $fatal(1,"int48 RNE mismatch row=%0d integer=%h got=%h expected=%h",
               idx,n,conv,ii_want[idx]);
    end
    $display("PASS_FP32_ARITHMETIC mul=2048 int48=2048");
    $finish;
  end
endmodule
