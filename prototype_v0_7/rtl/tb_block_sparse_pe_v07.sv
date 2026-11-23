`timescale 1ns/1ps
// Self-checking SystemVerilog stress bench. Override LANES_TB and ACC_W_TB.
// The arithmetic oracle reads the external input bus BEFORE the PE accepts it.
module tb_block_sparse_pe_v07;
  parameter LANES_TB=4, ACC_W_TB=32;
  localparam N=4;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n=0, start=0, certified_nonzero_block=1;
  reg [127:0] weights_flat=0;
  reg [31:0] vector_flat=0;
  wire ready,busy,done;
  wire [N*ACC_W_TB-1:0] sums_flat;
  wire [31:0] issued_multiplies,active_compute_cycles;
  integer global_cycles=0;
  integer seed=32'h12a4b6c8;
  integer runs=0;
  integer k;
  integer expected_rows[0:N-1];
  always @(posedge clk) global_cycles<=global_cycles+1;

  block_sparse_pe_v07 #(.BLOCK_SIZE(N),.DATA_W(8),.ACC_W(ACC_W_TB),.LANES(LANES_TB)) dut (
    .clk(clk),.rst_n(rst_n),.start(start),.certified_nonzero_block(certified_nonzero_block),
    .weights_flat(weights_flat),.vector_flat(vector_flat),.ready(ready),.busy(busy),.done(done),
    .sums_flat(sums_flat),.issued_multiplies(issued_multiplies),
    .active_compute_cycles(active_compute_cycles)
  );

  task calculate_expected;
    integer row,col,acc;
    reg signed [7:0] w,x;
    begin
      for(row=0;row<N;row=row+1) begin
        acc=0;
        for(col=0;col<N;col=col+1) begin
          w=$signed(weights_flat[(row*N+col)*8+:8]);
          x=$signed(vector_flat[col*8+:8]);
          acc=acc+(w*x);
        end
        if(ACC_W_TB==16) expected_rows[row]=$signed(acc[15:0]);
        else expected_rows[row]=acc;
      end
    end
  endtask

  task run_case;
    input skip, spurious_start;
    integer row,expected_mult,expected_active,begin_cycle,count,observed,actual;
    begin
      if(ready!==1 || busy!==0 || done!==0) $fatal(1,"not idle before case=%0d",runs);
      calculate_expected();
      if(skip) begin
        // Zero certificates must not be used to suppress nonzero weight blocks.
        for(row=0;row<N;row=row+1)
          if(expected_rows[row]!==0) $fatal(1,"invalid test certificate");
      end
      expected_mult=skip?0:16;
      expected_active=skip?0:(16/LANES_TB);
      @(negedge clk); certified_nonzero_block=!skip; start=1;
      @(negedge clk); start=0; begin_cycle=global_cycles;
      if(ready!==0 || busy!==1) $fatal(1,"accept handshake failed");
      // Deliberate host-bus disturbance: accepted input must be internally captured.
      weights_flat={16{8'hff}};
      vector_flat={4{8'h80}};
      if(spurious_start) start=1; // Must be ignored while not ready.
      count=0;
      while(done!==1 && count<40) begin
        @(negedge clk);
        count=count+1;
        if(count==1) start=0;
      end
      start=0;
      if(done!==1) $fatal(1,"timeout lanes=%0d case=%0d",LANES_TB,runs);
      observed=global_cycles-begin_cycle+1;
      if(observed!==expected_active+2)
        $fatal(1,"latency mismatch case=%0d got=%0d expected=%0d",runs,observed,expected_active+2);
      if(issued_multiplies!==expected_mult || active_compute_cycles!==expected_active)
        $fatal(1,"count mismatch case=%0d got=%0d,%0d expected=%0d,%0d",runs,issued_multiplies,active_compute_cycles,expected_mult,expected_active);
      for(row=0;row<N;row=row+1) begin
        actual=$signed(sums_flat[row*ACC_W_TB+:ACC_W_TB]);
        if(actual!==expected_rows[row])
          $fatal(1,"numeric mismatch case=%0d row=%0d actual=%0d expected=%0d",runs,row,actual,expected_rows[row]);
      end
      if(ready!==1 || busy!==0) $fatal(1,"not ready on completion");
      @(negedge clk);
      if(done!==0) $fatal(1,"done signal not single pulse");
      runs=runs+1;
    end
  endtask

  task random_case;
    input skip, inject;
    integer q;
    begin
      for(q=0;q<16;q=q+1) weights_flat[q*8+:8]=skip ? 8'd0 : $random(seed);
      for(q=0;q<4;q=q+1) vector_flat[q*8+:8]=$random(seed);
      run_case(skip,inject);
    end
  endtask

  task interrupt_and_reset;
    integer row;
    begin
      weights_flat={16{8'h80}}; vector_flat={4{8'h80}};
      @(negedge clk);start=1;certified_nonzero_block=1;
      @(negedge clk);start=0;
      if(ready!==0) $fatal(1,"not active at reset initiation");
      rst_n=0; #1;
      if(ready!==1 || busy!==0 || done!==0 || issued_multiplies!==0)
        $fatal(1,"asynchronous reset violated");
      for(row=0;row<N;row=row+1)
        if(sums_flat[row*ACC_W_TB+:ACC_W_TB]!==0)
          $fatal(1,"reset failed to clear result");
      @(negedge clk);rst_n=1;
      repeat(3) @(negedge clk);
      if(done!==0 || ready!==1) $fatal(1,"spurious post-reset completion");
      weights_flat=0;
      run_case(1,0);
    end
  endtask

  initial begin
    if(!(LANES_TB==1 || LANES_TB==2 || LANES_TB==4 || LANES_TB==8 || LANES_TB==16))
      $fatal(1,"unsupported LANES_TB");
    if(!(ACC_W_TB==16 || ACC_W_TB==32))
      $fatal(1,"unsupported ACC_W_TB");
    repeat(3) @(negedge clk);rst_n=1;
    repeat(2) @(negedge clk);
    weights_flat={16{8'h80}};vector_flat={4{8'h80}};
    run_case(0,1);
    weights_flat={16{8'h7f}};vector_flat={4{8'h7f}};
    run_case(0,1);
    weights_flat=0;vector_flat=32'hff017f80;
    run_case(1,0);
    interrupt_and_reset();
    for(k=0;k<128;k=k+1)
      random_case((k%11)==0,(k%7)==0);
    $display("PASS v0.7 RTL randomized verification LANES=%0d ACC_W=%0d cases=%0d",LANES_TB,ACC_W_TB,runs);
    $finish;
  end
endmodule
