// AI-Native-Computing v1.0: a burst-aligned column-buffered PE.
// This is behavioral/synthesizable research RTL; column_hold is REGISTERS,
// not a characterized SRAM macro or an HBM controller. One outstanding read.
module column_buffered_pe #(
  parameter ROWS=64,
  parameter COLS=4,
  parameter DATA_W=8,
  parameter ACC_W=32,
  parameter LANES=4
)(
  input wire clk,rst_n,start,
  input wire [COLS*DATA_W-1:0] vector_flat,
  output wire ready,busy,
  output reg done,
  output wire [ROWS*ACC_W-1:0] sums_flat,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire [15:0] mem_req_col,
  input wire mem_rsp_valid,
  input wire [ROWS*DATA_W-1:0] mem_rsp_column,
  output reg [31:0] issued_column_reads,
  output reg [31:0] fetched_weight_elements,
  output reg [31:0] skipped_weight_elements,
  output reg [31:0] active_compute_cycles
);
  localparam [2:0] IDLE=0, SCAN=1, REQUEST=2, WAIT_RSP=3, COMPUTE=4, FINISH=5;
  reg [2:0] state;
  reg [15:0] col_idx,row_idx;
  reg [COLS*DATA_W-1:0] vector_hold;
  reg [ROWS*DATA_W-1:0] column_hold;
  reg signed [ACC_W-1:0] accum[0:ROWS-1];
  assign ready=(state==IDLE);
  assign busy=(state!=IDLE);
  assign mem_req_valid=(state==REQUEST);
  assign mem_req_col=col_idx;
  wire signed [DATA_W-1:0] activation=$signed(vector_hold[col_idx*DATA_W+:DATA_W]);
  genvar row;
  generate
    for(row=0;row<ROWS;row=row+1)begin: OUT
      assign sums_flat[row*ACC_W+:ACC_W]=accum[row];
    end
  endgenerate
  wire signed [ACC_W-1:0] lane_product[0:LANES-1];
  genvar lane;
  generate
    for(lane=0;lane<LANES;lane=lane+1)begin: MAC
      wire signed [DATA_W-1:0] weight=
        $signed(column_hold[(row_idx+lane)*DATA_W+:DATA_W]);
      wire signed [2*DATA_W-1:0] product=weight*activation;
      assign lane_product[lane]=product;
    end
  endgenerate
`ifndef SYNTHESIS
  initial if(ROWS<1 || ROWS>65535 || COLS<1 || COLS>65535 ||
             DATA_W<2 || ACC_W<2*DATA_W ||
             LANES<1 || LANES>ROWS || ROWS%LANES!=0)
    $fatal(1,"unsupported PE parameters");
`endif
  integer i;
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin
      state<=IDLE;col_idx<=0;row_idx<=0;
      vector_hold<=0;column_hold<=0;done<=0;
      issued_column_reads<=0;fetched_weight_elements<=0;
      skipped_weight_elements<=0;active_compute_cycles<=0;
      for(i=0;i<ROWS;i=i+1)accum[i]<=0;
    end else begin
      done<=0;
      case(state)
        IDLE:if(start)begin
          vector_hold<=vector_flat;col_idx<=0;row_idx<=0;
          issued_column_reads<=0;fetched_weight_elements<=0;
          skipped_weight_elements<=0;active_compute_cycles<=0;
          for(i=0;i<ROWS;i=i+1)accum[i]<=0;
          state<=SCAN;
        end
        SCAN:begin
          if(col_idx>=COLS)state<=FINISH;
          else if(activation==0)begin
            skipped_weight_elements<=skipped_weight_elements+ROWS;
            col_idx<=col_idx+1;
          end else state<=REQUEST;
        end
        REQUEST:if(mem_req_ready)begin
          issued_column_reads<=issued_column_reads+1;
          fetched_weight_elements<=fetched_weight_elements+ROWS;
          state<=WAIT_RSP;
        end
        WAIT_RSP:if(mem_rsp_valid)begin
          column_hold<=mem_rsp_column;
          row_idx<=0;
          state<=COMPUTE;
        end
        COMPUTE:begin
          for(i=0;i<LANES;i=i+1)
            accum[row_idx+i]<=accum[row_idx+i]+lane_product[i];
          active_compute_cycles<=active_compute_cycles+1;
          if(row_idx+LANES>=ROWS)begin
            row_idx<=0;
            col_idx<=col_idx+1;
            state<=SCAN;
          end else row_idx<=row_idx+LANES;
        end
        FINISH:begin
          done<=1;state<=IDLE;
        end
        default:state<=IDLE;
      endcase
    end
  end
endmodule
