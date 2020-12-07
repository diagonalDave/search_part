# MIT license
#
# Copyright (c) Dave Humphries 2020
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

## Additionally this software is ropey and only intended as proof of concept.

import skidl


class voltage_translator_board(object):
    """ This board translates a 5v signal bus to a 3v3 signal bus.
        It is intended to translate the %V signal from a HEDS58xx encoder 
        to a 3v3 signal bus suitable for a 3v3 signal.
        The board includes an LP2951 LDO to provide the low rail and power for the MCU.
    """

    def __init__(self, high_signal_bus, low_signal_bus):
        assert isinstance(high_signal_bus, skidl.Bus)
        assert isinstance(low_signal_bus, skidl.Bus)
        assert high_signal_bus.width == low_signal_bus.width

        super().__init__()

        self.high_bus = high_signal_bus
        self.low_bus = low_signal_bus

        self.V5 = skidl.Net("5V")
        self.V33 = skidl.Net("3V3")
        self.GND = skidl.Net("GND")

        self.V5.drive = skidl.POWER
        self.V33.driv = skidl.POWER
        self.GND.drive = skidl.POWER

        self.create_LP2951_3v3()

        for i in range(self.high_bus.width):
            self.create_voltage_translator(self.high_bus[i], self.low_bus[i])

        self.create_connectors()

    @skidl.subcircuit
    def create_LP2951_3v3(self):

        # Regulator_Linear.lib: LP2951-3.3_SOIC (Micropower Voltage Regulators with Shutdown, 100mA, Fixed Output 5.0V, LDO, SOIC-8)
        # LP2951-3.0_SOIC (LP2951-5.0_SOIC, LP2951-3.3_SOIC): Micropower Voltage Regulators with Shutdown, 100mA, Fixed Output 5.0V, LDO, SOIC-8
        # Pin None/1/OUT/POWER-OUT
        # Pin None/2/SENSE/PASSIVE
        # Pin None/3/SHUTDOWN/INPUT
        # Pin None/4/GND/POWER-IN
        # Pin None/5/~ERROR/OPEN-COLLECTOR
        # Pin None/6/VTAP/INPUT
        # Pin None/7/FEEDBACK/INPUT
        # Pin None/8/IN/POWER-IN

        ldo3v3 = skidl.Part(
            "Regulator_Linear",
            "LP2951-3.3_SOIC",
            footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        )

        cin = skidl.Part(
            "Device",
            "C",
            value="10uF",
            footprint="Capacitor_SMD:C_1206_3216Metric_Pad1.42x1.75mm_HandSolder",
        )
        cout = cin.copy()

        ldo3v3[1] += self.V33, cout[1], ldo3v3[2]
        ldo3v3[8] += self.V5, cin[1]
        ldo3v3[4] += self.GND, cout[2], cin[2], ldo3v3[3]
        ldo3v3[6] += ldo3v3[7]
        ldo3v3[6].drive = skidl.POWER
        ldo3v3[5] += NC

    @skidl.subcircuit
    def create_voltage_translator(self, high_signal, low_signal):
        #  Transistor_FET.lib: 2N7002 (1.4A Id, 60V Vds, N-Channel MOSFET, SOT-23)
        #  Pin None/1/G/INPUT
        # Pin None/2/S/PASSIVE
        # Pin None/3/D/PASSIVE

        nfet = skidl.Part(
            "Transistor_FET", "2N7002", footprint="Package_TO_SOT_SMD:SOT-23"
        )
        r5v = skidl.Part(
            "Device",
            "R",
            ref="R5V",
            value="10k",
            footprint="Resistor_SMD:R_1206_3216Metric",
        )
        r3v = skidl.Part(
            "Device",
            "R",
            ref="R3V",
            value="10k",
            footprint="Resistor_SMD:R_1206_3216Metric",
        )
        nfet["S"] += low_signal, r3v[1]
        nfet["D"] += high_signal, r5v[1]
        nfet["G"] += self.V33
        self.V5 += r5v[2]
        self.V33 += r3v[2]

    def create_voltage_translators(self):
        """
        create_voltage_translators creates as many translators as needed for
        the bus size used to create the smpib_board object.
        """
        for i in range(self.high_bus.width):
            self.create_voltage_translator(self.high_bus[i], self.low_bus[i])

    def create_connectors(self):
        """
        Connectors are needed for the 5V and GND in 2pin(solder connection), 
        6pin JST connector for the line from the encoder. 4pin encoder 
        connection and 3V3 and GND connection to PSOC 6 board.
        """
        power_conn = skidl.Part(
            lib="Connector.lib",
            name="Conn_01x02_Male",
            footprint="Connector_JST:JST_XH_B2B-XH-AM_1x02_P2.50mm_Vertical",
        )
        power_conn[1] += self.V5
        power_conn[2] += self.GND

        power3v3_conn = skidl.Part(
            lib="Connector.lib",
            name="Conn_01x02_Male",
            footprint="Connector_PinSocket_2.54mm:PinSocket_1x02_P2.54mm_Vertical",
        )
        power3v3_conn[1] += self.V33
        power3v3_conn[2] += self.GND

        # pins to support psoc poard and connect grounds.

        support_conn1 = skidl.Part(
            lib="Connector.lib",
            name="Conn_01x01_Male",
            footprint="Connector_PinSocket_2.54mm:PinSocket_1x01_P2.54mm_Vertical",
        )
        support_conn1[1] += self.GND

        support_conn2 = skidl.Part(
            lib="Connector.lib",
            name="Conn_01x01_Male",
            footprint="Connector_PinSocket_2.54mm:PinSocket_1x01_P2.54mm_Vertical",
        )
        support_conn2[1] += self.GND

        enc_in = skidl.Part(
            lib="Connector.lib",
            name="Conn_01x06_Male",
            footprint="Connector_JST:JST_XH_B6B-XH-AM_1x06_P2.50mm_Vertical",
        )
        enc_in[1] += self.GND
        enc_in[2] += self.V5
        enc_in[3] += self.high_bus[0]
        enc_in[4] += self.high_bus[1]
        enc_in[5] += self.high_bus[2]
        enc_in[6] += self.high_bus[3]

        enc_out = skidl.Part(
            lib="Connector.lib",
            name="Conn_01x04_Male",
            footprint="Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
        )
        enc_out[1] += self.low_bus[0]
        enc_out[2] += self.low_bus[1]
        enc_out[3] += self.low_bus[2]
        enc_out[4] += self.low_bus[3]


if __name__ == "__main__":
    high_bus = skidl.Bus("high_in", 4)
    low_bus = skidl.Bus("low_out", 4)
    brd = voltage_translator_board(high_bus, low_bus)
    skidl.ERC()
    skidl.generate_netlist()
