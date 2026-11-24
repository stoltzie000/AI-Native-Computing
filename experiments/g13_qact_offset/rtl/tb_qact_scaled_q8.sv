module tb_qact_scaled_q8;
reg [31:0] x=32'hffffffff,inv_group=32'hffffffff;wire [31:0] scaled;wire signed [7:0] q;
reg [31:0] xcase[0:511],invcase[0:511],expected_product[0:511];reg [7:0] expected_q[0:511];
integer i;string folder;
qact_scaled_q8 dut(.x(x),.inv_group(inv_group),.scaled(scaled),.q(q));
initial begin
 if(!$value$plusargs("folder=%s",folder))$fatal(1,"missing folder");
 $readmemh({folder,"/x.hex"},xcase);
 $readmemh({folder,"/inv.hex"},invcase);
 $readmemh({folder,"/product.hex"},expected_product);
 $readmemh({folder,"/q.hex"},expected_q);
 for(i=0;i<512;i=i+1) begin
  x=xcase[i];inv_group=invcase[i];#1;
  if(scaled!==expected_product[i] || q!==expected_q[i])
    $fatal(1,"scaled Q8 mismatch i=%0d x=%h inv=%h product=%h expected=%h q=%h expected=%h",i,x,inv_group,scaled,expected_product[i],q,expected_q[i]);
 end
 $display("PASS_SCALED_Q8_RTL pairs=512");$finish;
end
endmodule
