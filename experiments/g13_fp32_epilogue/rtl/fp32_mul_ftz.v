`timescale 1ns/1ps
// Bit-exact scalar binary32 multiply with FTZ inputs and result.
// RNE rounding, canonical qNaN, signed zero. Combinational RTL; no timing claim.
// Independent Python word()/ftz()/mul() is differential oracle.
module fp32_mul_ftz(
  input wire [31:0] a,b,
  output reg [31:0] y
);
  reg sign;
  reg [7:0] ea,eb;
  reg [22:0] fa,fb;
  reg [23:0] ma,mb;
  reg [47:0] product;
  reg [24:0] rounded,underflow_round;
  integer exp_biased;
  integer normal_shift;

  function [24:0] round_u48;
    input [47:0] n;
    input integer shift;
    reg [47:0] quotient, remainder, halfway, mask;
    begin
      quotient=0;remainder=0;halfway=0;mask=0;
      if(shift<=0) round_u48=n << (-shift);
      else if(shift>48) round_u48=25'd0;
      else begin
        quotient=n >> shift;
        mask=(48'd1 << shift)-48'd1;
        remainder=n & mask;
        halfway=48'd1 << (shift-1);
        round_u48=quotient[24:0]+
              ((remainder>halfway) ||
               ((remainder==halfway) && quotient[0]));
      end
    end
  endfunction

  always @* begin
    sign=a[31]^b[31];
    ea=a[30:23];eb=b[30:23];
    fa=a[22:0];fb=b[22:0];
    ma={1'b1,fa};mb={1'b1,fb};
    product=ma*mb;
    rounded=0;underflow_round=0;exp_biased=0;normal_shift=0;
    if((ea==8'hff && fa!=0) || (eb==8'hff && fb!=0) ||
       (ea==8'hff && eb==0) || (eb==8'hff && ea==0))
      y=32'h7fc00000;
    else if(ea==8'hff || eb==8'hff)
      y={sign,8'hff,23'd0};
    else if(ea==0 || eb==0)
      y={sign,31'd0};
    else begin
      normal_shift=product[47]?24:23;
      exp_biased=ea+eb+(product[47]?1:0)-127;
      rounded=round_u48(product,normal_shift);
      if(rounded[24]) begin
        rounded=rounded >> 1;
        exp_biased=exp_biased+1;
      end
      if(exp_biased>=255)
        y={sign,8'hff,23'd0};
      else if(exp_biased>0)
        y={sign,exp_biased[7:0],rounded[22:0]};
      else begin
        // IEEE rounding may carry a subnormal to the smallest NORMAL.
        // All actual subnormal outputs are then flushed to signed zero.
        underflow_round=round_u48(product,151-ea-eb);
        if(underflow_round>=25'h800000)
          y={sign,8'h01,23'd0};
        else
          y={sign,31'd0};
      end
    end
  end
endmodule
