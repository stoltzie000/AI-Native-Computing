`timescale 1ns/1ps
// Exercise historical v0.6 RTL unchanged with 256 randomized input matrices.
module tb_v06_differential;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0,start=0,block_valid=0;
  reg [127:0] weights_flat=0;
  reg [31:0] vector_flat=0;
  wire busy,done;
  wire [127:0] sums_flat;
  wire [31:0] issued_multiplies,active_compute_cycles;
  integer seed=32'h62af9821,case_id=0;
  integer expected_rows[0:3];
  integer row,col,tot,cycles,j;
  reg signed [7:0] w,x;
  block_sparse_pe dut(clk,rst_n,start,block_valid,weights_flat,vector_flat,
                      busy,done,sums_flat,issued_multiplies,active_compute_cycles);
  task run_case;
    input skip;
    begin
      for(row=0;row<4;row=row+1) begin
        tot=0;
        for(col=0;col<4;col=col+1) begin
          w=$signed(weights_flat[(row*4+col)*8+:8]);
          x=$signed(vector_flat[col*8+:8]);
          tot=tot+w*x;
        end
        expected_rows[row]=tot;
        if(skip && tot!=0) $fatal(1,"false zero certificate in test");
      end
      @(negedge clk);block_valid=!skip;start=1;
      @(negedge clk);start=0;
      cycles=0;
      while(done!==1 && cycles<35) begin
        @(negedge clk);cycles=cycles+1;
      end
      if(done!==1 || issued_multiplies!==(skip?0:16) ||
         active_compute_cycles!==(skip?0:16))
        $fatal(1,"v0.6 count/handshake mismatch case=%0d",case_id);
      for(row=0;row<4;row=row+1)
        if($signed(sums_flat[row*32+:32])!==expected_rows[row])
          $fatal(1,"v0.6 numeric mismatch case=%0d row=%0d",case_id,row);
      @(negedge clk);
      if(done!==0) $fatal(1,"v0.6 done pulse error");
      case_id=case_id+1;
    end
  endtask
  initial begin
    repeat(3) @(negedge clk);rst_n=1;
    for(j=0;j<256;j=j+1) begin
      for(col=0;col<16;col=col+1)
        weights_flat[col*8+:8]=(j%13==0)?8'd0:$random(seed);
      for(col=0;col<4;col=col+1) vector_flat[col*8+:8]=$random(seed);
      run_case(j%13==0);
    end
    $display("PASS v0.6 differential randomized RTL: %0d cases",case_id);
    $finish;
  end
endmodule
