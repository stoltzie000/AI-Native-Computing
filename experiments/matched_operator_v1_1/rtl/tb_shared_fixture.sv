`timescale 1ns/1ps
// Shared fixed signed INT8 64x4 operator, exact ACC32 reference from Python.
// Loads *same source fixture* used by openTPU ISA/RTL VOP adapter.
module tb_shared_fixture;
  parameter LANES_TB=4;
  localparam ROWS=64, COLS=4, DATA_W=8, ACC_W=32;
  reg clk=0;always #5 clk=~clk;
  reg rst_n=0,start=0;
  reg [COLS*DATA_W-1:0] vector_flat=0;
  reg [ROWS*COLS*DATA_W-1:0] matrix_column_major=0;
  reg [7:0] weights [0:ROWS*COLS-1];
  reg [7:0] vec_mem [0:COLS-1];
  reg [31:0] golden [0:ROWS-1];
  reg [1023:0] weight_path,vector_path,golden_path;
  reg [ROWS*DATA_W-1:0] pending_column=0,mem_rsp_column=0;
  reg mem_rsp_valid=0;
  reg [31:0] clock_count=0;
  reg [1:0] pending=0;
  integer accepted_reads=0;
  wire mem_req_valid,mem_req_ready,ready,busy,done;
  wire [15:0] mem_req_col;
  wire [ROWS*ACC_W-1:0] sums_flat;
  wire [31:0] issued_column_reads,fetched_weight_elements,skipped_weight_elements,active_compute_cycles;
  assign mem_req_ready=(clock_count%5 != 0); // deterministic backpressure
  always @(posedge clk) clock_count<=clock_count+1;
  column_buffered_pe #(.ROWS(ROWS),.COLS(COLS),.DATA_W(DATA_W),.ACC_W(ACC_W),.LANES(LANES_TB)) dut (
    .clk(clk),.rst_n(rst_n),.start(start),.vector_flat(vector_flat),
    .ready(ready),.busy(busy),.done(done),.sums_flat(sums_flat),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_col(mem_req_col),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_column(mem_rsp_column),.issued_column_reads(issued_column_reads),
    .fetched_weight_elements(fetched_weight_elements),
    .skipped_weight_elements(skipped_weight_elements),.active_compute_cycles(active_compute_cycles)
  );
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n)begin
      mem_rsp_valid<=0;mem_rsp_column<=0;pending<=0;pending_column<=0;accepted_reads<=0;
    end else begin
      mem_rsp_valid<=0;
      if(mem_req_valid && mem_req_ready)begin
        if(mem_req_col>=COLS || pending!=0)$fatal(1,"overlap or invalid request");
        pending_column<=matrix_column_major[mem_req_col*ROWS*DATA_W+:ROWS*DATA_W];
        pending<=1;
        accepted_reads<=accepted_reads+1;
      end else if(pending==1) begin
        mem_rsp_valid<=1;
        mem_rsp_column<=pending_column;
        pending<=2;
      end else if(pending==2) pending<=0;
    end
  end
  integer row,col,ticks,active;
  initial begin
    if(!$value$plusargs("WFILE=%s",weight_path) ||
       !$value$plusargs("XFILE=%s",vector_path) ||
       !$value$plusargs("GFILE=%s",golden_path))
      $fatal(1,"missing fixture file plusarg");
    $readmemh(weight_path,weights);
    $readmemh(vector_path,vec_mem);
    $readmemh(golden_path,golden);
    active=0;
    for(col=0;col<COLS;col=col+1)begin
      vector_flat[col*DATA_W+:DATA_W]=vec_mem[col];
      if(vec_mem[col]!=0)active=active+1;
    end
    for(col=0;col<COLS;col=col+1)
      for(row=0;row<ROWS;row=row+1)
        matrix_column_major[(col*ROWS+row)*DATA_W+:DATA_W]=weights[col*ROWS+row];
    repeat(4)@(negedge clk);rst_n=1;
    repeat(2)@(negedge clk);
    if(ready!==1)$fatal(1,"not ready");
    @(negedge clk);start=1;
    @(negedge clk);start=0;
    if(busy!==1)$fatal(1,"busy not set");
    // Confirm snapshot behavior: original fixture vector cannot change in flight.
    vector_flat={COLS{8'h7f}};
    ticks=0;
    while(done!==1 && ticks<2000)begin @(negedge clk);ticks=ticks+1;end
    if(done!==1)$fatal(1,"timeout");
    for(row=0;row<ROWS;row=row+1)begin
      if(sums_flat[row*ACC_W+:ACC_W]!==golden[row])
        $fatal(1,"result mismatch row=%0d got=%0d expected=%0d",row,
          $signed(sums_flat[row*ACC_W+:ACC_W]),$signed(golden[row]));
    end
    if(accepted_reads!==active || issued_column_reads!==active ||
       fetched_weight_elements!==(ROWS*active) ||
       skipped_weight_elements!==(ROWS*(COLS-active)) ||
       active_compute_cycles!==(ROWS*active/LANES_TB))
      $fatal(1,"wrong counters active=%0d requests=%0d cycles=%0d",active,issued_column_reads,active_compute_cycles);
    @(negedge clk);
    if(done!==0 || busy!==0 || ready!==1)$fatal(1,"bad done/ready pulse");
    $display("PASS_SHARED_INT8_RTL LANES=%0d ACTIVE=%0d COMPUTE_CYCLES=%0d",LANES_TB,active,active_compute_cycles);
    $finish;
  end
endmodule
