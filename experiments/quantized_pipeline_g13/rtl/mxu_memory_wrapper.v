// Research wrapper: one outstanding ordered byte read; prequantized operands.
module mxu_memory_wrapper(
 input wire clk,rst_n,start,
 output wire ready, output reg done,
 output wire req_valid,input wire req_ready,output wire [8:0] req_addr,
 input wire rsp_valid,output wire rsp_ready,input wire [7:0] rsp_data,
 output wire [239:0] acc_flat,output wire [15:0] dropped_groups,consumed_groups
);
 localparam IDLE=0,REQ=1,RSP=2,LAUNCH=3,WAIT_CORE=4;
 reg [2:0] state;
 reg [8:0] index;
 reg [511:0] q;
 reg [2559:0] w;
 reg [63:0] da;
 reg [79:0] dw;
 wire core_done,core_ready;
 assign ready=state==IDLE;
 assign req_valid=state==REQ;
 assign req_addr=index;
 assign rsp_ready=state==RSP;
 exact_mxu_int8_core core(.clk(clk),.rst_n(rst_n),.start(state==LAUNCH),
 .q_flat(q),.w_flat(w),.da_flat(da),.dw_flat(dw),.ready(core_ready),
 .done(core_done),.acc_flat(acc_flat),.dropped_groups(dropped_groups),
 .consumed_groups(consumed_groups));
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n) begin state<=IDLE;index<=0;done<=0;q<=0;w<=0;da<=0;dw<=0;end
  else begin
   done<=0;
   case(state)
    IDLE: if(start) begin index<=0;state<=REQ;end
    REQ: if(req_ready) state<=RSP;
    RSP: if(rsp_valid) begin
     if(index<64) q[index*8+:8]<=rsp_data;
     else if(index<384) w[(index-64)*8+:8]<=rsp_data;
     else if(index<392) da[(index-384)*8+:8]<=rsp_data;
     else dw[(index-392)*8+:8]<=rsp_data;
     if(index==401) state<=LAUNCH;
     else begin index<=index+1;state<=REQ;end
    end
    LAUNCH: if(core_ready) state<=WAIT_CORE;
    WAIT_CORE: if(core_done) begin done<=1;state<=IDLE;end
    default: state<=IDLE;
   endcase
  end
 end
endmodule
