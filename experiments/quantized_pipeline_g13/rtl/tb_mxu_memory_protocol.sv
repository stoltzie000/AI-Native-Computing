// G1.3 independent protocol stress. Requires a shared reset that flushes the
// external responder's outstanding transaction; the untagged DUT cannot
// identify stale post-reset responses. Fixed 402-byte pinned ISA fixture.
`timescale 1ns/1ps
module tb_mxu_memory_protocol;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n=0, start=0, force_req_stall=0, force_rsp_hold=0;
  wire ready, done, req_valid, req_ready, rsp_ready;
  wire [8:0] req_addr;
  reg rsp_valid=0;
  reg [7:0] rsp_data=0;
  wire [239:0] acc_flat;
  wire [15:0] dropped_groups, consumed_groups;
  reg [7:0] qmem[0:63], wmem[0:319], damem[0:7], dwmem[0:9], mem[0:401];
  reg [47:0] expected[0:4];
  reg [15:0] expected_drops[0:0];
  reg pending=0;
  reg [4:0] delay_count=0;
  reg [31:0] prng=32'h4a1d2001;
  reg stalled=0;
  reg [8:0] held_addr=0;
  reg job_live=0;
  integer requests=0, responses=0, completions=0;
  integer job_cycles=0, memory_cycles=0, group_cycles=0;
  integer i, seed_arg;
  string case_a, case_b;

  mxu_memory_wrapper dut(
    .clk(clk),.rst_n(rst_n),.start(start),.ready(ready),.done(done),
    .req_valid(req_valid),.req_ready(req_ready),.req_addr(req_addr),
    .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data),
    .acc_flat(acc_flat),.dropped_groups(dropped_groups),
    .consumed_groups(consumed_groups)
  );
  // Deterministic PRNG, request backpressure and response latency.
  always @(negedge clk)
    if (rst_n) prng <= {prng[30:0],prng[31]^prng[21]^prng[1]^prng[0]};
  assign req_ready = rst_n && !pending && !force_req_stall &&
                     (prng[2:0] != 3'b000);

  // A one-outstanding responder. Reset MUST cancel pending transactions.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pending<=0; rsp_valid<=0; rsp_data<=0; delay_count<=0;
    end else begin
      if (rsp_valid && rsp_ready) begin
        rsp_valid<=0;
        pending<=0;
      end else if (pending && !rsp_valid) begin
        if (delay_count != 0) delay_count<=delay_count-1;
        else if (!force_rsp_hold) rsp_valid<=1;
      end
      if (req_valid && req_ready) begin
        if (pending) $fatal(1,"responder accepted overlapping request");
        pending<=1;
        rsp_data<=mem[req_addr];
        delay_count<={1'b0,prng[7:4]};
      end
    end
  end

  // Request address and valid must remain asserted until accepted.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stalled<=0;
      held_addr<=0;
    end else begin
      if (stalled && (!req_valid || req_addr !== held_addr))
        $fatal(1,"unstable request under backpressure");
      stalled<=req_valid && !req_ready;
      if (req_valid && !req_ready) held_addr<=req_addr;
    end
  end

  always @(posedge clk) begin
    if (rst_n) begin
      if (done && !job_live) $fatal(1,"unexpected completion after abort/idle");
      if (job_live) begin
        job_cycles=job_cycles+1;
        if (job_cycles>12000) $fatal(1,"job timeout");
        if (req_valid && req_ready) begin
          if (requests>=402 || req_addr !== requests[8:0])
            $fatal(1,"request address/order/count at %0d",requests);
          requests=requests+1;
        end
        if (rsp_valid && rsp_ready) begin
          if (responses>=requests || responses>=402)
            $fatal(1,"unmatched or duplicated response");
          responses=responses+1;
        end
        if (dut.state==3'd1 || dut.state==3'd2)
          memory_cycles=memory_cycles+1;
        if (dut.core.state==2'd1) group_cycles=group_cycles+1;
        if ((dut.state==3'd3 || dut.state==3'd4) && responses!=402)
          $fatal(1,"compute launch before final response");
        if (!ready && done) $fatal(1,"done without ready");
        if (done) begin
          completions=completions+1;
          if (completions!=1 || requests!=402 || responses!=402 ||
              consumed_groups!=40 || group_cycles!=40)
            $fatal(1,"final protocol count mismatch req=%0d rsp=%0d groups=%0d done=%0d",
                   requests,responses,group_cycles,completions);
        end
      end
    end
  end

  task automatic load_case(input string path);
    integer k;
    begin
      $readmemh({path,"/q.hex"},qmem);
      $readmemh({path,"/w.hex"},wmem);
      $readmemh({path,"/da.hex"},damem);
      $readmemh({path,"/dw.hex"},dwmem);
      $readmemh({path,"/expected.hex"},expected);
      $readmemh({path,"/drops.hex"},expected_drops);
      for(k=0;k<64;k=k+1) mem[k]=qmem[k];
      for(k=0;k<320;k=k+1) mem[64+k]=wmem[k];
      for(k=0;k<8;k=k+1) mem[384+k]=damem[k];
      for(k=0;k<10;k=k+1) mem[392+k]=dwmem[k];
    end
  endtask

  task automatic start_job;
    begin
      wait (ready);
      @(negedge clk);
      if (done || pending || rsp_valid) $fatal(1,"not idle at launch");
      requests=0; responses=0; completions=0; job_cycles=0;
      memory_cycles=0; group_cycles=0;
      job_live=1; start=1;
      @(negedge clk);
      start=0;
    end
  endtask

  task automatic reset_and_verify;
    begin
      @(negedge clk); #1;
      rst_n=0; job_live=0; start=0;
      repeat (3) @(negedge clk);
      #1;
      if (!ready || req_valid || rsp_ready || done || pending || rsp_valid)
        $fatal(1,"reset did not quiesce RTL and responder");
      rst_n=1;
      repeat (3) @(negedge clk);
      if (!ready || done || pending || rsp_valid)
        $fatal(1,"post-reset stale activity");
    end
  endtask

  task automatic finish_job(input integer job_number);
    integer k;
    begin
      wait(done);
      @(negedge clk);
      if (!ready || requests!=402 || responses!=402 ||
          consumed_groups!=40 || dropped_groups!==expected_drops[0])
        $fatal(1,"job %0d completion counters",job_number);
      for(k=0;k<5;k=k+1)
        if (acc_flat[k*48+:48] !== expected[k])
          $fatal(1,"job %0d output %0d mismatch",job_number,k);
      $display("PASS_PROTOCOL_STRESS job=%0d requests=%0d responses=%0d memory_cycles=%0d group_cycles=%0d job_cycles=%0d",
               job_number,requests,responses,memory_cycles,group_cycles,job_cycles);
      @(negedge clk);
      if (done) $fatal(1,"duplicate done pulse");
      repeat (3) @(negedge clk);
      if (done) $fatal(1,"delayed duplicate done");
      job_live=0;
    end
  endtask

  initial begin
    if (!$value$plusargs("case_a=%s",case_a) ||
        !$value$plusargs("case_b=%s",case_b))
      $fatal(1,"requires case_a and case_b");
    if ($value$plusargs("seed=%d",seed_arg)) begin
      if (seed_arg==0) $fatal(1,"seed must be nonzero");
      prng=seed_arg;
    end
    repeat (3) @(negedge clk); #1 rst_n=1;
    load_case(case_a);

    // Reset with an unaccepted request.
    force_req_stall=1;
    start_job();
    wait(req_valid && !req_ready);
    repeat (3) @(negedge clk);
    reset_and_verify();
    $display("PASS_RESET request_wait");

    // Reset after accepted read, but before its response is delivered.
    force_req_stall=0; force_rsp_hold=1;
    start_job();
    wait(pending && !rsp_valid);
    repeat (3) @(negedge clk);
    if (!pending || rsp_valid) $fatal(1,"failed to force response wait");
    reset_and_verify();
    $display("PASS_RESET response_wait");

    // Reset after all 402 responses, during active integer computation.
    force_rsp_hold=0;
    start_job();
    wait(dut.state==3'd4 && consumed_groups>=10);
    reset_and_verify();
    $display("PASS_RESET compute");

    // Two complete jobs with different source memory, no reset between jobs.
    start_job();
    finish_job(1);
    load_case(case_b);
    start_job();
    finish_job(2);
    $display("PASS_PROTOCOL_SUITE");
    $finish;
  end
endmodule
