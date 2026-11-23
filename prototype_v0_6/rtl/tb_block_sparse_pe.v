`timescale 1ns/1ps
// Small functional Verilog regression; no hardware performance or synthesis claim.
module tb_block_sparse_pe;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n=0;
  reg start=0;
  reg block_valid=0;
  reg [127:0] weights_flat;
  reg [31:0] vector_flat;
  wire busy,done;
  wire [127:0] sums_flat;
  wire [31:0] issued_multiplies,active_compute_cycles;
  integer j, cycles;

  block_sparse_pe #(.BLOCK_SIZE(4),.DATA_W(8),.ACC_W(32)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.block_valid(block_valid),
    .weights_flat(weights_flat),.vector_flat(vector_flat),.busy(busy),.done(done),
    .sums_flat(sums_flat),.issued_multiplies(issued_multiplies),
    .active_compute_cycles(active_compute_cycles)
  );

  task launch_and_check;
    input expected_skip;
    input integer row0,row1,row2,row3;
    begin
      @(negedge clk);
      block_valid=!expected_skip;
      start=1;
      @(negedge clk);
      start=0;
      cycles=0;
      while(done!==1 && cycles<40) begin
        @(negedge clk);
        cycles=cycles+1;
      end
      if(done!==1) begin $display("FAIL: timeout"); $fatal(1); end
      if($signed(sums_flat[31:0])!==row0 ||
         $signed(sums_flat[63:32])!==row1 ||
         $signed(sums_flat[95:64])!==row2 ||
         $signed(sums_flat[127:96])!==row3) begin
           $display("FAIL sums: %0d,%0d,%0d,%0d expected %0d,%0d,%0d,%0d",
             $signed(sums_flat[31:0]),$signed(sums_flat[63:32]),
             $signed(sums_flat[95:64]),$signed(sums_flat[127:96]),row0,row1,row2,row3);
           $fatal(1);
      end
      if(expected_skip) begin
        if(issued_multiplies!==0 || active_compute_cycles!==0) begin
          $display("FAIL skipped cycles"); $fatal(1);
        end
      end else begin
        if(issued_multiplies!==16 || active_compute_cycles!==16) begin
          $display("FAIL issued multiply count/cycles"); $fatal(1);
        end
      end
      @(negedge clk);
    end
  endtask

  initial begin
    weights_flat=0;
    vector_flat=0;
    repeat(3) @(negedge clk);
    rst_n=1;
    // Case 1: full active 4x4 block. Input [2, -1, 3, 0].
    vector_flat[7:0]=8'd2;
    vector_flat[15:8]=8'hff;
    vector_flat[23:16]=8'd3;
    vector_flat[31:24]=8'd0;
    for(j=0;j<16;j=j+1) weights_flat[j*8 +: 8]=j+1;
    launch_and_check(0,9,25,41,57);
    // Case 2: confirmed all-zero block. No multiply issued.
    weights_flat=0;
    launch_and_check(1,0,0,0,0);
    // Case 3: signed negative weight in first row.
    weights_flat=0;
    weights_flat[7:0]=8'hfd;  // -3 * 2 => -6
    weights_flat[15:8]=8'd5; // 5 * -1 => -5
    launch_and_check(0,-11,0,0,0);
    $display("PASS block_sparse_pe RTL functional tests: active, skip, signed");
    $finish;
  end
endmodule
