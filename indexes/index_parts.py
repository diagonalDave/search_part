# MIT license
#
# Copyright (C) 2016 Xess Corporation (parser definition) and 2020 Dave Humphries (the rest)
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
import re

logging.basicConfig(filename="part_index.log", level=logging.DEBUG)


def _parse_kicad_lib(text):
    """
    Return a pyparsing object storing the contents of a KiCad symbol library.
    """

    # Basic parser elements.
    terminator_char = "|"
    terminator = Literal(terminator_char + "\n").suppress()
    fnum = Group(Word(nums) + Optional(Literal(".") + Optional(Word(nums))))
    string = Word(printables, excludeChars=terminator_char)
    qstring = dblQuotedString() ^ sglQuotedString()
    qstring.addParseAction(removeQuotes)
    anystring = qstring ^ string

    # ------------------ Schematic symbol parser.--------------------

    # Field section parser. (Fields are ignored.)
    field_start = CaselessLiteral("F") + Word(nums)("field_num")
    field = field_start + restOfLine
    fields = ZeroOrMore(field).suppress()  # Just ignore all fields.

    # Part aliases.
    aliases = ZeroOrMore(
        CaselessKeyword("ALIAS").suppress()
        + ZeroOrMore(Word(alphanums))("alias_p")
        + restOfLine.suppress()
    )

    # Footprint section. (Footprints are just skipped over and ignored.)
    foot_start = CaselessKeyword("$FPLIST") + terminator
    foot_end = CaselessKeyword("$ENDFPLIST") + terminator
    footprints = Optional(foot_start + SkipTo(foot_end) + foot_end).suppress()

    # Draw section parser.
    draw_start = (CaselessKeyword("DRAW") + restOfLine).suppress()
    draw_end = (CaselessKeyword("ENDDRAW") + terminator).suppress()
    draw_pin = Group(
        Word("Xx", exact=1).suppress()
        + anystring("name")
        + anystring("num")
        + (anystring * 3).suppress()
        + anystring("orientation")
        + (anystring * 2).suppress()
        + anystring("unit")
        + anystring.suppress()
        + anystring("type")
        + Optional(anystring)("style")
        + terminator
    )
    draw_other = (Word("AaCcPpSsTt", exact=1) + White() + restOfLine).suppress()
    draw_element = draw_pin ^ draw_other
    draw = Group(draw_start + ZeroOrMore(draw_element) + draw_end)("pins")

    # Complete schematic symbol definition parser.
    def_start = (
        CaselessKeyword("DEF").suppress()
        + anystring("name")
        + anystring("ref_id")
        + restOfLine.suppress()
    )
    def_end = (CaselessKeyword("ENDDEF") + terminator).suppress()
    defn = Group(def_start + (fields & aliases & footprints & draw) + def_end)

    # Parser for set of schematic symbol definitions.
    defs = ZeroOrMore(defn)

    # Parser for entire library.
    version = CaselessKeyword("version").suppress() + fnum
    start = (
        CaselessKeyword("EESchema-LIBRARY").suppress()
        + SkipTo(version)
        + version("version")
        + restOfLine.suppress()
    )
    end_of_file = Optional(White()) + stringEnd
    lib = start + defs("parts") + end_of_file

    # ---------------------- End of parser -------------------------

    # Remove all comments from the text to be parsed but leave the lines blank.
    # (Don't delete the lines or else it becomes hard to find the line in the file
    # that made the parser fail.)
    text = re.sub("(^|\n)#.*?(?=\n)", "\n", text)

    # Terminate all lines with the terminator string.
    # (This makes it easier to handle each line without accidentally getting
    # stuff from the next line.)
    text = re.sub("\n", " " + terminator_char + "\n", text)

    # Remove the terminator from all lines that just have the terminator character on them.
    # (Don't delete the lines or else it becomes hard to find the line in the file
    # that made the parser fail.)
    text = re.sub("\n *\\" + terminator_char + " *(?=\n)", "\n", text)

    # Return the parsed text.
    return lib.parseString(text)


def _create_index(parsed_lib, lib_file_name):
    """Creates a dataframe that will provide an index based on pin count"""

    p_dict = {"part_name": [], "pin_count": [], "location": [], "alias": []}

    for part in parsed_lib.parts:
        p_dict["part_name"].append(part.name)
        p_dict["pin_count"].append(len(part.pins))
        p_dict["location"].append(lib_file_name)
        p_dict["alias"].append(part.name)
        for p in part.alias_p:
            p_dict["part_name"].append(p)
            p_dict["pin_count"].append(len(part.pins))
            p_dict["location"].append(lib_file_name)
            p_dict["alias"].append(part.name)

    return p_dict


def create_part_index(part_file_dir):
    file_path = Path(part_file_dir)
    assert file_path.exists() and file_path.is_dir()
    lib_list = file_path.glob("*.lib")
    # print(list(mod_list))

    print(f"Starting indexing of directory:{file_path}")
    index_df = pd.DataFrame(
        {"part_name": [], "pin_count": [], "location": [], "alias": []}
    )
    for k_lib_file in lib_list:
        print(k_lib_file)
        with open(k_lib_file, "r", encoding="UTF-8") as lib:
            try:
                parsed_lib = _parse_kicad_lib(lib.read())
                parts = _create_index(parsed_lib, k_lib_file)
                k_lib_df = pd.DataFrame(parts)
                index_df = pd.concat([index_df, k_lib_df])
            except:
                logging.error(f"Parse Error when parsing {k_lib_file}")

    index_df.to_csv("skidl_part_index.csv")

    print(f"Completed index, see part_index.log for any errors.")


# main entrypoint.
if __name__ == "__main__":
    ### Change the path ("D:\APPS\KiCad\share\kicad\library") to the path to the
    ### kicad library on your system e.g. "/usr/share/kicad/library" or "C:\Program Files\KiCad\share\kicad\library"
    ### indexing will take 5-10 minutes. Long enough for you to
    ### feel life is slipping away if you watch.
#     create_part_index("/usr/share/kicad/library")
    create_part_index("D:\APPS\KiCad\share\kicad\library")
