`timescale 1ns/1ps
// Original research IEEE binary32 add/sub RNE with FTZ inputs/results.
// Exception handling: canonical qNaN, infinity saturation, IEEE signed zeros.
module fp32_addsub_ftz(input wire [31:0] a,b,input wire subtract,output reg [31:0] y);
 function [26:0] shr_jam;
  input [26:0] v;
  input integer n;
  reg [26:0] mask;
  begin
   if(n<=0)shr_jam=v;
   else if(n>=27)shr_jam={26'b0,(|v)};
   else begin
    mask=(27'd1<<n)-1'b1;
    shr_jam=(v>>n)|{26'b0,(|(v&mask))};
   end
  end
 endfunction
 reg sa,sb,so;
 reg [7:0] ea,eb;
 reg [22:0] fa,fb;
 reg [26:0] ma,mb,big_sig,small_sig,sig;
 reg [27:0] total;
 reg [24:0] rounded;
 reg [23:0] mantissa;
 integer exponent,shift,k;
 always @* begin
  sa=a[31];sb=b[31]^subtract;
  ea=a[30:23];eb=b[30:23];fa=a[22:0];fb=b[22:0];
  ma=0;mb=0;big_sig=0;small_sig=0;sig=0;total=0;rounded=0;mantissa=0;
  so=0;exponent=0;shift=0;y=0;
  if((ea==255&&fa!=0)||(eb==255&&fb!=0))y=32'h7fc00000;
  else if(ea==255||eb==255)begin
   if(ea==255&&eb==255&&sa!=sb)y=32'h7fc00000;
   else if(ea==255)y={sa,8'hff,23'd0};
   else y={sb,8'hff,23'd0};
  end else if(ea==0&&eb==0) y={(sa&sb),31'd0};
  else if(ea==0)y={sb,eb,fb};
  else if(eb==0)y={sa,ea,fa};
  else begin
   ma={1'b1,fa,3'b000};mb={1'b1,fb,3'b000};
   if(ea>eb || (ea==eb&&fa>=fb))begin
    exponent=ea;so=sa;big_sig=ma;shift=ea-eb;
    small_sig=shr_jam(mb,shift);
   end else begin
    exponent=eb;so=sb;big_sig=mb;shift=eb-ea;
    small_sig=shr_jam(ma,shift);
   end
   if(sa==sb)begin
    total={1'b0,big_sig}+{1'b0,small_sig};
    if(total[27])begin
     sig=shr_jam(total[26:0],1);
     sig[26]=total[27];exponent=exponent+1;
    end else sig=total[26:0];
   end else begin
    sig=big_sig-small_sig;
    if(sig==0)begin so=0;exponent=0;end
    else begin
     for(k=0;k<27;k=k+1)
      if(!sig[26]&&exponent>0)begin sig=sig<<1;exponent=exponent-1;end
    end
   end
   if(sig==0)y=32'h00000000;
   else if(exponent<=0)y={so,31'd0};
   else begin
    mantissa=sig[26:3];
    rounded={1'b0,mantissa}+((sig[2])&&(sig[1]||sig[0]||sig[3]));
    if(rounded[24])begin exponent=exponent+1;rounded=rounded>>1;end
    if(exponent>=255)y={so,8'hff,23'd0};
    else y={so,exponent[7:0],rounded[22:0]};
   end
  end
 end
endmodule
