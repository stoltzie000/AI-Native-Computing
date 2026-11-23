`timescale 1ns/1ps
// Independent dense oracle, actual accepted column-request count, request stalls.
// Memory returns N signed weights per column from a column-major layout.
module tb_column_gated_pe;
  parameter ACC_W_TB=32;
  reg clk=0;always #5 clk=~clk;
  reg rst_n=0,start=0,stall=0;
  reg [31:0] vector_flat=0;
  reg [127:0] weights_column_major=0;
  wire ready,busy,done,mem_req_valid;
  wire [15:0] mem_req_col;
  wire [4*ACC_W_TB-1:0] sums_flat;
  reg mem_rsp_valid=0;
  reg [31:0] mem_rsp_column=0;
  wire [31:0] issued_column_reads,issued_weight_elements,skipped_weight_elements,active_compute_cycles;
  integer cycles=0,accepted_columns=0,seed=32'h1984abcd;
  integer pending=0;
  reg [31:0] pending_data=0;
  integer expected_rows[0:3];
  integer case_id=0,k;
  wire mem_req_ready=!stall || (cycles%5 != 0);
  always @(posedge clk)cycles<=cycles+1;

  column_gated_pe #(.N(4),.DATA_W(8),.ACC_W(ACC_W_TB)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.vector_flat(vector_flat),
    .ready(ready),.busy(busy),.done(done),.sums_flat(sums_flat),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_col(mem_req_col),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_column(mem_rsp_column),
    .issued_column_reads(issued_column_reads),
    .issued_weight_elements(issued_weight_elements),
    .skipped_weight_elements(skipped_weight_elements),
    .active_compute_cycles(active_compute_cycles)
  );

  always @(posedge clk or negedge rst_n) begin
    if(!rst_n)begin
      mem_rsp_valid<=0;mem_rsp_column<=0;pending<=0;pending_data<=0;
      accepted_columns<=0;
    end else begin
      mem_rsp_valid<=0;
      if(mem_req_valid && mem_req_ready)begin
        if(mem_req_col>=4 || pending!=0) $fatal(1,"bad or overlapping column read");
        pending_data<=weights_column_major[mem_req_col*32+:32];
        accepted_columns<=accepted_columns+1;
        pending<=1;
      end else if(pending==1)begin
        mem_rsp_valid<=1;
        mem_rsp_column<=pending_data;
        pending<=2;
      end else if(pending==2) pending<=0;
    end
  end

  task expected_dense;
    integer row,col,acc;
    reg signed [7:0] w,x;
    begin
      for(row=0;row<4;row=row+1)begin
        acc=0;
        for(col=0;col<4;col=col+1)begin
          w=$signed(weights_column_major[(col*4+row)*8+:8]);
          x=$signed(vector_flat[col*8+:8]);
          acc=acc+w*x;
        end
        if(ACC_W_TB==16)expected_rows[row]=$signed(acc[15:0]);
        else expected_rows[row]=acc;
      end
    end
  endtask

  task run_case;
    input use_stalls,inject_busy_start;
    integer col,row,active,baseline,actual,ticks;
    reg signed[7:0] x;
    begin
      if(ready!==1 || done!==0) $fatal(1,"not idle before case %0d",case_id);
      expected_dense();
      active=0;
      for(col=0;col<4;col=col+1)begin
        x=$signed(vector_flat[col*8+:8]);
        if(x!=0)active=active+1;
      end
      baseline=accepted_columns;
      @(negedge clk);stall=use_stalls;start=1;
      @(negedge clk);start=0;
      if(ready!==0 || busy!==1) $fatal(1,"not accepted");
      vector_flat={4{8'h80}};
      if(inject_busy_start)start=1;
      ticks=0;
      while(done!==1 && ticks<100)begin
        @(negedge clk);ticks=ticks+1;
        if(ticks==1)start=0;
      end
      start=0;
      if(done!==1)$fatal(1,"timeout case=%0d",case_id);
      if(issued_column_reads!==active ||
         issued_weight_elements!==active*4 ||
         skipped_weight_elements!==(16-active*4) ||
         active_compute_cycles!==active)
         $fatal(1,"column/multiply/skip count mismatch case=%0d",case_id);
      if(accepted_columns-baseline!==active)
         $fatal(1,"external column requests mismatch case=%0d",case_id);
      for(row=0;row<4;row=row+1)begin
        actual=$signed(sums_flat[row*ACC_W_TB+:ACC_W_TB]);
        if(actual!==expected_rows[row])
          $fatal(1,"bad result case=%0d row=%0d got=%0d expected=%0d",case_id,row,actual,expected_rows[row]);
      end
      if(ready!==1 || busy!==0) $fatal(1,"wrong done state");
      @(negedge clk);
      if(done!==0) $fatal(1,"done pulse too long");
      case_id=case_id+1;
    end
  endtask

  task reset_inflight;
    begin
      vector_flat=32'h01010101;
      @(negedge clk);start=1;stall=0;
      @(negedge clk);start=0;
      repeat(4) @(negedge clk);
      rst_n=0;#1;
      if(ready!==1 || done!==0 || issued_column_reads!==0)
        $fatal(1,"async reset state failure");
      @(negedge clk);rst_n=1;
      repeat(3) @(negedge clk);
      weights_column_major=0;vector_flat=0;
      run_case(0,0);
    end
  endtask

  initial begin
    if(!(ACC_W_TB==16 || ACC_W_TB==32))$fatal(1,"invalid accum width");
    repeat(3) @(negedge clk);rst_n=1;
    repeat(2) @(negedge clk);
    for(k=0;k<16;k=k+1)weights_column_major[k*8+:8]=k+1;
    vector_flat=32'h01020304;run_case(0,1); // four requests, 16 weights
    vector_flat=32'h00010200;run_case(1,1); // two requests, 8 weights
    vector_flat=0;run_case(0,0);             // zero requests
    reset_inflight();
    for(k=0;k<128;k=k+1)begin
      for(integer i=0;i<16;i=i+1)weights_column_major[i*8+:8]=$random(seed);
      for(integer j=0;j<4;j=j+1)
        vector_flat[j*8+:8]=((k+j)%3==0)?8'd0:$random(seed);
      run_case((k%5)==0,(k%7)==0);
    end
    $display("PASS v0.9 column-gated RTL ACC_W=%0d cases=%0d",ACC_W_TB,case_id);
    $finish;
  end
endmodule
