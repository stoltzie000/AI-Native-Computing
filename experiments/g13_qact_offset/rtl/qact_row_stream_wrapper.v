`timescale 1ns/1ps
// Narrow ready/valid streaming wrapper around independently verified serial QACT.
// 64 x 32-bit input handshakes, then 64 quantized bytes + eight 5-bit offsets.
// A row inverse is externally supplied with the first input beat; NOT hardware reciprocal.
// No external DRAM, DMA, pin assignment, clock constraint or physical power claimed.
module qact_row_stream_wrapper(
 input wire clk,rst_n,
 input wire input_valid,output wire input_ready,
 input wire [31:0] input_data,row_inverse,
 output wire output_valid,input wire output_ready,
 output wire [7:0] output_data,
 output wire output_is_offset,output wire output_last,
 output reg row_done
);
 localparam LOAD=3'd0,START=3'd1,WAIT_CORE=3'd2,DRAIN_Q=3'd3,DRAIN_D=3'd4;
 reg [2:0] state;
 reg [5:0] load_index;
 reg [6:0] output_index;
 reg [31:0] words[0:63];
 reg [31:0] inverse_latched;
 wire [2047:0] flat;
 wire core_ready,core_done;
 wire [511:0] q_flat;
 wire [39:0] offset_flat;
 genvar i;
 generate for(i=0;i<64;i=i+1) begin:INPUT_WORDS
  assign flat[i*32+:32]=words[i];
 end endgenerate
 qact_row_scaled_serial core(.clk(clk),.rst_n(rst_n),.start(state==START),
   .x_flat(flat),.row_inverse(inverse_latched),.ready(core_ready),
   .done(core_done),.q_flat(q_flat),.offset_flat(offset_flat));
 assign input_ready=(state==LOAD);
 assign output_valid=(state==DRAIN_Q || state==DRAIN_D);
 assign output_is_offset=(state==DRAIN_D);
 assign output_last=(state==DRAIN_D && output_index==7'd71);
 assign output_data=(state==DRAIN_Q)?
   q_flat[output_index*8+:8]:{3'd0,offset_flat[(output_index-7'd64)*5+:5]};
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n)begin
   state<=LOAD;load_index<=0;output_index<=0;
   inverse_latched<=0;row_done<=0;
  end else begin
   row_done<=0;
   case(state)
    LOAD:if(input_valid && input_ready)begin
     words[load_index]<=input_data;
     if(load_index==0)inverse_latched<=row_inverse;
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
     if(output_index==71)begin output_index<=0;state<=LOAD;row_done<=1;end
     else output_index<=output_index+1'b1;
    end
    default:begin state<=LOAD;load_index<=0;output_index<=0;end
   endcase
  end
 end
endmodule
