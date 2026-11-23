`timescale 1ns/1ps
// Request/response memory model and independent dense signed arithmetic oracle.
module tb_column_buffered_pe;
  parameter ROWS_TB=64;
  parameter LANES_TB=4;
  parameter ACC_W_TB=32;
  localparam COLS=4, DATA_W=8;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0,start=0,stall=0;
  reg [COLS*DATA_W-1:0] vector_flat=0;
  reg [ROWS_TB*COLS*DATA_W-1:0] matrix_column_major=0;
  wire ready,busy,done,mem_req_valid;
  wire [15:0] mem_req_col;
  wire [ROWS_TB*ACC_W_TB-1:0] sums_flat;
  reg mem_rsp_valid=0;
  reg [ROWS_TB*DATA_W-1:0] mem_rsp_column=0;
  wire [31:0] issued_column_reads,fetched_weight_elements,skipped_weight_elements,active_compute_cycles;
  integer cycle_clock=0,accepted_reads=0,pending=0,seed=32'h2211aa55;
  reg [ROWS_TB*DATA_W-1:0] pending_column=0;
  integer expected[0:ROWS_TB-1];
  integer case_id=0;
  integer i,j,k;
  wire mem_req_ready=!stall || (cycle_clock%5 != 0);
  always @(posedge clk)cycle_clock<=cycle_clock+1;

  column_buffered_pe #(.ROWS(ROWS_TB),.COLS(COLS),.DATA_W(DATA_W),
    .ACC_W(ACC_W_TB),.LANES(LANES_TB)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.vector_flat(vector_flat),
    .ready(ready),.busy(busy),.done(done),.sums_flat(sums_flat),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_col(mem_req_col),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_column(mem_rsp_column),.issued_column_reads(issued_column_reads),
    .fetched_weight_elements(fetched_weight_elements),
    .skipped_weight_elements(skipped_weight_elements),
    .active_compute_cycles(active_compute_cycles)
  );

  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin
      mem_rsp_valid<=0;mem_rsp_column<=0;
      pending<=0;pending_column<=0;accepted_reads<=0;
    end else begin
      mem_rsp_valid<=0;
      if(mem_req_valid && mem_req_ready)begin
        if(mem_req_col>=COLS || pending!=0)
          $fatal(1,"invalid request or overlapping response");
        pending_column<=matrix_column_major[mem_req_col*ROWS_TB*8+:ROWS_TB*8];
        pending<=1;accepted_reads<=accepted_reads+1;
      end else if(pending==1)begin
        mem_rsp_valid<=1;
        mem_rsp_column<=pending_column;
        pending<=2;
      end else if(pending==2) pending<=0;
    end
  end

  task calculate_expected;
    integer row,col,total;
    reg signed[7:0] w,a;
    begin
      for(row=0;row<ROWS_TB;row=row+1)begin
        total=0;
        for(col=0;col<COLS;col=col+1)begin
          w=$signed(matrix_column_major[(col*ROWS_TB+row)*8+:8]);
          a=$signed(vector_flat[col*8+:8]);
          total=total+w*a;
        end
        expected[row]=ACC_W_TB==16?$signed(total[15:0]):total;
      end
    end
  endtask

  task run_case;
    input stalls,inject_busy_start;
    integer col,row,active,baseline,ticks,result;
    reg signed[7:0] a;
    begin
      if(ready!==1 || busy!==0 || done!==0) $fatal(1,"not idle before case %0d",case_id);
      calculate_expected();active=0;
      for(col=0;col<COLS;col=col+1)begin
        a=$signed(vector_flat[col*8+:8]);
        if(a!=0)active=active+1;
      end
      baseline=accepted_reads;
      @(negedge clk);stall=stalls;start=1;
      @(negedge clk);start=0;
      if(ready!==0 || busy!==1) $fatal(1,"did not accept start");
      vector_flat={COLS{8'h80}}; // mutate external input AFTER acceptance
      if(inject_busy_start)start=1; // must be ignored while busy
      ticks=0;
      while(done!==1 && ticks<1200)begin
        @(negedge clk);ticks=ticks+1;
        if(ticks==1)start=0;
      end
      start=0;
      if(done!==1)$fatal(1,"timeout rows=%0d lanes=%0d case=%0d",ROWS_TB,LANES_TB,case_id);
      if(issued_column_reads!==active ||
         fetched_weight_elements!==(active*ROWS_TB) ||
         skipped_weight_elements!==((COLS-active)*ROWS_TB) ||
         active_compute_cycles!==(active*ROWS_TB/LANES_TB))
        $fatal(1,"counter mismatch case=%0d reads=%0d fetch=%0d skip=%0d MACcycles=%0d active=%0d",case_id,
          issued_column_reads,fetched_weight_elements,skipped_weight_elements,active_compute_cycles,active);
      if(accepted_reads-baseline!==active)$fatal(1,"physical request count mismatch");
      for(row=0;row<ROWS_TB;row=row+1)begin
        result=$signed(sums_flat[row*ACC_W_TB+:ACC_W_TB]);
        if(result!==expected[row])
          $fatal(1,"signed arithmetic mismatch case=%0d row=%0d got=%0d expected=%0d",case_id,row,result,expected[row]);
      end
      if(ready!==1 || busy!==0) $fatal(1,"invalid completion handshake");
      @(negedge clk);
      if(done!==0)$fatal(1,"done pulse >1 cycle");
      case_id=case_id+1;
    end
  endtask

  task reset_inflight;
    begin
      vector_flat=32'h01010101;
      @(negedge clk);start=1;stall=0;
      @(negedge clk);start=0;
      repeat(8)@(negedge clk);
      rst_n=0;#1;
      if(ready!==1 || busy!==0 || done!==0 ||
         issued_column_reads!==0 || active_compute_cycles!==0)
        $fatal(1,"mid-flight asynchronous reset failed");
      @(negedge clk);rst_n=1;
      repeat(3) @(negedge clk);
      vector_flat=0;
      run_case(0,0);
    end
  endtask

  initial begin
    if(ROWS_TB%LANES_TB || ROWS_TB<1 || LANES_TB<1) $fatal(1,"bad test parameter");
    repeat(3)@(negedge clk);rst_n=1;
    repeat(2)@(negedge clk);
    for(i=0;i<ROWS_TB*COLS;i=i+1)matrix_column_major[i*8+:8]=i;
    vector_flat=32'h00020301;run_case(0,1); // 3 active
    vector_flat=32'h02000001;run_case(1,1); // 2 active
    vector_flat=0;run_case(0,0); // no memory reads
    for(i=0;i<ROWS_TB*COLS;i=i+1)matrix_column_major[i*8+:8]=8'h80;
    vector_flat=32'h80808080;run_case(1,0); // signed overflow at ACC16
    reset_inflight();
    for(k=0;k<90;k=k+1)begin
      for(i=0;i<ROWS_TB*COLS;i=i+1)matrix_column_major[i*8+:8]=$random(seed);
      for(j=0;j<COLS;j=j+1)
        vector_flat[j*8+:8]=((k+j)%3==0)?8'd0:$random(seed);
      run_case((k%5)==0,(k%7)==0);
    end
    $display("PASS v1.0 burst-buffered PE ROWS=%0d LANES=%0d ACC=%0d cases=%0d",ROWS_TB,LANES_TB,ACC_W_TB,case_id);
    $finish;
  end
endmodule
