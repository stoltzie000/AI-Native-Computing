# Invoke in batch with -tclargs <ROM directory> ?full|bringup?.
if {$argc < 1 || $argc > 2} { error "expected the generated ROM directory and optional profile" }
set profile [expr {$argc == 2 ? [lindex $argv 1] : "full"}]
if {$profile ni {full bringup}} { error "expected full or bringup" }
set fpga [file dirname [file normalize [info script]]]
set repo [file normalize [file join $fpga .. .. ..]]
cd [file normalize [lindex $argv 0]]
foreach file {frames.hex results.hex} {
    if {![file exists $file]} { error "missing $file" }
}
set part xc7a100tcsg324-1
set_part $part
set sources [open [file join $fpga pipeline.f]]
foreach source [split [string trim [read $sources]] "\n"] {
    read_verilog [file join $repo $source]
}
close $sources
read_verilog [file join $fpga arty_bram_selftest.v]
set top arty_bram_selftest
if {$profile eq "bringup"} {
    set top arty_bram_bringup
    read_verilog [file join $fpga arty_bram_bringup.v]
}
read_xdc [file join $fpga arty_a7_100t.xdc]
synth_design -top $top -part $part
# These board pins have no synchronous external data consumer or producer.
# All register-to-register data paths, including reset release, remain timed.
set_false_path -from [get_ports reset_button]
set_false_path -to [get_ports {passed failed}]
opt_design
place_design
phys_opt_design
route_design
report_route_status -file vivado-route.rpt
report_utilization -file vivado-utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file vivado-timing.rpt
report_drc -file vivado-drc.rpt
write_checkpoint -force vivado-routed.dcp
if {![report_route_status -boolean_check ROUTED_FULLY] || [report_route_status -boolean_check ERRORS_IN_ROUTES]} {
    error "incomplete or erroneous routing"
}
set primary [get_clocks -of_objects [get_ports clk]]
if {[llength $primary] != 1 || abs([get_property PERIOD $primary]-10.0)>0.001} {
    error "expected a 10 ns oscillator"
}
if {$profile eq "bringup"} {
    set generated [get_clocks -of_objects [get_pins -hierarchical -filter {REF_PIN_NAME == CLKOUT0}]]
    if {[llength $generated] != 1 || abs([get_property PERIOD $generated]-160.0)>0.001} {
        error "expected a PLL-generated 160 ns datapath clock"
    }
}
foreach delay {max min} {
    set paths [get_timing_paths -delay_type $delay -max_paths 1]
    if {[llength $paths] != 1 || [get_property SLACK $paths] < 0} { error "missing or negative $delay slack" }
}
puts "Routed setup and hold checks passed. Review DRC and unconstrained-path reports."
