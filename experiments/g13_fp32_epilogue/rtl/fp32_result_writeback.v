`timescale 1ns/1ps
// Single-beat result writeback; byte-lane 0 carries result bits 7:0.
// Reset cancels unaccepted writes only. Accepted writes are not rolled back.
module fp32_result_writeback(
 input wire clk,rst_n,
 input wire result_valid, output wire result_ready,
 input wire [159:0] result_data,input wire [63:0] result_addr,
 output wire write_valid,input wire write_ready,
 output reg [511:0] write_data,output reg [63:0] write_addr,
 output wire [63:0] write_mask,output reg done
);
 reg pending;
 assign result_ready=!pending && rst_n;
 assign write_valid=pending && rst_n;
 assign write_mask=64'h00000000000fffff;
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin pending<=0;done<=0;write_data<=0;write_addr<=0;end
  else begin
   done<=0;
   if(write_valid && write_ready) begin pending<=0;done<=1;end
   if(result_valid && result_ready) begin
    pending<=1;write_data<={352'b0,result_data};write_addr<=result_addr;
   end
  end
 end
endmodule
