`timescale 1ns/1ps
// Separate bring-up configuration. The 100 MHz oscillator drives a real
// PLL at 800 MHz VCO; CLKOUT0 /128 supplies 6.25 MHz to the complete self-test.
module arty_bram_bringup(input wire clk, reset_button, output wire passed, failed);
    wire feedback_raw, feedback, core_raw, core_clk, locked;
    PLLE2_BASE #(
        .CLKIN1_PERIOD(10.0), .DIVCLK_DIVIDE(1), .CLKFBOUT_MULT(8), .CLKOUT0_DIVIDE(128)
    ) pll(
        .CLKIN1(clk), .CLKFBIN(feedback), .CLKFBOUT(feedback_raw), .CLKOUT0(core_raw),
        .LOCKED(locked), .PWRDWN(1'b0), .RST(reset_button)
    );
    BUFG feedback_buffer(.I(feedback_raw), .O(feedback));
    BUFG core_buffer(.I(core_raw), .O(core_clk));
    arty_bram_selftest selftest(
        .clk(core_clk), .reset_button(reset_button || !locked), .passed(passed), .failed(failed)
    );
endmodule
