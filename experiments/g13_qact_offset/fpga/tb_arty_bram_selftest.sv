`timescale 1ns/1ps
module tb_arty_bram_selftest;
    reg clk=0, reset_button=0;
    wire passed, failed;
    reg corrupt;
    always #5 clk=!clk;
    arty_bram_selftest dut(.*);
    initial begin
        #1; reset_button=1; corrupt=$test$plusargs("corrupt");
        if (corrupt) dut.expected[37] = dut.expected[37] ^ 32'h1;
        repeat(3) @(negedge clk);
        reset_button=0;
        wait(passed || failed);
        repeat(5) @(negedge clk);
        if (failed !== corrupt || passed !== !corrupt) $fatal(1,"wrong status LEDs");
        if (corrupt && dut.received !== 37) $fatal(1,"wrong fault location");
        $display("PASS_ARTY_SELFTEST_SIM corrupt=%0d pass_led=%0d fail_led=%0d",corrupt,passed,failed);
        $finish;
    end
    initial begin #1000000; $fatal(1,"board watchdog"); end
endmodule
