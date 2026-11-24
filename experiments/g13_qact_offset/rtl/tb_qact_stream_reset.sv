`timescale 1ns/1ps
module tb_qact_stream_reset;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,input_valid=0,output_ready=0;
 reg [31:0] input_data=0,row_inverse=0;
 wire input_ready,output_valid,output_is_offset,output_last,row_done;
 wire [7:0] output_data;
 reg [31:0] xmem[0:2047],invmem[0:31];
 reg [7:0] qmem[0:2047],dmem[0:255];
 integer i,complete=0,aborted=0;
 string folder;
 qact_row_stream_wrapper dut(.*);
 task automatic feed(input integer row,input integer amount);
  integer k;
  begin
   for(k=0;k<amount;k=k+1)begin
    @(negedge clk);#1;
    if(!input_ready||output_valid)$fatal(1,"input not ready %0d:%0d",row,k);
    input_valid=1;input_data=xmem[row*64+k];
    row_inverse=invmem[row];
    @(posedge clk);#1;
    input_valid=0;input_data=32'hffffffff;row_inverse=0;
   end
  end
 endtask
 task automatic reset_and_verify;
  begin
   @(negedge clk);#1;rst_n=0;input_valid=0;output_ready=0;
   #1;
   if(!input_ready||output_valid||row_done)$fatal(1,"reset did not abort pending row");
   repeat(3)@(negedge clk);#1;rst_n=1;
   repeat(3)@(negedge clk);#1;
   if(!input_ready||output_valid||row_done)$fatal(1,"stale output after reset");
   aborted=aborted+1;
  end
 endtask
 task automatic drain(input integer row,input integer first,input integer count);
  integer k;
  begin
   for(k=first;k<first+count;k=k+1)begin
    wait(output_valid);
    @(negedge clk);#1;output_ready=1;
    if(k<64)begin
     if(output_data!==qmem[row*64+k]||output_is_offset||output_last)
      $fatal(1,"quantized replay mismatch row=%0d k=%0d",row,k);
    end else begin
     if(output_data!=={3'd0,dmem[row*8+k-64][4:0]}||!output_is_offset||
        output_last!==(k==71))
      $fatal(1,"metadata replay mismatch row=%0d k=%0d",row,k);
    end
    @(posedge clk);#1;
   end
   output_ready=0;
   if(first+count==72)begin
    if(!row_done || !input_ready || output_valid)
      $fatal(1,"final completion not unique");
    @(posedge clk);#1;
    if(row_done)$fatal(1,"duplicate row_done");
    complete=complete+1;
   end
  end
 endtask
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing fixture");
  $readmemh({folder,"/x.hex"},xmem);$readmemh({folder,"/inv.hex"},invmem);
  $readmemh({folder,"/q.hex"},qmem);$readmemh({folder,"/d.hex"},dmem);
  repeat(3)@(negedge clk);#1;rst_n=1;
  // 1: Partial input is cancelled; next full row must match.
  feed(0,17);reset_and_verify();
  feed(1,64);drain(1,0,72);
  // 2: Abort active mathematical computation after at least 16 Q8 products.
  feed(2,64);
  wait(dut.core.state==2'd2 && dut.core.idx==7'd16);
  reset_and_verify();
  feed(3,64);drain(3,0,72);
  // 3: Abort a stalled output transaction after five accepted bytes.
  feed(4,64);drain(4,0,5);
  wait(output_valid);
  repeat(6)begin
   @(negedge clk);#1;
   if(!output_valid||output_ready||output_is_offset||output_data!==qmem[4*64+5])
     $fatal(1,"stalled output unstable prior to reset");
  end
  reset_and_verify();
  feed(5,64);drain(5,0,72);
  if(complete!=3 || aborted!=3)$fatal(1,"abort/recovery accounting");
  $display("PASS_QACT_STREAM_RESET aborted=3 recovered=3 outputs=216");
  $finish;
 end
 initial begin #3000000;$fatal(1,"global timeout");end
endmodule
