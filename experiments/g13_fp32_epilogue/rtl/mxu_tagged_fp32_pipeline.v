`timescale 1ns/1ps
// Tagged 426-byte prequantized operand+scale loader with bit-exact FP32 epilogue. NOT a DRAM controller.
// Seven 64-byte transactions fetch 426 useful bytes (tail mask 42 bytes).
// A reset forces a flush request; start is blocked until the external
// responder acknowledges all pre-reset transactions are cancelled.
module mxu_tagged_fp32_pipeline #(
  parameter BURST_BYTES=64,
  parameter MAX_OUTSTANDING=4,
  parameter TAG_W=4
)(
  input wire clk,rst_n,start,
  output wire ready,output reg done,output reg protocol_error,
  output wire flush_req,input wire flush_ack,
  output wire req_valid,input wire req_ready,
  output wire [TAG_W-1:0] req_tag,
  output wire [8:0] req_addr,
  output reg [BURST_BYTES-1:0] req_mask,
  input wire rsp_valid,output wire rsp_ready,
  input wire [TAG_W-1:0] rsp_tag,
  input wire [BURST_BYTES*8-1:0] rsp_data,
  output wire [239:0] acc_flat,
  output wire [159:0] fp32_flat,
  output wire [15:0] dropped_groups,consumed_groups
);
  localparam TOTAL_BYTES=426;
  localparam NUM_BURSTS=(TOTAL_BYTES+BURST_BYTES-1)/BURST_BYTES;
  localparam ST_FLUSH=3'd0,ST_IDLE=3'd1,ST_LOAD=3'd2,
             ST_LAUNCH=3'd3,ST_COMPUTE=3'd4,ST_FAULT=3'd5;
  reg [2:0] state;
  reg [TAG_W-1:0] issued,received;
  reg [TAG_W:0] inflight;
  reg [NUM_BURSTS-1:0] pending_tags,completed_tags;
  wire [511:0] q;
  wire [2559:0] w;
  wire [63:0] da;
  wire [79:0] dw;
  wire [31:0] activation_scale;
  wire [159:0] weight_scale_flat;
  reg [7:0] payload [0:TOTAL_BYTES-1];
  wire core_done,core_ready;
  wire req_fire=req_valid && req_ready;
  wire rsp_fire=rsp_valid && rsp_ready;
  integer mask_lane;

  assign ready=(state==ST_IDLE);
  assign flush_req=(state==ST_FLUSH);
  assign req_valid=(state==ST_LOAD) &&
                   (issued<NUM_BURSTS) &&
                   (inflight<MAX_OUTSTANDING);
  assign req_tag=issued;
  assign req_addr=issued*BURST_BYTES;
  assign rsp_ready=(state==ST_LOAD);

  always @* begin
    req_mask={BURST_BYTES{1'b0}};
    for(mask_lane=0;mask_lane<BURST_BYTES;mask_lane=mask_lane+1)
      if(req_valid && ((issued*BURST_BYTES+mask_lane)<TOTAL_BYTES))
        req_mask[mask_lane]=1'b1;
  end

  // Static byte/register enables avoid dynamic 3216-bit write barrel muxing.
  // Tag/address comparison is a compile-time constant for every byte lane.
  // Each byte has exactly one writer, and invalid tags never mutate payload.
  genvar byte_i;
  generate for(byte_i=0;byte_i<TOTAL_BYTES;byte_i=byte_i+1) begin: BYTE_LANE
    always @(posedge clk or negedge rst_n) begin
      if(!rst_n) payload[byte_i]<=8'b0;
      else if(rsp_fire && rsp_tag==(byte_i / BURST_BYTES) &&
              pending_tags[rsp_tag] && !completed_tags[rsp_tag])
        payload[byte_i]<=rsp_data[(byte_i % BURST_BYTES)*8+:8];
    end
    if(byte_i<64) assign q[byte_i*8+:8]=payload[byte_i];
    else if(byte_i<384) assign w[(byte_i-64)*8+:8]=payload[byte_i];
    else if(byte_i<392) assign da[(byte_i-384)*8+:8]=payload[byte_i];
    else if(byte_i<402) assign dw[(byte_i-392)*8+:8]=payload[byte_i];
    else if(byte_i<406) assign activation_scale[(byte_i-402)*8+:8]=payload[byte_i];
    else assign weight_scale_flat[(byte_i-406)*8+:8]=payload[byte_i];
  end endgenerate

  exact_mxu_int8_core core(
    .clk(clk),.rst_n(rst_n),.start(state==ST_LAUNCH),
    .q_flat(q),.w_flat(w),.da_flat(da),.dw_flat(dw),
    .ready(core_ready),.done(core_done),.acc_flat(acc_flat),
    .dropped_groups(dropped_groups),.consumed_groups(consumed_groups)
  );

  mxu_integer_epilogue epilogue(
    .acc_flat(acc_flat),.weight_scale_flat(weight_scale_flat),
    .activation_scale(activation_scale),.result_flat(fp32_flat)
  );

  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=ST_FLUSH;
      done<=0;protocol_error<=0;
      issued<=0;received<=0;inflight<=0;
      pending_tags<=0;completed_tags<=0;
    end else begin
      done<=0;
      case(state)
        ST_FLUSH: if(flush_ack && !rsp_valid) state<=ST_IDLE;
        ST_IDLE: if(start) begin
          issued<=0;received<=0;inflight<=0;
          pending_tags<=0;completed_tags<=0;
          protocol_error<=0;
          state<=ST_LOAD;
        end
        ST_LOAD: begin
          if(req_fire) begin
            pending_tags[req_tag]<=1'b1;
            issued<=issued+1'b1;
          end
          if(rsp_fire) begin
            if(rsp_tag>=NUM_BURSTS ||
               !pending_tags[rsp_tag] || completed_tags[rsp_tag]) begin
              protocol_error<=1;
              state<=ST_FAULT;
            end else begin
              pending_tags[rsp_tag]<=1'b0;
              completed_tags[rsp_tag]<=1'b1;
              received<=received+1'b1;
              if(received==NUM_BURSTS-1 && issued==NUM_BURSTS)
                state<=ST_LAUNCH;
            end
          end
          case({req_fire,rsp_fire})
            2'b10: inflight<=inflight+1'b1;
            2'b01: inflight<=inflight-1'b1;
            default: ;
          endcase
        end
        ST_LAUNCH: if(core_ready) state<=ST_COMPUTE;
        ST_COMPUTE: if(core_done) begin
          done<=1;
          state<=ST_IDLE;
        end
        ST_FAULT: state<=ST_FAULT;
        default: begin protocol_error<=1;state<=ST_FAULT;end
      endcase
    end
  end
`ifndef SYNTHESIS
  initial if(BURST_BYTES<1 || BURST_BYTES>128 ||
             (BURST_BYTES & (BURST_BYTES-1)) != 0 ||
             NUM_BURSTS >= (1 << TAG_W) || MAX_OUTSTANDING<1 ||
             MAX_OUTSTANDING>NUM_BURSTS)
    $fatal(1,"unsupported burst geometry");
`endif
endmodule
