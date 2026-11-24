// G1.2 research: exact integer kernel for openTPU MM WF0 INT8 D32, KB2.
// Inputs are ALREADY QUANTIZED by upstream QACT and need stable during RUN.
// There is NO memory controller, DMA, QACT circuit or FP32 epilogue here.
// One 8-element signed INT8 group dot product per clock, 5 outputs x 8 groups.
module exact_mxu_int8_core #(
    parameter N=5, parameter ACC_W=48
)(
    input wire clk, rst_n, start,
    input wire [64*8-1:0] q_flat,
    input wire [N*64*8-1:0] w_flat,
    input wire [8*8-1:0] da_flat,
    input wire [N*2*8-1:0] dw_flat,
    output wire ready,
    output reg done,
    output wire [N*ACC_W-1:0] acc_flat,
    output reg [15:0] dropped_groups,
    output reg [15:0] consumed_groups
);
    localparam IDLE=2'd0, RUN=2'd1, FINISH=2'd2;
    reg [1:0] state;
    reg [15:0] row_idx;
    reg [2:0] group_idx;
    reg signed [ACC_W-1:0] acc [0:N-1];
    assign ready = (state == IDLE);
    wire [7:0] da = da_flat[group_idx*8+:8];
    wire [7:0] dw = dw_flat[(row_idx*2 + (group_idx >> 2))*8+:8];
    wire signed [9:0] shift = 10'sd16 - $signed({2'b00,dw}) - $signed({2'b00,da});
    wire signed [15:0] product [0:7];
    genvar i;
    generate for (i=0;i<8;i=i+1) begin: MULT
       wire signed [7:0] a=$signed(q_flat[(group_idx*8+i)*8+:8]);
       wire signed [7:0] w=$signed(w_flat[(row_idx*64+group_idx*8+i)*8+:8]);
       assign product[i] = a*w;
    end
    for(i=0;i<N;i=i+1)begin: OUT
        assign acc_flat[i*ACC_W+:ACC_W]=acc[i];
    end
    endgenerate
    integer p;
    reg signed [31:0] dot;
    always @* begin
        dot=32'sd0;
        for(p=0;p<8;p=p+1)
            dot=dot+$signed({{16{product[p][15]}},product[p]});
    end
    wire signed [ACC_W-1:0] wide_dot=dot;
    wire signed [ACC_W-1:0] term=shift<0 ? {ACC_W{1'b0}} : (wide_dot <<< shift);
    integer r;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)begin
            state<=IDLE; row_idx<=0; group_idx<=0;done<=0;
            dropped_groups<=0;consumed_groups<=0;
            for(r=0;r<N;r=r+1) acc[r]<=0;
        end else begin
            done<=0;
            case(state)
                IDLE: if(start)begin
                    row_idx<=0;group_idx<=0;
                    dropped_groups<=0;consumed_groups<=0;
                    for(r=0;r<N;r=r+1) acc[r]<=0;
                    state<=RUN;
                end
                RUN: begin
                    acc[row_idx] <= acc[row_idx]+term;
                    consumed_groups<=consumed_groups+1;
                    if(shift<0)dropped_groups<=dropped_groups+1;
                    if(group_idx==7)begin
                        group_idx<=0;
                        if(row_idx==N-1) state<=FINISH;
                        else row_idx<=row_idx+1;
                    end else group_idx<=group_idx+1;
                end
                FINISH: begin
                    done<=1;state<=IDLE;
                end
                default:state<=IDLE;
            endcase
        end
    end
`ifndef SYNTHESIS
    initial if(N<1 || N>65535 || ACC_W<40) $fatal(1,"unsupported geometry");
`endif
endmodule
