`timescale 1ns/1ps
module tb_qact_mxu_stream_bram;
    reg clk=0, rst_n=0, input_valid=0, output_ready=0;
    always #5 clk = !clk;
    reg [31:0] input_data=0;
    wire input_ready, output_valid, output_last;
    wire [31:0] output_data;
    qact_mxu_stream_bram dut(.*);

    reg [31:0] frames[0:3647], results[0:119], scales[0:23];
    reg [7:0] codes[0:1535], offsets[0:191];
    reg [47:0] accumulators[0:119];
    reg [15:0] drops[0:23];
    reg held=0, held_last;
    reg [31:0] held_data;
    integer transfers=0, stalls=0, last_stalls=0, gaps=0, first_latency=0;
    string folder;

    always @(posedge clk) begin
        if (!rst_n) held <= 0;
        else begin
            if (held && (output_valid !== 1 || output_last !== held_last || output_data !== held_data))
                $fatal(1,"result changed while stalled");
            held <= output_valid && !output_ready;
            held_last <= output_last;
            held_data <= output_data;
        end
    end

    task automatic check_intermediates(input integer row);
        integer k;
        begin
            if (dut.activation_scale !== scales[row] || dut.consumed_groups !== 16'd40 ||
                dut.dropped_groups !== drops[row]) $fatal(1,"scale/group counts row=%0d",row);
            for (k=0;k<64;k=k+1)
                if (dut.codes[k*8+:8] !== codes[row*64+k]) $fatal(1,"Q8 row=%0d index=%0d",row,k);
            for (k=0;k<8;k=k+1)
                if (dut.activation_offsets[k*8+:8] !== offsets[row*8+k]) $fatal(1,"offset row=%0d index=%0d",row,k);
            for (k=0;k<5;k=k+1)
                if (dut.accumulators[k*48+:48] !== accumulators[row*5+k]) $fatal(1,"INT48 row=%0d index=%0d",row,k);
        end
    endtask

    task automatic run_frame(input integer row, input integer gapped);
        integer sent, received, cycles;
        reg hold_last_once;
        begin
            sent=0; received=0; cycles=0; hold_last_once=0;
            while (received < 5) begin
                @(negedge clk);
                input_valid = sent < 152 && (!gapped || (cycles+row)%5 != 1);
                input_data = input_valid ? frames[row*152+sent] : 32'hdeadbeef;
                if (sent==82 && input_valid) input_data[31:16] = 16'hcafe; // wire padding
                output_ready = !gapped || ((cycles+row)%7>2 && (!output_last || hold_last_once));
                #1;
                if (sent < 152 && input_ready !== 1) $fatal(1,"input blocked inside frame");
                if (sent == 152 && input_ready !== 0) $fatal(1,"accepted next frame early");
                if (output_valid) begin
                    if (sent != 152) $fatal(1,"premature result");
                    if (output_data !== results[row*5+received] || output_last !== (received==4))
                        $fatal(1,"FP32 row=%0d lane=%0d got=%h expected=%h",row,received,output_data,results[row*5+received]);
                    if (output_ready) begin
                        if (received==0) check_intermediates(row);
                        received=received+1;
                        transfers=transfers+1;
                    end else begin
                        stalls=stalls+1;
                        if (output_last) begin hold_last_once=1; last_stalls=last_stalls+1; end
                    end
                end
                if (input_valid && input_ready) sent=sent+1;
                else if (sent<152) gaps=gaps+1;
                cycles=cycles+1;
                if (cycles>1000) $fatal(1,"frame timeout");
            end
            if (!gapped && row==0) first_latency=cycles;
            @(posedge clk); #1;
            if (input_ready !== 1 || output_valid !== 0) $fatal(1,"failed to retire frame");
        end
    endtask

    task automatic assert_reset;
        begin
            @(negedge clk); rst_n=0; input_valid=0; output_ready=0;
            #1;
            if (input_ready !== 1 || output_valid !== 0) $fatal(1,"reset did not cancel frame");
            repeat(3) @(posedge clk);
            @(negedge clk); rst_n=1;
            repeat(3) begin
                @(posedge clk); #1;
                if (output_valid !== 0 || input_ready !== 1) $fatal(1,"stale transaction after reset");
            end
        end
    endtask

    task automatic abort_frame(input integer point);
        integer i, length;
        begin
            length = point==0 ? 22 : point==1 ? 105 : 152;
            for (i=0;i<length;i=i+1) begin
                @(negedge clk); input_valid=1; input_data=frames[2*152+i]; output_ready=0;
                #1; if (!input_ready) $fatal(1,"abort setup input");
            end
            @(posedge clk); #1;
            input_valid=0;
            case (point)
                2: wait(dut.qact.state==dut.qact.WAIT_RECIP);
                3: wait(dut.qact.state==dut.qact.FACTORS && dut.qact.index==3);
                4: wait(dut.qact.state==dut.qact.PRIME);
                5: wait(dut.qact.state==dut.qact.SEND_Q && dut.qact.index==31);
                6: wait(dut.qact.state==dut.qact.SEND_OFFSETS);
                7: wait(dut.qact.state==dut.qact.SEND_SCALE);
                8: wait(dut.consumed_groups==19 && dut.state==dut.WAIT_MXU);
                9: wait(dut.state==dut.WAIT_EPILOGUE);
                10: begin wait(output_valid); repeat(4) @(posedge clk); end
            endcase
            assert_reset();
        end
    endtask

    integer row, mode, point;
    initial begin
        if (!$value$plusargs("folder=%s",folder)) $fatal(1,"fixture folder required");
        $readmemh({folder,"/frames.hex"},frames); $readmemh({folder,"/results.hex"},results);
        $readmemh({folder,"/codes.hex"},codes); $readmemh({folder,"/offsets.hex"},offsets);
        $readmemh({folder,"/scales.hex"},scales); $readmemh({folder,"/accumulators.hex"},accumulators);
        $readmemh({folder,"/drops.hex"},drops);
        assert_reset();
        for (mode=0;mode<2;mode=mode+1)
            for (row=0;row<24;row=row+1) run_frame(row,mode);
        if (transfers!=240 || stalls==0 || last_stalls<24 || gaps==0) $fatal(1,"missing handshake coverage");
        $display("PASS_BRAM_MXU frames=48 unique_rows=24 fp32=240 stalls=%0d final_stalls=%0d input_gaps=%0d first_frame_cycles=%0d",stalls,last_stalls,gaps,first_latency);
        for (point=0;point<11;point=point+1) begin
            abort_frame(point);
            run_frame((point+7)%24,1);
        end
        if (transfers!=295) $fatal(1,"recovery accounting");
        $display("PASS_BRAM_RESET aborts=11 recovered=11 fp32=55");
        $finish;
    end
    initial begin #1000000; $fatal(1,"global watchdog"); end
endmodule
