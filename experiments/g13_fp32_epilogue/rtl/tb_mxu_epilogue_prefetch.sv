`timescale 1ns/1ps
module tb_mxu_epilogue_prefetch;
    reg clk=0, rst_n=0, start=0;
    always #5 clk = !clk;
    reg [239:0] acc_flat;
    reg [159:0] weight_scale_flat;
    reg [31:0] activation_scale;
    wire original_ready, original_done, ready, done;
    wire [159:0] original_result, result_flat, parallel_result;
    mxu_integer_epilogue_serial original(.ready(original_ready), .done(original_done),
                                         .result_flat(original_result), .*);
    mxu_integer_epilogue_serial #(.PREFETCH_CONVERSION(1)) candidate(.*);
    mxu_integer_epilogue parallel_ref(.result_flat(parallel_result), .*);
    reg [31:0] random_state=32'h9cc59371;
    integer completions=0, aborts=0, checked_cycles=0;

    function automatic [31:0] advance(input [31:0] x);
        reg [31:0] t;
        begin
            t=x^(x<<13); t=t^(t>>17); advance=t^(t<<5);
        end
    endfunction
    task automatic check_outputs;
        begin
            if ({ready,done,result_flat} !== {original_ready,original_done,original_result})
                $fatal(1,"changed interface or partial result at cycle %0d",checked_cycles);
            checked_cycles=checked_cycles+1;
        end
    endtask
    task automatic reset_job;
        begin
            @(negedge clk); #1; rst_n=0; start=0; #1; check_outputs();
            if (ready !== 1 || done !== 0 || result_flat !== 0) $fatal(1,"reset contract");
            repeat(2) @(posedge clk);
            @(negedge clk); #1; rst_n=1;
        end
    endtask
    task automatic run_job(input integer number, input integer abort_cycle);
        integer lane, cycle;
        reg [159:0] expected;
        begin
            @(negedge clk); #1;
            for(lane=0;lane<5;lane=lane+1)begin
                random_state=advance(random_state); acc_flat[lane*48+:32]=random_state;
                random_state=advance(random_state); acc_flat[lane*48+32+:16]=random_state[15:0];
                random_state=advance(random_state); weight_scale_flat[lane*32+:32]=random_state;
            end
            random_state=advance(random_state); activation_scale=random_state;
            if(number%8==0)begin
                acc_flat={48'h800000000000,48'h7fffffffffff,48'd16777219,48'd16777217,48'd0};
                weight_scale_flat={32'h3f800000,32'hbf800000,32'h7f800000,32'h00000001,32'h80000000};
                activation_scale=32'h3f800000;
            end
            #1; expected=parallel_result;
            if (ready !== 1) $fatal(1,"job %0d not accepted",number);
            start=1;
            @(posedge clk); #1; start=0; check_outputs();
            acc_flat=~acc_flat; weight_scale_flat=~weight_scale_flat; activation_scale=~activation_scale;
            for(cycle=0;cycle<11;cycle=cycle+1)begin
                if(cycle==abort_cycle)begin reset_job(); aborts=aborts+1; disable run_job; end
                start=(cycle==3);
                @(posedge clk); #1; check_outputs();
                if (done !== (cycle==10) || ready !== (cycle==10)) $fatal(1,"latency %0d",cycle);
            end
            start=0;
            if (result_flat !== expected) $fatal(1,"parallel reference mismatch job=%0d",number);
            completions=completions+1;
        end
    endtask
    integer i;
    initial begin
        reset_job();
        for(i=0;i<512;i=i+1)run_job(i,-1);
        for(i=0;i<11;i=i+1)begin run_job(i+512,i); run_job(i+523,-1); end
        @(posedge clk); #1; check_outputs();
        if(completions!=523 || aborts!=11 || done) $fatal(1,"completion accounting");
        $display("PASS_EPILOGUE_PREFETCH completed=%0d outputs=%0d aborts=%0d cycles_per_job=11 compared_cycles=%0d",
                 completions,completions*5,aborts,checked_cycles);
        $finish;
    end
    initial begin #1000000; $fatal(1,"watchdog"); end
endmodule
