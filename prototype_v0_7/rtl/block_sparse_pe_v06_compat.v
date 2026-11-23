// v0.7 verification-only language compatibility copy of historical v0.6.
// Sole semantic change: reserved identifier cell -> cell_index.
// AI-Native-Computing v0.6 research processing element.
// Verilog-2001 intended for synthesis, NOT silicon or FPGA validated.
// A block_valid=0 skip is mathematically correct ONLY if entire block is zero.
// Signed INT8 x INT8 -> signed INT32 accumulating row sums, one multiply per clock.
// Controller must hold weight and input flat buses stable while busy=1.
module block_sparse_pe #(
    parameter BLOCK_SIZE = 4,
    parameter DATA_W = 8,
    parameter ACC_W = 32
)(
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire block_valid,
    input  wire [BLOCK_SIZE*BLOCK_SIZE*DATA_W-1:0] weights_flat,
    input  wire [BLOCK_SIZE*DATA_W-1:0] vector_flat,
    output wire busy,
    output reg  done,
    output wire [BLOCK_SIZE*ACC_W-1:0] sums_flat,
    output reg [31:0] issued_multiplies,
    output reg [31:0] active_compute_cycles
);
  localparam [1:0] IDLE=2'd0, RUN=2'd1, FINISH=2'd2;
  reg [1:0] state;
  reg [15:0] cell_index;
  reg signed [ACC_W-1:0] accum [0:BLOCK_SIZE-1];
  integer i;

  assign busy = (state == RUN);
  genvar g;
  generate
    for(g=0;g<BLOCK_SIZE;g=g+1) begin: PACK_OUT
      assign sums_flat[g*ACC_W +: ACC_W] = accum[g];
    end
  endgenerate

  wire signed [DATA_W-1:0] selected_weight = $signed(weights_flat[cell_index*DATA_W +: DATA_W]);
  wire signed [DATA_W-1:0] selected_input = $signed(vector_flat[(cell_index%BLOCK_SIZE)*DATA_W +: DATA_W]);
  wire signed [2*DATA_W-1:0] product = selected_weight * selected_input;
  wire signed [ACC_W-1:0] extended_product = {{(ACC_W-2*DATA_W){product[2*DATA_W-1]}}, product};

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      cell_index <= 0;
      done <= 0;
      issued_multiplies <= 0;
      active_compute_cycles <= 0;
      for (i=0;i<BLOCK_SIZE;i=i+1) accum[i] <= 0;
    end else begin
      done <= 0;
      case(state)
        IDLE: if (start) begin
          cell_index <= 0;
          issued_multiplies <= 0;
          active_compute_cycles <= 0;
          for (i=0;i<BLOCK_SIZE;i=i+1) accum[i] <= 0;
          // Skip a certified all-zero block. No multiplier clocks issued.
          state <= block_valid ? RUN : FINISH;
        end
        RUN: begin
          accum[cell_index/BLOCK_SIZE] <= accum[cell_index/BLOCK_SIZE] + extended_product;
          issued_multiplies <= issued_multiplies+1;
          active_compute_cycles <= active_compute_cycles+1;
          if(cell_index==BLOCK_SIZE*BLOCK_SIZE-1) state <= FINISH;
          else cell_index <= cell_index+1;
        end
        FINISH: begin
          done <= 1;
          state <= IDLE;
        end
        default: state <= IDLE;
      endcase
    end
  end
endmodule
