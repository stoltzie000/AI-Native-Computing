# Digilent Arty A7-100 rev D/E (xc7a100tcsg324-1), onboard 100 MHz oscillator.
# Only the button and LEDs leave the FPGA. All payload buses share clk.
set_property -dict {PACKAGE_PIN E3 IOSTANDARD LVCMOS33} [get_ports clk]
set_property -dict {PACKAGE_PIN D9 IOSTANDARD LVCMOS33} [get_ports reset_button]
set_property -dict {PACKAGE_PIN H5 IOSTANDARD LVCMOS33} [get_ports passed]
set_property -dict {PACKAGE_PIN J5 IOSTANDARD LVCMOS33} [get_ports failed]
create_clock -period 10.000 [get_ports clk]
