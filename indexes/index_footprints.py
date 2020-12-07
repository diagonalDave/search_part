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

from pyparsing import *

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(filename="footprint_index.log",  level=logging.DEBUG)


def create_footprint_index(footprint_file_dir):
    file_path = Path(footprint_file_dir)
    assert file_path.exists() and file_path.is_dir()
    mod_list = file_path.glob("**/*.kicad_mod")
    # print(list(mod_list))
    found_fp = {"name": [], "pad_count": [], "location": []}
    print(f"Starting indexing of directory:{file_path}")
    for k_mod_file in mod_list:
        print(k_mod_file)
        try:
            name, num_pads = _parse_kicad_mod(k_mod_file)
            found_fp["name"].append(name)
            found_fp["pad_count"].append(num_pads)
            found_fp["location"].append(Path(k_mod_file).parent.name)
           # found_fp["pad_size_info"].append(size_info)

        except ParseException:
            logging.error(f"Parse Error when parsing {k_mod_file}")
            
    fp_df = pd.DataFrame(found_fp)
    fp_df.to_csv("skidl_footprint_index.csv")

    print(f"Completed index, see footprint_index.log for any errors.")

def _parse_kicad_mod(file_path):
    ####footprint parser start
    # look for module name, tags and pad count.
    close_bracket = Literal(")").suppress()
    open_bracket = Literal("(").suppress()

    name = (
        Suppress("(")
        + CaselessKeyword("module").suppress()
        + (Optional('"') + Word(printables)("name")+  Optional('"'))
        
        + restOfLine.suppress()
    )
    pad = (
        Suppress("(")
        + CaselessKeyword("pad").suppress()
        + (Word(nums) | Word('""').suppress())
        + restOfLine.suppress()
    )

    pads = OneOrMore(pad)("pads")

    module = name + ZeroOrMore(SkipTo(pad).suppress() + pads + SkipTo(stringEnd).suppress())

    module_toks = module.parseFile(file_path)

    return module_toks.name, len(module_toks.pads)

if __name__ == "__main__":
    ### Change the path ("D:\APPS\KiCad\share\kicad\modules") to the path to the
    ### kicad modules on your system e.g.  "/usr/share/kicad/modules" or "C:\Program Files\KiCad\share\kicad\modules"
    ### indexing will take 5-10 minutes. Long enough for you to
    ### feel life is slipping away if you watch. 
    #create_footprint_index("/usr/share/kicad/modules")
    create_footprint_index("D:\APPS\KiCad\share\kicad\modules")
    
