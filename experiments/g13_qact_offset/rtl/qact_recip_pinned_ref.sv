// Research reference adapter to unmodified openTPU RTL, Apache-2.0.
// Source pin: FeSens/openTPU@d84db55712aba0d40811d7762cb052f05d55b7e5.
// Not an original reciprocal datapath or area/performance claim.
module qact_recip_pinned_ref(input logic [31:0] x,output logic [31:0] y);
 assign y=otpu_fp::fp_recip(x);
endmodule
