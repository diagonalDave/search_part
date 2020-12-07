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

## This is an example usage file for the proof of concept search_parts module.

import skidl
import search_part as sp


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

        self.sp = sp.SearchPart()

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
        ldo3v3 = self.sp.create_part(8, "lp2951", "soic-8", value="LP2951-3.3")
        c5v = self.sp.create_part(2, "C", "c_1206", ref="C5V",  value="10uF")
        c3v3 = c5v.copy()
        c3v3.ref = "C3V3"

        ldo3v3[1] += self.V33, c3v3[1], ldo3v3[2]
        ldo3v3[8] += self.V5, c5v[1]
        ldo3v3[4] += self.GND, c5v[2], c3v3[2], ldo3v3[3]
        ldo3v3[6] += ldo3v3[7]
        ldo3v3[6].drive = skidl.POWER
        ldo3v3[5] += NC

    @skidl.subcircuit
    def create_voltage_translator(self, high_signal, low_signal):

        nfet = self.sp.create_part(3, "2N7002", "sot-23", value="2N7002")
        r5v = self.sp.create_part(2, "R", "R_1206", ref="R5V", value="10k")
        r3v = self.sp.create_part(2, "R", "R_1206", ref="R3V", value="10k")

        nfet["S"] += low_signal, r3v[1]
        nfet["D"] += high_signal, r5v[1]
        nfet["G"] += self.V33
        self.V5 += r5v[2]
        self.V33 += r3v[2]

    def create_voltage_translators(self):
        """
        create_voltage_translators creates as many translators as needed for
        the bus size used to create the voltage_translator_board object.
        """
        for i in range(self.high_bus.width):
            self.create_voltage_translator(self.high_bus[i], self.low_bus[i])

    def create_connectors(self):
        """
        Connectors are needed for the 5V and GND in 2pin(solder connection), 
        6pin JST connector for the line from the encoder. 4pin encoder 
        connection and 3V3 and GND connection to PSOC 6 board.
        """

        power_conn = self.sp.create_part(2, "conn", "JST_XH", value="5V_IN")
        power3v3_conn = self.sp.create_part(
            2, "conn", "pinheader.*2.54.*vertical", value="3V3_PWR"
        )
        support_conn1 = self.sp.create_part(
            1, "conn", "pinHeader.*2.54.*vertical", value="SUPP_1"
        )
        support_conn2 = support_conn1.copy()
        support_conn2.value = "SUPP_2"

        # to parametise the buswidth could be used as for the pin_counts
        # in the enc headers.
        enc_in = self.sp.create_part(
            (self.high_bus.width + 2), "Conn", "JST_XH", value="ENC_IN_5V"
        )
        enc_out = self.sp.create_part(
            self.high_bus.width,
            "Conn",
            "^pinHeader_1.*2.54.*vertical$",
            value="ENC_OUT_3V3",
        )

        power_conn[1] += self.V5
        power_conn[2] += self.GND

        power3v3_conn[1] += self.V33
        power3v3_conn[2] += self.GND

        support_conn1[1] += self.GND

        support_conn2[1] += self.GND

        enc_in[1] += self.GND
        enc_in[2] += self.V5
        for i in range(self.high_bus.width):
            enc_in[i + 3] += self.high_bus[i]

        for i in range(self.low_bus.width):
            enc_out[i + 1] += self.low_bus[i]
        


if __name__ == "__main__":
    high_bus = skidl.Bus("high_in", 4)
    low_bus = skidl.Bus("low_out", 4)
    brd = voltage_translator_board(high_bus, low_bus)
    skidl.ERC()
    skidl.generate_netlist()
