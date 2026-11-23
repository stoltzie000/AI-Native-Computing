// AI-Native Computing v0.8 — exact-zero activation-gated weight request engine.
// Research RTL only. ONE outstanding in-order memory request, no physical PHY.
// The controller omits each weight read for which activation[col] == zero.
// This preserves exact signed integer matrix-vector output (mod 2^ACC_W).
module activation_gated_pe #(
  parameter BLOCK_SIZE=4,
  parameter DATA_W=8,
  parameter ACC_W=32
)(
  input wire clk,rst_n,start,
  input wire [BLOCK_SIZE*DATA_W-1:0] vector_flat,
  output wire ready,busy,
  output reg done,
  output wire [BLOCK_SIZE*ACC_W-1:0] sums_flat,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire [15:0] mem_req_row,mem_req_col,
  input wire mem_rsp_valid,
  input wire [DATA_W-1:0] mem_rsp_weight,
  output reg [31:0] issued_weight_reads,issued_multiplies,skipped_products
);
  localparam [2:0] IDLE=0,SCAN=1,REQUEST=2,WAIT_RSP=3,FINISH=4;
  reg [2:0] state;
  reg [15:0] row_idx,col_idx;
  reg [BLOCK_SIZE*DATA_W-1:0] vector_hold;
  reg signed [ACC_W-1:0] accum[0:BLOCK_SIZE-1];
  genvar g;
  generate
    for(g=0;g<BLOCK_SIZE;g=g+1) begin: OUTPUTS
      assign sums_flat[g*ACC_W+:ACC_W]=accum[g];
    end
  endgenerate

  assign ready=(state==IDLE);
  assign busy=(state!=IDLE);
  assign mem_req_valid=(state==REQUEST);
  assign mem_req_row=row_idx;
  assign mem_req_col=col_idx;

  wire signed [DATA_W-1:0] current_activation=
    $signed(vector_hold[col_idx*DATA_W+:DATA_W]);
  wire signed [DATA_W-1:0] current_weight=$signed(mem_rsp_weight);
  wire signed [2*DATA_W-1:0] product=current_weight*current_activation;
  wire signed [ACC_W-1:0] product_extended=product;

`ifndef SYNTHESIS
  initial begin
    if(BLOCK_SIZE<1 || BLOCK_SIZE>65535 || DATA_W<2 || ACC_W<2*DATA_W)
      $fatal(1,"invalid activation-gated PE geometry");
  end
`endif

  integer i;
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=IDLE;
      row_idx<=0;col_idx<=0;
      vector_hold<=0;
      done<=0;
      issued_weight_reads<=0;
      issued_multiplies<=0;
      skipped_products<=0;
      for(i=0;i<BLOCK_SIZE;i=i+1) accum[i]<=0;
    end else begin
      done<=0;
      case(state)
        IDLE: if(start) begin
          vector_hold<=vector_flat;
          row_idx<=0;col_idx<=0;
          issued_weight_reads<=0;
          issued_multiplies<=0;
          skipped_products<=0;
          for(i=0;i<BLOCK_SIZE;i=i+1) accum[i]<=0;
          state<=SCAN;
        end
        SCAN: begin
          if(row_idx>=BLOCK_SIZE) begin
            state<=FINISH;
          end else if(current_activation==0) begin
            // IMPORTANT: no weight request or multiply is issued for zero.
            skipped_products<=skipped_products+1;
            if(col_idx==BLOCK_SIZE-1) begin
              col_idx<=0;row_idx<=row_idx+1;
            end else col_idx<=col_idx+1;
          end else begin
            state<=REQUEST;
          end
        end
        REQUEST: if(mem_req_ready) begin
          issued_weight_reads<=issued_weight_reads+1;
          state<=WAIT_RSP;
        end
        WAIT_RSP: if(mem_rsp_valid) begin
          accum[row_idx]<=accum[row_idx]+product_extended;
          issued_multiplies<=issued_multiplies+1;
          if(col_idx==BLOCK_SIZE-1) begin
            col_idx<=0;row_idx<=row_idx+1;
          end else col_idx<=col_idx+1;
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
