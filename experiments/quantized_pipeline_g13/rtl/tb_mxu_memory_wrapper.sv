`timescale 1ns/1ps
module tb_mxu_memory_wrapper;
 reg clk=0; always #5 clk=~clk;
 reg rst_n=0,start=0;
 wire ready,done,req_valid,rsp_ready;
 reg req_ready=0,rsp_valid=0;
 wire [8:0] req_addr;
 reg [7:0] rsp_data=0;
 wire [239:0] acc_flat;
 wire [15:0] dropped_groups,consumed_groups;
 reg [7:0] qm[0:63],wm[0:319],dam[0:7],dwm[0:9],mem[0:401];
 reg [47:0] expected[0:4];
 reg [15:0] expected_drops[0:0];
 string base_dir;
 integer i,cycles=0,reads=0,responses=0,delay_count=0,mode=0;
 reg pending=0;
 mxu_memory_wrapper dut(.*);
 always @(negedge clk) begin
  req_ready= rst_n && !pending && !rsp_valid && (mode==0 || cycles%5!=0);
  if(pending && !rsp_valid) begin
   if(delay_count==0) rsp_valid=1;
   else delay_count=delay_count-1;
  end
 end
 always @(posedge clk) begin
  if(rst_n) begin
   cycles=cycles+1;
   if(req_valid && req_ready) begin
    if(req_addr!==reads[8:0] || pending) $fatal(1,"request order");
    rsp_data<=mem[req_addr]; pending<=1; reads<=reads+1;
    delay_count<=mode==0?0:(reads%7);
   end
   if(rsp_valid && rsp_ready) begin
    pending<=0; rsp_valid<=0; responses<=responses+1;
   end
   if(consumed_groups!=0 && responses!=402) $fatal(1,"premature compute");
   if(cycles>8000) $fatal(1,"timeout");
  end
 end
 initial begin
  if(!$value$plusargs("case=%s",base_dir)) $fatal(1,"missing case");
  if(!$value$plusargs("mode=%d",mode)) mode=0;
  $readmemh({base_dir,"/q.hex"},qm);
  $readmemh({base_dir,"/w.hex"},wm);
  $readmemh({base_dir,"/da.hex"},dam);
  $readmemh({base_dir,"/dw.hex"},dwm);
  $readmemh({base_dir,"/expected.hex"},expected);
  $readmemh({base_dir,"/drops.hex"},expected_drops);
  for(i=0;i<64;i=i+1) mem[i]=qm[i];
  for(i=0;i<320;i=i+1) mem[64+i]=wm[i];
  for(i=0;i<8;i=i+1) mem[384+i]=dam[i];
  for(i=0;i<10;i=i+1) mem[392+i]=dwm[i];
  repeat(3) @(negedge clk); #1 rst_n=1;
  @(negedge clk); #1 start=1;
  @(negedge clk); #1 start=0;
  wait(done); @(negedge clk); #1;
  if(reads!=402 || responses!=402 || consumed_groups!=40 ||
     dropped_groups!==expected_drops[0] || !ready) $fatal(1,"counts");
  for(i=0;i<5;i=i+1)
   if(acc_flat[i*48+:48]!==expected[i]) $fatal(1,"output mismatch");
  $display("PASS_MEMORY_RTL mode=%0d cycles=%0d",mode,cycles);
  $finish;
 end
endmodule
