`timescale 1ns/1ps
// Check exact arithmetic AND observable weight-memory transactions.
module tb_activation_gated_pe;
  parameter ACC_W_TB=32;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0,start=0,stall_enable=0;
  reg [31:0] vector_flat=0;
  reg [127:0] memory_weights=0;
  wire ready,busy,done;
  wire [4*ACC_W_TB-1:0] sums_flat;
  wire mem_req_valid;
  wire [15:0] mem_req_row,mem_req_col;
  reg mem_rsp_valid=0;
  reg [7:0] mem_rsp_weight=0;
  wire [31:0] issued_weight_reads,issued_multiplies,skipped_products;
  integer cycles=0,accepted_reads=0,seed=32'h4c89ab02;
  integer pending=0;reg [7:0] pending_weight=0;
  integer case_id=0,k;
  integer expected_rows[0:3];
  wire mem_req_ready=(!stall_enable || cycles%5 != 0);
  always @(posedge clk) cycles<=cycles+1;

  activation_gated_pe #(.BLOCK_SIZE(4),.DATA_W(8),.ACC_W(ACC_W_TB)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.vector_flat(vector_flat),
    .ready(ready),.busy(busy),.done(done),.sums_flat(sums_flat),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_weight(mem_rsp_weight),
    .issued_weight_reads(issued_weight_reads),.issued_multiplies(issued_multiplies),
    .skipped_products(skipped_products)
  );

  // One outstanding read with deterministic in-order response one pipeline step later.
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      mem_rsp_valid<=0;mem_rsp_weight<=0;
      pending<=0;pending_weight<=0;accepted_reads<=0;
    end else begin
      mem_rsp_valid<=0;
      if(mem_req_valid && mem_req_ready) begin
        if(mem_req_row>=4 || mem_req_col>=4 || pending!=0)
          $fatal(1,"invalid or overlapping request");
        pending_weight<=memory_weights[(mem_req_row*4+mem_req_col)*8+:8];
        pending<=1;
        accepted_reads<=accepted_reads+1;
      end else if(pending==1) begin
        mem_rsp_valid<=1;mem_rsp_weight<=pending_weight;
        pending<=2;
      end else if(pending==2) begin
        pending<=0;
      end
    end
  end

  task calculate_expected;
    integer row,col,acc;
    reg signed [7:0] w,x;
    begin
      for(row=0;row<4;row=row+1) begin
        acc=0;
        for(col=0;col<4;col=col+1) begin
          w=$signed(memory_weights[(row*4+col)*8+:8]);
          x=$signed(vector_flat[col*8+:8]);
          acc=acc+w*x;
        end
        if(ACC_W_TB==16) expected_rows[row]=$signed(acc[15:0]);
        else expected_rows[row]=acc;
      end
    end
  endtask

  task run_case;
    input use_stalls,inject_busy_start;
    integer row,col,active,expected_reads,prior_reads,count,actual;
    reg signed [7:0] activation;
    begin
      if(ready!==1 || busy!==0 || done!==0) $fatal(1,"not ready");
      calculate_expected();
      active=0;
      for(col=0;col<4;col=col+1) begin
        activation=$signed(vector_flat[col*8+:8]);
        if(activation!=0)active=active+1;
      end
      expected_reads=active*4;
      prior_reads=accepted_reads;
      @(negedge clk);stall_enable=use_stalls;start=1;
      @(negedge clk);start=0;
      if(ready!==0 || busy!==1) $fatal(1,"accept handshake failed");
      // Exercise latched activations: mutate external bus after acceptance.
      vector_flat={4{8'h80}};
      if(inject_busy_start)start=1;
      count=0;
      while(done!==1 && count<200) begin
        @(negedge clk);
        count=count+1;
        if(count==1)start=0;
      end
      start=0;
      if(done!==1) $fatal(1,"timeout case=%0d",case_id);
      if(issued_weight_reads!==expected_reads || issued_multiplies!==expected_reads ||
         skipped_products!==(16-expected_reads))
        $fatal(1,"transaction count mismatch case=%0d reads=%0d mult=%0d skips=%0d expected=%0d",
          case_id,issued_weight_reads,issued_multiplies,skipped_products,expected_reads);
      if(accepted_reads-prior_reads!==expected_reads)
        $fatal(1,"external weight reads mismatch case=%0d actual=%0d expected=%0d",
          case_id,accepted_reads-prior_reads,expected_reads);
      for(row=0;row<4;row=row+1) begin
        actual=$signed(sums_flat[row*ACC_W_TB+:ACC_W_TB]);
        if(actual!==expected_rows[row])
          $fatal(1,"numerical mismatch case=%0d row=%0d actual=%0d expected=%0d",
            case_id,row,actual,expected_rows[row]);
      end
      if(ready!==1 || busy!==0) $fatal(1,"ready not returned after done");
      @(negedge clk);
      if(done!==0) $fatal(1,"done pulse too long");
      case_id=case_id+1;
    end
  endtask

  task reset_midflight;
    begin
      vector_flat=32'h01010101;
      @(negedge clk);start=1;stall_enable=0;
      @(negedge clk);start=0;
      repeat(4) @(negedge clk);
      rst_n=0;
      #1;
      if(done!==0 || ready!==1 || issued_weight_reads!==0 ||
         issued_multiplies!==0 || skipped_products!==0)
        $fatal(1,"async reset failed");
      @(negedge clk);rst_n=1;
      repeat(3) @(negedge clk);
      if(done!==0 || ready!==1) $fatal(1,"spurious completion after reset");
    end
  endtask

  initial begin
    if(!(ACC_W_TB==16 || ACC_W_TB==32)) $fatal(1,"invalid test width");
    repeat(3) @(negedge clk);rst_n=1;
    repeat(2) @(negedge clk);
    for(k=0;k<16;k=k+1) memory_weights[k*8+:8]=k+1;
    vector_flat=32'h04fd0201;run_case(0,0); // all four active
    vector_flat=32'h00030002;run_case(1,1); // two zero activations
    vector_flat=0;run_case(0,0);             // all weights skipped
    reset_midflight();
    for(k=0;k<96;k=k+1) begin
      for(integer w=0;w<16;w=w+1) memory_weights[w*8+:8]=$random(seed);
      for(integer x=0;x<4;x=x+1)
        vector_flat[x*8+:8]=((k+x)%3==0)?8'd0:$random(seed);
      run_case((k%4)==0,(k%7)==0);
    end
    $display("PASS v0.8 activation-gated RTL ACC_W=%0d cases=%0d",ACC_W_TB,case_id);
    $finish;
  end
endmodule
