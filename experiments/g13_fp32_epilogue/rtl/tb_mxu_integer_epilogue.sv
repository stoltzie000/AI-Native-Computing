`timescale 1ns/1ps
module tb_mxu_integer_epilogue;
  reg [239:0] acc_flat='x;
  reg [159:0] weight_scale_flat='x;
  reg [31:0] activation_scale='x;
  wire [159:0] result_flat;
  reg [47:0] input_acc[0:4];
  reg [31:0] weight_scale[0:4], expected[0:4], scale[0:0];
  integer k;
  string case_dir;

  mxu_integer_epilogue dut(
    .acc_flat(acc_flat),.weight_scale_flat(weight_scale_flat),
    .activation_scale(activation_scale),.result_flat(result_flat)
  );
  initial begin
    if(!$value$plusargs("case=%s",case_dir))
      $fatal(1,"missing +case= fixture path");
    $readmemh({case_dir,"/expected.hex"},input_acc);
    $readmemh({case_dir,"/wscale.hex"},weight_scale);
    $readmemh({case_dir,"/ascale.hex"},scale);
    $readmemh({case_dir,"/expected_fp32.hex"},expected);
    for(k=0;k<5;k=k+1) begin
      acc_flat[k*48+:48]=input_acc[k];
      weight_scale_flat[k*32+:32]=weight_scale[k];
    end
    activation_scale=scale[0];
    #5;
    for(k=0;k<5;k=k+1)
      if(result_flat[k*32+:32] !== expected[k])
        $fatal(1,"epilogue FP32 mismatch idx=%0d got=%h want=%h int=%h",
               k,result_flat[k*32+:32],expected[k],input_acc[k]);
    $display("PASS_FP32_EPILOGUE_ISA case=%s outputs=5",case_dir);
    $finish;
  end
endmodule
