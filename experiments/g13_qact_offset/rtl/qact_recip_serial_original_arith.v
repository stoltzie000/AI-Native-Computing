`timescale 1ns/1ps
// Original reciprocal control plus original FP32 FTZ add/sub and multiplier.
module qact_recip_serial_original_arith #(parameter BALANCED_NORMALIZE=0)(
 input wire clk,rst_n,start,input wire [31:0] x,
 output wire ready,output reg done,output reg [31:0] result
);
 localparam IDLE=4'd0,M1=4'd1,S1=4'd2,M2=4'd3,
            M3=4'd4,S2=4'd5,M4=4'd6,M5=4'd7,
            S3=4'd8,M6=4'd9,ADD=4'd10,FINISH=4'd11;
 reg [3:0] state;
 reg [31:0] a,y,t,magnitude;
 reg sign;
 wire [31:0] m_a=((state==M1)||(state==M3)||(state==M5))?a:
                   ((state==M2)||(state==M4)||(state==M6))?y:32'd0;
 wire [31:0] m_b=((state==M1)||(state==M3)||(state==M5))?y:t;
 wire [31:0] mul_result;
 fp32_mul_ftz multiplication(.a(m_a),.b(m_b),.y(mul_result));
 wire [31:0] sub_a=((state==S1)||(state==S2))?32'h40000000:32'h3f800000;
 wire [31:0] addsub_a=(state==ADD)?t:sub_a;
 wire [31:0] addsub_b=(state==ADD)?y:t;
 wire [31:0] addsub_result;
 fp32_addsub_ftz #(.BALANCED_NORMALIZE(BALANCED_NORMALIZE)) arithmetic(.a(addsub_a),.b(addsub_b),
   .subtract(state!=ADD),.y(addsub_result));
 assign ready=state==IDLE;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;done<=0;result<=0;
   a<=0;y<=0;t<=0;magnitude<=0;sign<=0;
  end else begin
   done<=0;
   case(state)
    IDLE:if(start)begin
     sign<=x[31];magnitude<=(x[30:23]==0)?0:{1'b0,x[30:0]};
     if(x[30:23]==0)begin result<=0;done<=1;end
     else if(x[30:0]>=32'h7e800000)begin result<={x[31],31'd0};done<=1;end
     else begin
      a<={9'h07f,x[22:0]};
      y<=32'h7ef311c3-{9'h07f,x[22:0]};
      state<=M1;
     end
    end
    M1:begin t<=mul_result;state<=S1;end
    S1:begin t<=addsub_result;state<=M2;end
    M2:begin y<=mul_result;state<=M3;end
    M3:begin t<=mul_result;state<=S2;end
    S2:begin t<=addsub_result;state<=M4;end
    M4:begin y<=mul_result;state<=M5;end
    M5:begin t<=mul_result;state<=S3;end
    S3:begin t<=addsub_result;state<=M6;end
    M6:begin t<=mul_result;state<=ADD;end
    ADD:begin y<=addsub_result;state<=FINISH;end
    FINISH:begin
     result<=(y+((32'd127-{24'd0,magnitude[30:23]})<<23))|{sign,31'd0};
     done<=1;state<=IDLE;
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
