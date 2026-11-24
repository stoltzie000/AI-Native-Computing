`timescale 1ns/1ps
// Separate adversarial negative tests: unexpected and duplicate response tags,
// mandatory reset+flush quiescence, fail-closed behavior. No numerical fixture.
module tb_mxu_tagged_burst_fault;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n=0,start=0,flush_ack=0,rsp_valid=0;
  reg [3:0] rsp_tag=0;
  reg [511:0] rsp_data=0;
  wire ready,done,protocol_error,flush_req,req_valid,req_ready,rsp_ready;
  wire [3:0] req_tag;
  wire [8:0] req_addr;
  wire [63:0] req_mask;
  wire [239:0] acc_flat;
  wire [15:0] dropped_groups,consumed_groups;
  assign req_ready=1'b1;

  mxu_tagged_burst_wrapper dut(
    .clk(clk),.rst_n(rst_n),.start(start),.ready(ready),.done(done),
    .protocol_error(protocol_error),.flush_req(flush_req),
    .flush_ack(flush_ack),.req_valid(req_valid),.req_ready(req_ready),
    .req_tag(req_tag),.req_addr(req_addr),.req_mask(req_mask),
    .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),
    .rsp_data(rsp_data),.acc_flat(acc_flat),
    .dropped_groups(dropped_groups),.consumed_groups(consumed_groups)
  );

  task automatic reset_flush_gate;
    begin
      @(negedge clk);#1 rst_n=0;
      flush_ack=1; rsp_valid=1; start=0; rsp_tag=4'hf;
      repeat(3) @(negedge clk);
      #1 rst_n=1;
      repeat(2) @(negedge clk);
      if(!flush_req || ready || req_valid || rsp_ready || protocol_error)
        $fatal(1,"flush acknowledged despite live stale response");
      rsp_valid=0;
      wait(ready);
      @(negedge clk);
      if(flush_req || protocol_error || done) $fatal(1,"post-reset state");
      $display("PASS_TAGGED_FLUSH_GATE");
    end
  endtask

  task automatic start_one;
    begin
      wait(ready);
      @(negedge clk);
      start=1;
      @(negedge clk);
      start=0;
      if(!req_valid && !rsp_ready) $fatal(1,"loader did not start");
    end
  endtask

  task automatic send_response(input [3:0] tag);
    begin
      @(negedge clk); rsp_tag=tag; rsp_valid=1;
      @(negedge clk); rsp_valid=0;
    end
  endtask

  task automatic assert_fault;
    begin
      wait(protocol_error);
      @(negedge clk);
      if(!protocol_error || req_valid || rsp_ready || ready || done ||
         flush_req) $fatal(1,"malformed response did not fail closed");
      repeat(3) @(negedge clk);
      if(!protocol_error || done) $fatal(1,"fault not latched");
    end
  endtask

  initial begin
    repeat(2) @(negedge clk);
    reset_flush_gate();
    start_one();
    send_response(4'hf);
    assert_fault();
    $display("PASS_TAGGED_INVALID_TAG");

    reset_flush_gate();
    start_one();
    // First tag must have been accepted before returning its response.
    send_response(4'h0);
    if(protocol_error) $fatal(1,"unexpected fault on valid response");
    send_response(4'h0);
    assert_fault();
    $display("PASS_TAGGED_DUPLICATE_TAG");
    $display("PASS_TAGGED_FAULT_SUITE");
    $finish;
  end
  initial begin #1000000;$fatal(1,"fault test watchdog");end
endmodule
