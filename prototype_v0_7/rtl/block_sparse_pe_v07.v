// Experimental v0.7 block-sparse PE. Not measured silicon or FPGA hardware.
// Inputs are latched on start&&ready. A zero block must be certified upstream.
// Parameter LANES must divide BLOCK_SIZE*BLOCK_SIZE.
module block_sparse_pe_v07 #(
  parameter BLOCK_SIZE=4,
  parameter DATA_W=8,
  parameter ACC_W=32,
  parameter LANES=4
)(
  input wire clk, rst_n, start, certified_nonzero_block,
  input wire [BLOCK_SIZE*BLOCK_SIZE*DATA_W-1:0] weights_flat,
  input wire [BLOCK_SIZE*DATA_W-1:0] vector_flat,
  output wire ready, busy,
  output reg done,
  output wire [BLOCK_SIZE*ACC_W-1:0] sums_flat,
  output reg [31:0] issued_multiplies,
  output reg [31:0] active_compute_cycles
);
  localparam CELLS=BLOCK_SIZE*BLOCK_SIZE;
  localparam [1:0] IDLE=0, RUN=1, FINISH=2;
  reg [1:0] state;
  reg [31:0] cell_index;
  reg [CELLS*DATA_W-1:0] weights_hold;
  reg [BLOCK_SIZE*DATA_W-1:0] vector_hold;
  reg signed [ACC_W-1:0] accum [0:BLOCK_SIZE-1];

  assign ready=(state==IDLE);
  assign busy=(state!=IDLE);
  genvar g;
  generate
    for(g=0;g<BLOCK_SIZE;g=g+1) begin: OUTPUTS
      assign sums_flat[g*ACC_W +: ACC_W]=accum[g];
    end
  endgenerate

`ifndef SYNTHESIS
  initial begin
    if(BLOCK_SIZE<1 || DATA_W<2 || ACC_W<2*DATA_W ||
       LANES<1 || LANES>CELLS || (CELLS%LANES)!=0)
      $fatal(1,"Invalid PE widths or lane count");
  end
`endif

  // Combine all products for a row before updating that row register.
  // Otherwise multiple nonblocking assignments would silently drop terms.
  reg signed [ACC_W-1:0] row_partial [0:BLOCK_SIZE-1];
  reg [31:0] multiplies_this_cycle;
  reg signed [DATA_W-1:0] weight_tmp, vector_tmp;
  reg signed [2*DATA_W-1:0] product_tmp;
  reg signed [ACC_W-1:0] product_ext;
  integer row,lane,idx;
  always @* begin
    for(row=0;row<BLOCK_SIZE;row=row+1) row_partial[row]=0;
    multiplies_this_cycle=0;
    weight_tmp=0;
    vector_tmp=0;
    product_tmp=0;
    product_ext=0;
    idx=0;
    for(lane=0;lane<LANES;lane=lane+1) begin
      idx=cell_index+lane;
      if(idx<CELLS) begin
        weight_tmp=$signed(weights_hold[idx*DATA_W +: DATA_W]);
        vector_tmp=$signed(vector_hold[(idx%BLOCK_SIZE)*DATA_W +: DATA_W]);
        product_tmp=weight_tmp*vector_tmp;
        product_ext=product_tmp; // signed assignment extends to ACC_W
        row_partial[idx/BLOCK_SIZE]=row_partial[idx/BLOCK_SIZE]+product_ext;
        multiplies_this_cycle=multiplies_this_cycle+1;
      end
    end
  end

  integer k;
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=IDLE;
      cell_index<=0;
      weights_hold<=0;
      vector_hold<=0;
      done<=0;
      issued_multiplies<=0;
      active_compute_cycles<=0;
      for(k=0;k<BLOCK_SIZE;k=k+1) accum[k]<=0;
    end else begin
      done<=0;
      case(state)
        IDLE: if(start) begin
          weights_hold<=weights_flat;
          vector_hold<=vector_flat;
          cell_index<=0;
          issued_multiplies<=0;
          active_compute_cycles<=0;
          for(k=0;k<BLOCK_SIZE;k=k+1) accum[k]<=0;
          state<=certified_nonzero_block ? RUN : FINISH;
        end
        RUN: begin
          for(k=0;k<BLOCK_SIZE;k=k+1) accum[k]<=accum[k]+row_partial[k];
          issued_multiplies<=issued_multiplies+multiplies_this_cycle;
          active_compute_cycles<=active_compute_cycles+1;
          if(cell_index+LANES>=CELLS) state<=FINISH;
          else cell_index<=cell_index+LANES;
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
