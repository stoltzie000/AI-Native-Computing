// AI-Native Computing v0.9: coalesced column-major exact-zero activation-gated PE.
// Four signed MACs per accepted column; one burst request for all rows of that column.
// This is functional research RTL, not a validated HBM/DDR controller or physical GPU speedup.
module column_gated_pe #(
  parameter N=4,
  parameter DATA_W=8,
  parameter ACC_W=32
)(
  input wire clk,rst_n,start,
  input wire [N*DATA_W-1:0] vector_flat,
  output wire ready,busy,
  output reg done,
  output wire [N*ACC_W-1:0] sums_flat,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire [15:0] mem_req_col,
  input wire mem_rsp_valid,
  input wire [N*DATA_W-1:0] mem_rsp_column,
  output reg [31:0] issued_column_reads,
  output reg [31:0] issued_weight_elements,
  output reg [31:0] skipped_weight_elements,
  output reg [31:0] active_compute_cycles
);
  localparam [2:0] IDLE=0, SCAN=1, REQUEST=2, WAIT_RSP=3, FINISH=4;
  reg [2:0] state;
  reg [15:0] col_idx;
  reg [N*DATA_W-1:0] vector_hold;
  reg signed [ACC_W-1:0] accum [0:N-1];

  assign ready=(state==IDLE);
  assign busy=(state!=IDLE);
  assign mem_req_valid=(state==REQUEST);
  assign mem_req_col=col_idx;

  wire signed [DATA_W-1:0] activation=$signed(vector_hold[col_idx*DATA_W+:DATA_W]);

  genvar g;
  generate
    for(g=0;g<N;g=g+1)begin: RESULT
      assign sums_flat[g*ACC_W+:ACC_W]=accum[g];
    end
  endgenerate

`ifndef SYNTHESIS
  initial if(N<1 || N>65535 || DATA_W<2 || ACC_W<2*DATA_W)
    $fatal(1,"invalid PE geometry");
`endif

  integer r;
  reg signed [DATA_W-1:0] wr;
  reg signed [2*DATA_W-1:0] prod;
  reg signed [ACC_W-1:0] prod_ext;
  // A single column response contains N independent signed weights.
  // Use a separate signed product for each row, then register its sum.
  wire signed [ACC_W-1:0] row_product[0:N-1];
  generate
    for(g=0;g<N;g=g+1)begin: MACS
      wire signed [DATA_W-1:0] weight=$signed(mem_rsp_column[g*DATA_W+:DATA_W]);
      wire signed [2*DATA_W-1:0] multiply=weight*activation;
      assign row_product[g]=multiply;
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=IDLE;
      col_idx<=0;vector_hold<=0;
      done<=0;
      issued_column_reads<=0;
      issued_weight_elements<=0;
      skipped_weight_elements<=0;
      active_compute_cycles<=0;
      for(r=0;r<N;r=r+1) accum[r]<=0;
    end else begin
      done<=0;
      case(state)
        IDLE: if(start)begin
          vector_hold<=vector_flat;
          col_idx<=0;
          issued_column_reads<=0;
          issued_weight_elements<=0;
          skipped_weight_elements<=0;
          active_compute_cycles<=0;
          for(r=0;r<N;r=r+1) accum[r]<=0;
          state<=SCAN;
        end
        SCAN: begin
          if(col_idx>=N) state<=FINISH;
          else if(activation==0)begin
            // No memory transaction and no multiplies for this column.
            skipped_weight_elements<=skipped_weight_elements+N;
            col_idx<=col_idx+1;
          end else state<=REQUEST;
        end
        REQUEST: if(mem_req_ready)begin
          issued_column_reads<=issued_column_reads+1;
          issued_weight_elements<=issued_weight_elements+N;
          state<=WAIT_RSP;
        end
        WAIT_RSP: if(mem_rsp_valid)begin
          for(r=0;r<N;r=r+1) accum[r]<=accum[r]+row_product[r];
          active_compute_cycles<=active_compute_cycles+1;
          col_idx<=col_idx+1;
          state<=SCAN;
        end
        FINISH: begin
          done<=1;
          state<=IDLE;
        end
        default: state<=IDLE;
      endcase
    end
  end
endmodule
