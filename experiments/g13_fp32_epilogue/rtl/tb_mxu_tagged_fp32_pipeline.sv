`timescale 1ns/1ps
module tb_mxu_tagged_fp32_pipeline;
  localparam B=64, NUM=7, TAG_W=4;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n=0,start=0,force_req_stall=0,force_rsp_hold=0;
  wire ready,done,protocol_error,flush_req,req_valid,req_ready,rsp_ready;
  reg flush_ack=0,rsp_valid=0;
  wire [TAG_W-1:0] req_tag;
  wire [8:0] req_addr;
  wire [B-1:0] req_mask;
  reg [TAG_W-1:0] rsp_tag=0;
  reg [B*8-1:0] rsp_data=0;
  wire [239:0] acc_flat;
  wire [159:0] fp32_flat;
  wire [15:0] dropped_groups,consumed_groups;
  reg [7:0] qm[0:63],wm[0:319],dam[0:7],dwm[0:9],mem[0:447];
  reg [47:0] expected[0:4];
  reg [31:0] expected_fp32[0:4], ascale[0:0], wscale[0:4];
  reg [15:0] expected_drops[0:0];
  reg busy[0:NUM-1];
  integer delay_count[0:NUM-1];
  integer flush_ticks=0, selected, i, k, lane, seed_arg;
  integer accepted=0, returned=0, job_cycles=0, group_cycles=0;
  integer reorders=0, done_seen=0;
  reg [NUM-1:0] request_seen=0,response_seen=0;
  reg [31:0] prng=32'h39d117a5;
  reg held=0,job_live=0;
  reg [8:0] held_addr=0;
  reg [TAG_W-1:0] held_tag=0;
  string case_a,case_b;

  mxu_tagged_fp32_pipeline #.BURST_BYTES(B),.MAX_OUTSTANDING(4),
                              .TAG_W(TAG_W)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.ready(ready),.done(done),
    .protocol_error(protocol_error),.flush_req(flush_req),
    .flush_ack(flush_ack),.req_valid(req_valid),.req_ready(req_ready),
    .req_tag(req_tag),.req_addr(req_addr),.req_mask(req_mask),
    .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),
    .rsp_data(rsp_data),.acc_flat(acc_flat),.fp32_flat(fp32_flat),
    .dropped_groups(dropped_groups),.consumed_groups(consumed_groups)
  );

  always @(negedge clk) if(rst_n)
    prng <= {prng[30:0],prng[31]^prng[21]^prng[1]^prng[0]};
  assign req_ready=rst_n && !flush_req && !force_req_stall &&
                   prng[2:0]!=3'b000;

  // Responder is not reset by rst_n. It independently cancels old traffic
  // only after a 3-cycle explicit flush handshake, including stale rsp_valid.
  initial begin
    for(i=0;i<NUM;i=i+1) begin busy[i]=0;delay_count[i]=0;end
  end
  always @(posedge clk) begin
    if(flush_req) begin
      if(flush_ticks<3) flush_ticks<=flush_ticks+1;
      else begin
        flush_ack<=1;
        rsp_valid<=0;
        for(k=0;k<NUM;k=k+1) begin
          busy[k]<=0;delay_count[k]<=0;
        end
      end
    end else begin
      flush_ack<=0;flush_ticks<=0;
      if(rsp_valid && rsp_ready) begin
        busy[rsp_tag]<=0;
        rsp_valid<=0;
      end
      if(req_valid && req_ready) begin
        if(req_tag>=NUM || busy[req_tag]) $fatal(1,"responder tag conflict");
        busy[req_tag]<=1;
        delay_count[req_tag]<=8-(req_tag%4);
      end
      for(k=0;k<NUM;k=k+1)
        if(busy[k] && delay_count[k]>0)
          delay_count[k]<=delay_count[k]-1;
      if(!rsp_valid && !force_rsp_hold) begin
        // Choose highest ready tag: deliberately induces OOO completion.
        selected=-1;
        for(k=0;k<NUM;k=k+1)
          if(busy[k] && delay_count[k]==0) selected=k;
        if(selected>=0) begin
          rsp_valid<=1;
          rsp_tag<=selected[TAG_W-1:0];
          for(lane=0;lane<B;lane=lane+1)
            rsp_data[lane*8+:8]<=mem[selected*B+lane];
        end
      end
    end
  end

  // Assert request stability under backpressure; never accept during flush.
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin held<=0;held_addr<=0;held_tag<=0;end
    else begin
      if(held && (!req_valid || req_addr!==held_addr || req_tag!==held_tag))
        $fatal(1,"tagged request changed while stalled");
      held<=req_valid && !req_ready;
      if(req_valid && !req_ready) begin
        held_addr<=req_addr;held_tag<=req_tag;
      end
    end
  end

  always @(posedge clk) begin
    if(protocol_error) $fatal(1,"DUT protocol_error");
    if(flush_req && (req_valid || rsp_ready || ready))
      $fatal(1,"traffic allowed while flush pending");
    if(rst_n && done && !job_live) $fatal(1,"stale done after reset");
    if(rst_n && job_live) begin
      job_cycles=job_cycles+1;
      if(job_cycles>5000) $fatal(1,"tagged job timeout");
      if(req_valid && req_ready) begin
        if(accepted>=NUM || req_tag !== accepted[TAG_W-1:0] ||
           req_addr !== (accepted*B) || request_seen[req_tag])
          $fatal(1,"bad tagged request #%0d tag=%0d",accepted,req_tag);
        for(integer m=0;m<B;m=m+1)
          if(req_mask[m] !== ((req_addr+m)<426))
            $fatal(1,"incorrect head/tail mask at lane %0d",m);
        request_seen[req_tag]=1;
        accepted=accepted+1;
      end
      if(rsp_valid && rsp_ready) begin
        if(rsp_tag>=NUM || !request_seen[rsp_tag] || response_seen[rsp_tag])
          $fatal(1,"duplicate/unknown response tag");
        response_seen[rsp_tag]=1;
        if(rsp_tag!=returned) reorders=reorders+1;
        returned=returned+1;
      end
      if(dut.core.state==2'd1) group_cycles=group_cycles+1;
      if(dut.state==3'd3 && returned!=NUM)
        $fatal(1,"premature core launch");
      if(done) begin
        done_seen=done_seen+1;
        if(!ready || done_seen!=1 || accepted!=NUM || returned!=NUM ||
           group_cycles!=40 || consumed_groups!=40 || reorders==0)
          $fatal(1,"tagged completion/count or ordering failure");
      end
    end
  end

  task automatic load_case(input string path);
    integer n;
    begin
      $readmemh({path,"/q.hex"},qm);
      $readmemh({path,"/w.hex"},wm);
      $readmemh({path,"/da.hex"},dam);
      $readmemh({path,"/dw.hex"},dwm);
      $readmemh({path,"/expected.hex"},expected);
      $readmemh({path,"/expected_fp32.hex"},expected_fp32);
      $readmemh({path,"/ascale.hex"},ascale);
      $readmemh({path,"/wscale.hex"},wscale);
      $readmemh({path,"/drops.hex"},expected_drops);
      for(n=0;n<64;n=n+1) mem[n]=qm[n];
      for(n=0;n<320;n=n+1) mem[64+n]=wm[n];
      for(n=0;n<8;n=n+1) mem[384+n]=dam[n];
      for(n=0;n<10;n=n+1) mem[392+n]=dwm[n];
      for(n=0;n<4;n=n+1) mem[402+n]=ascale[0][n*8+:8];
      for(n=0;n<20;n=n+1) mem[406+n]=wscale[n/4][(n%4)*8+:8];
      for(n=426;n<448;n=n+1) mem[n]=8'hcc;
    end
  endtask

  task automatic start_job;
    begin
      wait(ready);
      @(negedge clk);
      if(done || flush_req || rsp_valid) $fatal(1,"not idle");
      accepted=0;returned=0;job_cycles=0;group_cycles=0;
      reorders=0;done_seen=0;
      request_seen=0;response_seen=0;
      job_live=1;start=1;
      @(negedge clk);start=0;
    end
  endtask

  task automatic finish_job(input integer job_number);
    integer n;
    begin
      wait(done);
      @(negedge clk);
      if(!ready || accepted!=NUM || returned!=NUM ||
         consumed_groups!=40 || dropped_groups!==expected_drops[0])
        $fatal(1,"tagged job completion counters");
      for(n=0;n<5;n=n+1)
        if(acc_flat[n*48+:48] !== expected[n])
          $fatal(1,"tagged result mismatch job=%0d out=%0d",job_number,n);
      for(n=0;n<5;n=n+1)
        if(fp32_flat[n*32+:32] !== expected_fp32[n])
          $fatal(1,"tagged FP32 mismatch job=%0d out=%0d got=%h want=%h",
                 job_number,n,fp32_flat[n*32+:32],expected_fp32[n]);
      $display("PASS_TAGGED_FP32_PIPELINE job=%0d requests=%0d responses=%0d reorders=%0d group_cycles=%0d job_cycles=%0d",
               job_number,accepted,returned,reorders,group_cycles,job_cycles);
      @(negedge clk);
      if(done || done_seen!=1) $fatal(1,"completion pulse incorrect");
      repeat(3) @(negedge clk);
      if(done) $fatal(1,"duplicate done");
      job_live=0;
    end
  endtask

  task automatic abort_and_flush;
    begin
      @(negedge clk);#1 rst_n=0;job_live=0;start=0;
      repeat(3) @(negedge clk);
      #1 rst_n=1;
      wait(ready);
      repeat(3) @(negedge clk);
      if(done || protocol_error || flush_req || rsp_valid)
        $fatal(1,"stale transaction escaped flush");
    end
  endtask

  initial begin
    if(!$value$plusargs("case_a=%s",case_a) ||
       !$value$plusargs("case_b=%s",case_b))
      $fatal(1,"missing case_a or case_b");
    if($value$plusargs("seed=%d",seed_arg)) begin
      if(seed_arg==0) $fatal(1,"invalid seed");
      prng=seed_arg;
    end
    repeat(4) @(negedge clk);#1 rst_n=1;
    wait(ready);
    load_case(case_a);
    force_rsp_hold=1;
    start_job();
    wait(accepted>=3);
    abort_and_flush();
    $display("PASS_TAGGED_FP32_FLUSH outstanding_cancelled");
    force_rsp_hold=0;
    start_job();
    finish_job(1);
    load_case(case_b);
    start_job();
    finish_job(2);
    $display("PASS_TAGGED_FP32_SUITE");
    $finish;
  end
  initial begin #1000000; $fatal(1,"global watchdog");end
endmodule
