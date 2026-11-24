`timescale 1ns/1ps
module tb_exact_mxu_int8_core;
    localparam N=5, ACC_W=48;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,start=0;
    reg [64*8-1:0] q_flat=0;
    reg [N*64*8-1:0] w_flat=0;
    reg [8*8-1:0] da_flat=0;
    reg [N*2*8-1:0] dw_flat=0;
    wire ready,done;
    wire [N*ACC_W-1:0] acc_flat;
    wire [15:0] dropped_groups,consumed_groups;
    reg [7:0] qm[0:63],wm[0:N*64-1],dam[0:7],dwm[0:N*2-1];
    reg [47:0] expected[0:N-1];
    reg [15:0] expected_drops[0:0];
    string base_dir;
    integer idx,ticks;
    exact_mxu_int8_core #(.N(N),.ACC_W(ACC_W)) dut(
        .clk(clk),.rst_n(rst_n),.start(start),
        .q_flat(q_flat),.w_flat(w_flat),.da_flat(da_flat),.dw_flat(dw_flat),
        .ready(ready),.done(done),.acc_flat(acc_flat),
        .dropped_groups(dropped_groups),.consumed_groups(consumed_groups)
    );
    initial begin
        if(!$value$plusargs("case=%s",base_dir))$fatal(1,"missing +case=path");
        $readmemh({base_dir,"/q.hex"},qm);
        $readmemh({base_dir,"/w.hex"},wm);
        $readmemh({base_dir,"/da.hex"},dam);
        $readmemh({base_dir,"/dw.hex"},dwm);
        $readmemh({base_dir,"/expected.hex"},expected);
        $readmemh({base_dir,"/drops.hex"},expected_drops);
        for(idx=0;idx<64;idx=idx+1)q_flat[idx*8+:8]=qm[idx];
        for(idx=0;idx<N*64;idx=idx+1)w_flat[idx*8+:8]=wm[idx];
        for(idx=0;idx<8;idx=idx+1)da_flat[idx*8+:8]=dam[idx];
        for(idx=0;idx<N*2;idx=idx+1)dw_flat[idx*8+:8]=dwm[idx];
        repeat(3) @(negedge clk);rst_n=1;
        @(negedge clk);start=1;
        @(negedge clk);start=0;
        ticks=0;
        while(done!==1 && ticks<160)begin
            @(negedge clk);ticks=ticks+1;
        end
        if(done!==1)$fatal(1,"timeout: %s",base_dir);
        if(consumed_groups!==40 || dropped_groups!==expected_drops[0])
            $fatal(1,"group counts mismatch consumed=%0d drop=%0d want=%0d",consumed_groups,dropped_groups,expected_drops[0]);
        for(idx=0;idx<N;idx=idx+1)begin
            if(acc_flat[idx*ACC_W+:ACC_W]!==expected[idx])
                $fatal(1,"integer mismatch case=%s row=%0d got=%h expected=%h",base_dir,idx,acc_flat[idx*ACC_W+:ACC_W],expected[idx]);
        end
        if(ready!==1)$fatal(1,"ready not returned");
        @(negedge clk);
        if(done!==0)$fatal(1,"done pulse lasted >1 cycle");
        $display("PASS_QMM_CORE path=%s groups=%0d dropped=%0d",base_dir,consumed_groups,dropped_groups);
        $finish;
    end
endmodule
