`timescale 1ns/1ps
// Signed 48-bit exact accumulator -> binary32 round-to-nearest-ties-even.
// Pure combinational bit arithmetic, no host $realtobits or non-synth constructs.
module int48_to_fp32_rne(
  input wire [47:0] integer_in,
  output reg [31:0] y
);
  reg [47:0] magnitude;
  reg [47:0] quotient,remainder,halfway;
  reg [24:0] significand;
  integer top,shift,exp_biased,i;
  always @* begin
    magnitude=integer_in[47]? (~integer_in+48'd1):integer_in;
    top=-1;shift=0;exp_biased=0;
    quotient=0;remainder=0;halfway=0;significand=0;
    for(i=0;i<48;i=i+1)
      if(magnitude[i]) top=i;
    if(top<0) y=32'd0;
    else begin
      shift=top-23;
      if(shift<=0)
        significand=magnitude << (-shift);
      else begin
        quotient=magnitude >> shift;
        remainder=magnitude & ((48'd1 << shift)-48'd1);
        halfway=48'd1 << (shift-1);
        significand=quotient[24:0]+
          ((remainder>halfway) ||
           ((remainder==halfway) && quotient[0]));
      end
      exp_biased=top+127;
      if(significand[24]) begin
        significand=significand >> 1;
        exp_biased=exp_biased+1;
      end
      y={integer_in[47],exp_biased[7:0],significand[22:0]};
    end
  end
endmodule
