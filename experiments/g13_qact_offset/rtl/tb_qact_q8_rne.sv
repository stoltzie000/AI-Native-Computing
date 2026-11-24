module tb_qact_q8_rne;
reg [31:0] x=32'hffffffff;wire signed [7:0] q;
reg [31:0] words[0:2048];reg [7:0] expected[0:2048];
integer i;string folder;
qact_q8_rne dut(.x(x),.q(q));
initial begin
 if(!$value$plusargs("folder=%s",folder))$fatal(1,"folder missing");
 $readmemh({folder,"/x.hex"},words);$readmemh({folder,"/expected.hex"},expected);
 for(i=0;i<2049;i=i+1) begin x=words[i];#1;
 if(q!==expected[i])$fatal(1,"q8 mismatch i=%0d x=%h actual=%h expected=%h",i,x,q,expected[i]);end
 $display("PASS_Q8_RTL cases=2049");$finish;
end
endmodule
