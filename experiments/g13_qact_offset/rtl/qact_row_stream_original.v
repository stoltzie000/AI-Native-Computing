`timescale 1ns/1ps
// Original FP32 arithmetic streaming quantizer, 64 raw input words.
// Output: 64 Q8 bytes, 8 offsets, 4 FP32 scale bytes (little-endian).
// No external DRAM, DMA, pin assignment, clock constraint or physical power claimed.
module qact_row_stream_original(
 input wire clk,rst_n,
 input wire input_valid,output wire input_ready,
 input wire [31:0] input_data,
 output wire output_valid,input wire output_ready,
 output wire [7:0] output_data,
 output wire [1:0] output_kind,output wire output_last,
 output reg row_done
);
 localparam LOAD=3'd0,START=3'd1,WAIT_CORE=3'd2,DRAIN_Q=3'd3,DRAIN_D=3'd4,DRAIN_S=3'd5;
 reg [2:0] state;
 reg [5:0] load_index;
 reg [6:0] output_index;
 reg [31:0] words[0:63];
 wire [2047:0] flat;
 wire core_ready,core_done;
 wire [511:0] q_flat;
 wire [39:0] offset_flat;
 wire [31:0] row_scale,computed_inverse;
 genvar i;
 generate for(i=0;i<64;i=i+1) begin:INPUT_WORDS
  assign flat[i*32+:32]=words[i];
 end endgenerate
 qact_row_clocked_original core(.clk(clk),.rst_n(rst_n),.start(state==START),
   .x_flat(flat),.ready(core_ready),.done(core_done),.q_flat(q_flat),
   .offset_flat(offset_flat),.row_scale(row_scale),.row_inverse(computed_inverse));
 assign input_ready=(state==LOAD);
 assign output_valid=(state==DRAIN_Q || state==DRAIN_D || state==DRAIN_S);
 assign output_kind=(state==DRAIN_D)?2'd1:(state==DRAIN_S)?2'd2:2'd0;
 assign output_last=(state==DRAIN_S && output_index==7'd75);
 assign output_data=(state==DRAIN_Q)?q_flat[output_index*8+:8]:
   (state==DRAIN_D)?{3'd0,offset_flat[(output_index-7'd64)*5+:5]}:
   row_scale[(output_index-7'd72)*8+:8];
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n)begin
   state<=LOAD;load_index<=0;output_index<=0;
   row_done<=0;
  end else begin
   row_done<=0;
   case(state)
    LOAD:if(input_valid && input_ready)begin
     words[load_index]<=input_data;
     if(load_index==63)begin load_index<=0;state<=START;end
     else load_index<=load_index+1'b1;
    end
    START:if(core_ready)state<=WAIT_CORE;
    WAIT_CORE:if(core_done)begin output_index<=0;state<=DRAIN_Q;end
    DRAIN_Q:if(output_valid && output_ready)begin
     if(output_index==63)begin output_index<=64;state<=DRAIN_D;end
     else output_index<=output_index+1'b1;
    end
    DRAIN_D:if(output_valid && output_ready)begin
     if(output_index==71)begin output_index<=72;state<=DRAIN_S;end
     else output_index<=output_index+1'b1;
    end
    DRAIN_S:if(output_valid && output_ready)begin
     if(output_index==75)begin output_index<=0;state<=LOAD;row_done<=1;end
     else output_index<=output_index+1'b1;
    end
    default:begin state<=LOAD;load_index<=0;output_index<=0;end
   endcase
  end
 end
endmodule
