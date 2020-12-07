
# Table of Contents

1.  [Search Part](#org4978424)
    1.  [Info](#org4088e50)
    2.  [Installation](#orga82bd6c)
        1.  [Download and setup](#org8908fad)
        2.  [Create the indexes](#orgc109002)
    3.  [Basic Usage](#orge187f09)
    4.  [Search part tools](#orgdddc04e)
    5.  [Examples](#orgfeb9bd0)
        1.  [Refine your regex](#org2f95ea5)



<a id="org4978424"></a>

# Search Part

Search part is a proof of concept (POC) part creator for SKIDL. 

Currently the code is good enough for my purposes "Works on my
machine "(TM). But may also be useful for others wishing to use SKIDL more easily.

The main purpose of this POC is to see if it is worthwhile to work it into
SKIDL, provide tests, back port to Python 2 (man get with the times
f-strings are worth it alone) and all the other stuff to make it robust and
reliable on all platforms.

It currently has only been tested on Python 3.8 and pandas 1.15 Windows10
and Python 3.6 and pandas 1.15 on Suse Leap 15.2. Hopefully it will work on
Macs too.


<a id="org4088e50"></a>

## Info

Creating a part with search part avoids having to know the storage
structure of KiCad parts and footprints.
It is intended to be simple to use:
```
import search_ part as sp
pc = sp.SearchPart()
ldo = pc.create_part(8, "LP2951.*soic", "SOIC") #returns a skidl.Part()
```
To get this simplicity the first part or footprint on the list is
returned, this may not be the part you want or it may blow-up
because no parts were found. This is when you turn to the [1.4](#orgdddc04e)
section below.

The function create\_part is a skidl.Part() wrapper that takes parameters that most designers know:

1.  **pin\_count**
2.  **part\_name**&#x2013;this can be a partial name and is in fact a regex so
    regex symbols can be used. Search\_part provides some tools that
    can help narrow your part search to the correct one. 
    See [Search part tools](#orgdddc04e) section below.
3.  **footprint\_name**, this can be a partial name and is also a 
    regex. See [Search part tools](#orgdddc04e).
4.  **pad\_count**, this by default is set to the pin\_count but sometimes
    these are different.
5.  **\*\*kwargs**, add any key word args you want to pass through to skidl.Part()


<a id="orga82bd6c"></a>

## Installation

The installation of search\_part has two parts:

1.  Download and get it setup.
2.  Create the indexes.


<a id="org8908fad"></a>

### Download and setup

1.  Download or clone the repository onto your system.
2.  pip install pandas 1.15 to the python environment you intend using.
3.  Make sure skidl is installed ;)
4.  Navigate to the search\_part directory. You shoud see:
    -   search\_parts.py
    -   a couple of example files: voltage\_translator\_board\_sp.py and a comparable
        voltage\_translator\_board.py skidl only file.
    -   indexes directory that has two .py files.
    -   pcb\_files directory with some pcb files that use the generated .net files.


<a id="orgc109002"></a>

### Create the indexes

There are a lot of ways this could be done but using a stone axe
is at least simple if not gratifying.

1.  Navigate to the indexes directory. There are two .py files, if
    the names are confusing stop now this isn't going to work.
2.  Open index\_footprints.py in an editor then head to the bottom
    of the file.
3.  Replace the file path with the one to your kicad **modules**
    directory, some hints are given for common directories in the
    comment.
4.  Save the file open a cmd prompt/terminal then create an index
    with:
    ```
    python index\_footprints.py
    ```
This will take 5-10 minutes to run and generate a
skidl\_footprint\_index.csv file.

1.  Repeat steps 2-4 with the index\_parts.py file and your kicad
    **library** directory.

Once this has run for its 5-10 mins it will generate a
skidl\_parts\_index.csv file.

1.  Check the logs to see how it went. Typically all footprint
    files index correctly and there are four part files that wind up in the
    logs. I will look at these when I have a chance.If you need to
    use parts from these files you will have to use skidl.Part() to
    get them on the board.

Test the indexes have been created correctly:

1.  Navigate to the search\_part directory.
2.  Open a python3 terminal then enter:
    ```
    dave@suse-lappy:~/git/python/skidl/search_part> python3 search_part.py
    Create some parts as a test.
    Generate a net list. Check the parts in kicad by importing the search_part.net file.
    
    No errors or warnings found during netlist generation.
    
    Query for all footprints with 5 pads in a dip package.
    Unnamed: 0                                 name  pad_count            location
    8367        8367                     DIP-5-6_W10.16mm          5  Package_DIP.pretty
    8368        8368            DIP-5-6_W10.16mm_LongPads          5  Package_DIP.pretty
    8369        8369                      DIP-5-6_W7.62mm          5  Package_DIP.pretty
    8370        8370             DIP-5-6_W7.62mm_LongPads          5  Package_DIP.pretty
    8371        8371  DIP-5-6_W7.62mm_SMDSocket_SmallPads          5  Package_DIP.pretty
    8372        8372               DIP-5-6_W7.62mm_Socket          5  Package_DIP.pretty
    8373        8373      DIP-5-6_W7.62mm_Socket_LongPads          5  Package_DIP.pretty
    8374        8374   DIP-5-6_W8.89mm_SMDSocket_LongPads          5  Package_DIP.pretty
    >>>
    ```
If you see the above then you are ready to go. 
If not:

1.  Check the index logs and the index.csv files (they should both be around 1MB in size).


<a id="orge187f09"></a>

## Basic Usage

1.  Create a python file in the search\_part directory.
2.  Import skidl and search\_part then start building your skidl
    circuit. 
    ```
    import skidl
    import search_part as sp
    part_creator = sp.SearchPart()
    r5v = part_creator.create_part(2, "R", "R_1206", ref="R5V", value="10k")
    &#x2026;
    use the part
    &#x2026;
    r5v[1] += V5
    r5v[2] += input_net
    ```

The voltage\_translator\_sp.py file provides example usage.


<a id="orgdddc04e"></a>

## Search part tools

Two further functions are provided with search\_part that allow you
to interogate the indexes: query\_part\_return\_all(pin\_count,
part\_name) and query\_footprint\_return\_all(pad\_count,
footprint\_name)

Search\_part uses case insensitive regexes to filter the dataset it then
uses the first record to create the part. This is simple but can cause an
exception if nothing is returned or you get the wrong part or footprint
sent to the board file.  The process to refine a regex described below
takes about 30 seconds at the interpreter. The regexes are simple and only
use a few operators to reduce the filtered dataset to what you want.

1.  Open a python interpreter in the search\_part directory.
```
>>> import search_part as sp
>>> pp = sp.SearchPart()
>>> pp.query_part_return_all(4, "conn")
   Unnamed: 0                     part_name  &#x2026;                                           location                         alias
   2459          11                    CONN_01X04  &#x2026;         D:\APPS\KiCad\share\kicad\library\conn.lib                    CONN_01X04
   2497          49                    CONN_02X02  &#x2026;         D:\APPS\KiCad\share\kicad\library\conn.lib
   ...
   3463           2           Conn_01x03_Shielded  &#x2026;  D:\APPS\KiCad\share\kicad\library\Connector_Ge&#x2026;           Conn_01x03_Shielded

[13 rows x 5 columns]
>>> pp.query_footprint_return_all(4, "pinHeader.*vertical")
   Unnamed: 0                                           name  pad_count                           location
   918          918             FanPinHeader_1x04_P2.54mm_Vertical          4                   Connector.pretty
   ...
   4946        4946                PinHeader_2x02_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
   4947        4947            PinHeader_2x02_P2.54mm_Vertical_SMD          4  Connector_PinHeader_2.54mm.pretty
   >>>
```
From these results you can see that refining the footprint name
will be needed to get the right spacing and orientation, see
[1.5.1](#org2f95ea5) for an example of refining the footprint name.


<a id="orgfeb9bd0"></a>

## Examples

Some example files have been provided in the search\_part directory
to illustrate skidl and search\_part usage. There is nothing high
falutin' about the examples and I expect it will change as I become
more familiar with skidl for pcbs. 
voltage\_translator\_board\_sp.py is the search\_part/skidl version
voltage\_translator\_board.py is the skidl only version this board was
layed out and sent for fabrication.


<a id="org2f95ea5"></a>

### Refine your regex

To be blunt regexes can be painful, hopefully this section will
allow you to easily get the part or footprint to the top of the
filtered list.
Let's start with a standard 4 pin header used on just about any
prototyping board. 

1.  Try something simple:
```
>>> pp.query_footprint_return_all(4, "pinHeader")
```
Returns a shipload of results starting with 'FanPinHeader' &#x2026;

There are two possibilities here:

-   search the list manually, find your part and  copy and paste the full text into

create\_part. You are now done. Or;

-   refine the regex.

The following describes how to refine the regex.

Looking at these results you realise that specifying the pin
spacing is important, they make more than one kind!

 Try again
```
>>> pp.query_footprint_return_all(4, "pinHeader.*2.54")
```
Adding a '\.*' means anything can be between 'pinHeader' and '2.54'
This reduces the list to:
```
>>> pp.query_footprint_return_all(4, "pinHeader.*2.54")
  Unnamed: 0                                           name  pad_count                           location
  918          918             FanPinHeader_1x04_P2.54mm_Vertical          4                   Connector.pretty
  4794        4794              PinHeader_1x04_P2.54mm_Horizontal          4  Connector_PinHeader_2.54mm.pretty
  4795        4795                PinHeader_1x04_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
  ...
  4946        4946                PinHeader_2x02_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
  4947        4947            PinHeader_2x02_P2.54mm_Vertical_SMD          4  Connector_PinHeader_2.54mm.pretty
  >>>
```
Looking through the list again you realise orientation needs
to be specified.

Try again
```   
    >>> pp.query_footprint_return_all(4, "pinHeader.*2.54.*vertical")
     Unnamed: 0                                           name  pad_count                           location
     
     918          918             FanPinHeader_1x04_P2.54mm_Vertical          4                   Connector.pretty
     4795        4795                PinHeader_1x04_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
     4796        4796   PinHeader_1x04_P2.54mm_Vertical_SMD_Pin1Left          4  Connector_PinHeader_2.54mm.pretty
     4797        4797  PinHeader_1x04_P2.54mm_Vertical_SMD_Pin1Right          4  Connector_PinHeader_2.54mm.pretty
     4946        4946                PinHeader_2x02_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
     4947        4947            PinHeader_2x02_P2.54mm_Vertical_SMD          4  Connector_PinHeader_2.54mm.pretty
     >>>
```
OK getting closer I don't want no smd pin header. A bit of
contemplation give you the realisation that the bits you want end
with 'Vertical'.

Try again
```    
    >>> pp.query_footprint_return_all(4, "pinHeader.*2.54.*vertical$")
    Unnamed: 0                                name  pad_count                           location

    918          918  FanPinHeader_1x04_P2.54mm_Vertical          4                   Connector.pretty
    4795        4795     PinHeader_1x04_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
    4946        4946     PinHeader_2x02_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
    >>>
```
The $ sign at the end means that 'vertical' has to be at the end
of the line.

Now ffs what is with the 'FanPinHeader'? It has resolutely stayed
at the top of the list. Its got to go.
```
  >>> pp.query_footprint_return_all(4, "^pinHeader.*2.54.*vertical$")
  Unnamed: 0                             name  pad_count                           location
  4795        4795  PinHeader_1x04_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
  4946        4946  PinHeader_2x02_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
  >>>
```
The '^' sign at the beginning means 'pinHeader' is the first thing
on the line.
You could leave it here and search\_part will use the first
footprint, but for completeness we will get rid of the remaining
option by adding "\_1" to 'pinHeader'
```
>>> pp.query_footprint_return_all(4, "^pinHeader_1.*2.54.*vertical$")
Unnamed: 0                             name  pad_count                           location
4795        4795  PinHeader_1x04_P2.54mm_Vertical          4  Connector_PinHeader_2.54mm.pretty
>>>
```
While it takes a chunk of time to read and write this process it happens quickly
with the interpreter so the above could occur in less than 30 seconds with a
little experience.

Once you have the correct regex copy and paste into your
create\_part field to get it every time.

