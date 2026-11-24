module qact_q8_rne(input wire [31:0] x,output reg signed [7:0] q);
reg sign;reg [7:0] ex;reg [22:0] frac;reg [23:0] m;
reg [23:0] integer_part,remain,half,mask;integer shift,rounded;
always @* begin
 sign=x[31];ex=x[30:23];frac=x[22:0];m={1'b1,frac};
 integer_part=0;remain=0;half=0;mask=0;shift=0;rounded=0;q=0;
 if(ex==255) begin
  if(frac!=0) q=0;else if(sign) q=-8'sd127;else q=8'sd127;
 end else if(ex==0) q=0;
 else if(ex>=134) begin if(sign) q=-8'sd127;else q=8'sd127;end
 else if(ex<126) q=0;
 else begin
  shift=150-ex;integer_part=m>>shift;
  mask=(24'd1<<shift)-24'd1;remain=m&mask;half=24'd1<<(shift-1);
  rounded=integer_part+((remain>half)||((remain==half)&&integer_part[0]));
  if(rounded>127) rounded=127;
  if(sign) q=-rounded;else q=rounded;
 end
end
endmodule
