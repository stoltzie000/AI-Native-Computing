`timescale 1ns/1ps
module tb_qact_stream_original;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,input_valid=0,output_ready=0;
 reg [31:0] input_data=0;
 wire input_ready,output_valid,output_last,row_done;
 wire [1:0] output_kind;
 wire [7:0] output_data;
 reg [31:0] xmem[0:2047],scalemem[0:31];
 reg [7:0] qmem[0:2047],dmem[0:255];
 integer row,n,index,cycles=0,stalls=0;
 reg held=0;reg [7:0] held_byte;reg [1:0] held_kind;reg held_last;
 string folder;
`ifdef QACT_BRAM
 qact_row_stream_bram dut(.*);
`else
 qact_row_stream_original dut(.*);
`endif
 always @(posedge clk) begin
  cycles<=cycles+1;
  if(cycles>200000)$fatal(1,"stream watchdog");
  if(!rst_n)held<=0;
  else begin
   if(held && (!output_valid || output_data!==held_byte ||
       output_kind!==held_kind || output_last!==held_last))
     $fatal(1,"stream output changed under backpressure");
   held<=output_valid && !output_ready;
   if(output_valid && !output_ready) begin
    held_byte<=output_data;held_kind<=output_kind;held_last<=output_last;
   end
  end
 end
 task automatic send_row(input integer which);
  integer k;
  begin
   for(k=0;k<64;k=k+1)begin
    @(negedge clk);
    #1;
    if(!input_ready || output_valid)$fatal(1,"input not ready row=%0d beat=%0d",which,k);
    input_data=xmem[which*64+k];
    input_valid=1;
    @(posedge clk);#1;
    input_valid=0;input_data=32'hdeadbeef;
   end
   @(negedge clk);#1;
   if(input_ready)$fatal(1,"early next-row acceptance");
   // Illegal early next-row pulse must be ignored.
   input_valid=1;input_data=32'hffffffff;
   @(posedge clk);#1;input_valid=0;
  end
 endtask
 task automatic read_row(input integer which);
  integer k,loops;
  begin
   k=0;loops=0;
   while(k<76)begin
    @(negedge clk);#1;
    output_ready=(loops%7!=3)&&(loops%11!=5);
    if(output_valid)begin
     if(input_ready)$fatal(1,"input accepted before output drained");
     if(output_ready)begin
      if(k<64)begin
       if(output_kind!==2'd0 || output_data!==qmem[which*64+k] || output_last)
        $fatal(1,"Q output mismatch row=%0d index=%0d got=%h want=%h",which,k,output_data,qmem[which*64+k]);
      end else if(k<72)begin
       if(output_kind!==2'd1 || output_data!=={3'd0,dmem[which*8+k-64][4:0]} || output_last)
        $fatal(1,"offset mismatch row=%0d index=%0d data=%h",which,k,output_data);
      end else begin
       if(output_kind!==2'd2 || output_data!==scalemem[which][(k-72)*8+:8] || output_last!==(k==75))
        $fatal(1,"scale mismatch row=%0d index=%0d data=%h",which,k,output_data);
      end
      k=k+1;
     end else stalls=stalls+1;
    end
    @(posedge clk);#1;
    loops=loops+1;
    if(loops>1000)$fatal(1,"output service timeout");
   end
   if(!row_done || !input_ready || output_valid)
    $fatal(1,"missing row-complete handshake row=%0d",which);
   @(posedge clk);#1;
   if(row_done)$fatal(1,"duplicate row_done");
   output_ready=0;
  end
 endtask
 initial begin
  if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing folder");
  $readmemh({folder,"/x.hex"},xmem);
  $readmemh({folder,"/scale.hex"},scalemem);
  $readmemh({folder,"/q.hex"},qmem);
  $readmemh({folder,"/d.hex"},dmem);
  repeat(3)@(negedge clk);#1;rst_n=1;
  for(row=0;row<32;row=row+1)begin
   send_row(row);
   read_row(row);
  end
  if(stalls==0)$fatal(1,"no injected backpressure");
`ifdef QACT_BRAM
  $display("PASS_QACT_STREAM_BRAM rows=32 inputs=2048 outputs=2432 stalls=%0d",stalls);
`else
  $display("PASS_QACT_STREAM_ORIGINAL rows=32 inputs=2048 outputs=2432 stalls=%0d",stalls);
`endif
  $finish;
 end
 initial begin #3000000;$fatal(1,"global timeout");end
endmodule
