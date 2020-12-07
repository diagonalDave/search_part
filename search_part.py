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
import re
import skidl


class SearchPart(object):
    def __init__(self):
        #  self.load_indexes()
        self.part_df = pd.DataFrame()
        self.fp_df = pd.DataFrame()
        self._load_indexes()

    def _load_indexes(self, index_dir=None):
        if index_dir is None:
            index_path = Path.cwd() / "indexes"
        else:
            index_path = Path(index_dir)

        if index_path.exists():
            if index_path.is_dir():
                index_path_list = list(
                    index_path.glob("skidl_footprint_index.csv")
                )
                if len(index_path_list) > 0 and index_path_list[0].is_file():
                    fp_index_path = index_path_list[0]
                else:
                    # abandon all hope.
                    raise Exception(
                        f"Footprint index file cannot be found at:{fp_index_path}"
                    )

                index_path_list = list(index_path.glob("skidl_part_index.csv"))
                if len(index_path_list) > 0 and index_path_list[0].is_file():
                    part_index_path = index_path_list[0]
                else:
                    # abandon all hope.
                    raise Exception(
                        f"Part index file cannot be found at:{part_index_path}"
                    )

            else:
                # the path is bad
                raise Exception(
                    f"Path to index directory is a file:{index_path}"
                )
        else:
            # path doesn't exist
            raise Exception(
                f"Index directory cannot be found at:{index_path}"
            )

        self.part_df = pd.read_csv(part_index_path)
        self.fp_df = pd.read_csv(fp_index_path)

    def query_part(self, pin_count, name):
        """Returns a list of index records based on the input pin_count
        and filtered by name"""
        assert isinstance(pin_count, int)
        assert isinstance(name, str)
        filter_df = self.part_df[self.part_df.pin_count == pin_count]
        filter_df = filter_df[filter_df.part_name.str.contains(name.upper(), case=False, regex=True)]
        lib = filter_df.location.values[0]
        p_name = filter_df.part_name.values[0]

        return lib[:-4], p_name

    def query_part_return_all(self, pin_count, name):
        assert pin_count is not None
        assert isinstance(pin_count, int) and pin_count > -1
        assert name is not None
        assert isinstance(name, str) and name != ""

        filter_df = self.part_df[self.part_df.pin_count == pin_count]
        return filter_df[filter_df.part_name.str.contains(name.upper(), case=False, regex=True)]

    def query_footprint(self, pad_count, name):
        """Returns a list of index records based on the pad count
        and filtered by the name."""
        k_mod = "Not implemented"
        fp_name = "Not implemented"
        assert isinstance(pad_count, int)
        assert isinstance(name, str)
        filter_df = self.fp_df[self.fp_df.pad_count == pad_count]
        filter_df = filter_df[filter_df.name.str.contains(name.upper(), case=False, regex=True)]
        # take the first one
        k_mod = filter_df.location.values[0]
        fp_name = filter_df.name.values[0]

        return k_mod, fp_name


    def query_footprint_return_all(self, pad_count, name, by_pad_count=True):
        """Returns a data frame that has been filtered by pin_count and name.
        by_pad_count= True filters by pad_count first then by name.
        by_pad_count=False filters by name first then pad_count.
        """
        assert by_pad_count is not None
        assert pad_count is not None and pad_count > -1
        assert name is not None and name != ""

        if by_pad_count:
            filter_df = self.fp_df[self.fp_df.pad_count == pad_count]
            return filter_df[filter_df.name.str.contains(name.upper(), case=False, regex=True)]
        else:
            filter_df = self.fp_df[self.fp_df.name.str.contains(name.upper(), case=False, regex=True)]
            return filter_df[filter_df.pad_count == pad_count]

    def create_part(self, pin_count, name, fp_name, pad_count=None, **kwargs):
        if pad_count is None:
            pad_count = pin_count

        lib, name = self.query_part(pin_count, name)
        fp_mod, fp_name = self.query_footprint(pad_count, fp_name)
        p_art = skidl.Part(
            lib, name, footprint=f"{fp_mod[:-7]}:{fp_name}", **kwargs
        )

        return p_art

    def __str__(self):
        out_str = self.part_df.to_string(max_rows=10)

        return out_str


if __name__ == "__main__":
    sp = SearchPart()
    print("Create some parts as a test.")
    par_t = sp.create_part(5, "74cbt", "sot")
    part2 = sp.create_part(8, "LP2951", "soic-8", value="LP2951-3.3")
    cin = sp.create_part(2, "C", "C_1206", ref="C", value="10uF")
    nfet = sp.create_part(3, "2N7002", "sot-23", value="2N7002")
    r5v = sp.create_part(2, "R", "R_1206", ref="R5V", value="10k")
    print("Generate a net list. Check the parts in kicad by importing the search_part.net file.")
    skidl.generate_netlist()
    pp = SearchPart()
    print("Query for all footprints with 5 pads in a dip package.")
    print(pp.query_footprint_return_all(5, "dip"))
    
