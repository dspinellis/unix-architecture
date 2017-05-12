#!/usr/bin/env python
#
# Copyright 2017 Diomidis Spinellis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Convert a hirerchical box diagram into LaTeX
"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import re
import sys

RE_COLOR = re.compile(r'\[\s*color\s*=(\w+)\s*\]')
RE_HOR_BOX = re.compile(r'\s*hbox\s*\{')
RE_HOR_BOX_LABEL = re.compile(r'\s*hbox\s+([^{\s].*)')
RE_VER_BOX = re.compile(r'\s*vbox\s*\{')
RE_PLAIN_BOX = re.compile(r'\s*pbox\s*\{')
RE_BLOCK_END = re.compile(r'\s*\}')
RE_HOR_LABEL = re.compile(r'\s*hl\s+(.*)')
RE_VER_LABEL = re.compile(r'\s*vl\s+(.*)')

def cell_color(container, color):
    """Return the color of a cell given its container and the specified color"""
    if not color and container and container.color:
        return container.color
    else:
        return r'{\cellcolor{' + color + '}}' if color else ''

class NewLine(object):
    """An instruction to move elements to a next line"""

    def required_columns(self):
        """Number of additional columns (0 or 1) this element requires
        in the table"""
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return ''

    def to_string(self):
        return "\\\\\n"

class HorizontalLabel(object):
    """A label placed horizontally"""

    def __init__(self, container, label, color):
        self.label = label
        self.container = container
        self.color = cell_color(container, color)

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return ''

    def to_string(self):
	return (r'\multicolumn{' + str(self.container.ncol - 1) + '}{|c|}{' +
         self.color + self.label + "} \\\\\n")

class VerticalLabel(object):
    """A label placed vertically"""

    def __init__(self, container, label, color):
        self.label = label
        self.container = container
        self.ordinal = container.ncol
        self.color = cell_color(container, color)

    def required_columns(self):
        return 1

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return ''

    def to_string(self):
        r = ''
        if self.ordinal == 1:
            r += "\\hline% vl\n"

        is_last = self.ordinal == self.container.ncol - 1
        r += r'\multicolumn{1}{|c' + ('|' if is_last else '') + '}'
        r += r'{' + self.container.vertical_adjustbox()
        r += '{' + self.color + self.label + '}}'
        r += "\\\\\n" if is_last else "&\n"
        return r

class Box(object):
    """Contents of a box"""

    def __init__(self, container, color):
        self.contents = []
        self.ncol = 1
        self.container = container
        self.color = cell_color(container, color)

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return "\\\\\n"

    def to_string(self):
        r = (r'\begin{tabular}[t]{' + self.vertical_border() +
             ('l' * self.ncol) + self.vertical_border() + "}\n" +
             self.top_horizontal_border())
        for c in self.contents:
            r +=  c.to_string()
        if self.contents:
                r += self.contents[-1].end_line()
        r += self.bottom_horizontal_border() + r'\end{tabular}\hspace{1em}'
        return r

    def add_element(self, e):
        self.contents.append(e)
        self.ncol += e.required_columns()

    def vertical_border(self):
        return '|';

    def top_horizontal_border(self):
        return "\\hline% box border\n";

    def bottom_horizontal_border(self):
        return "\\hline\\noalign{\\vskip 2mm}% box border\n";


class HorizontalBox(Box):
    """Contents of a horizontal box"""
    def __init__(self, container, color):
        super(HorizontalBox, self).__init__(container, color)

    def vertical_adjustbox(self):
        if self.container:
            return self.container.vertical_adjustbox()
        else:
            return r'\adjustbox{angle=90,margin=0 0 0 0.5em}'

class PlainBox(HorizontalBox):
    """A horizontal box without a border"""
    def __init__(self, container, color):
        super(PlainBox, self).__init__(container, color)

    def vertical_border(self):
        return '';

    def top_horizontal_border(self):
        return '';

    def bottom_horizontal_border(self):
        return '';

class VerticalBox(Box):
    """Contents of a horizontal box rotated by 90 degrees"""
    def __init__(self, container, color):
        super(VerticalBox, self).__init__(container, color)

    def vertical_adjustbox(self):
        return r'\adjustbox{angle=-90,margin=0 0.5em 0 0}'

    def to_string(self):
        return ("\\rotatebox[origin=rt]{90}{\n" +
                super(VerticalBox, self).to_string() +
                "}\n")

def process_box(args, file_name, file_input, box):
    """Process a box's contents, adding them as elements to the returned box"""
    for line in file_input:
        if RE_BLOCK_END.match(line):
            return box
        else:
            e = process_line(args, file_name, file_input, line, box)
            if e:
                box.add_element(e)
    return box

def process_line(args, file_name, file_input, line, container):
    """Process a single element line return an element object, None if empty"""
    line = line.rstrip()
    if line and line[0] == '#':
        return None
    line = re.sub(r'#.*', '', line)

    if not line:
        return NewLine()

    matched = RE_COLOR.search(line)
    if matched:
        color = matched.group(1)
        line = RE_COLOR.sub('', line)
    else:
        color = ''

    if RE_HOR_BOX.match(line):
        return process_box(args, file_name, file_input,
                           HorizontalBox(container, color))

    if RE_VER_BOX.match(line):
        return process_box(args, file_name, file_input,
                           VerticalBox(container, color))

    if RE_PLAIN_BOX.match(line):
        return process_box(args, file_name, file_input,
                           PlainBox(container, color))

    matched = RE_HOR_LABEL.match(line)
    if matched:
        return HorizontalLabel(container, matched.group(1), color)

    # A box with a single horizontal label
    matched = RE_HOR_BOX_LABEL.match(line)
    if matched:
        box = HorizontalBox(container, color)
        box.add_element(HorizontalLabel(box, matched.group(1), color))
        return box

    matched = RE_VER_LABEL.match(line)
    if matched:
        return VerticalLabel(container, matched.group(1), color)

    sys.exit('Syntax error in line: ' + line)

def process_file(args, file_name, file_input):
    """File processing function"""

    box = process_box(args, file_name, file_input, PlainBox(None, None))
    print(box.to_string())

def prologue():
    """Begin a stand-alone LaTeX document"""
    print(r"""\documentclass{standalone}

\usepackage{adjustbox}
\usepackage{array}
\usepackage{graphicx}
\usepackage[table,svgnames]{xcolor}

\begin{document}
\textsf{""")

def epilogue():
    """Finish the standalone LaTeX document"""
    print("}\n\end{document}\n")

def main():
    """Program entry point"""
    parser = argparse.ArgumentParser(
        description='Generic Python program')
    parser.add_argument('-e', '--long-option',
                        help='Long option',
                        action='store_true')

    parser.add_argument('file',
                        help='File to process',
                        nargs='*', default='-',
                        type=str)
    args = parser.parse_args()
    if args.long_option:
        print("Long option set\n")
    prologue()
    for file_name in args.file:
        if file_name == '-':
            process_file(args, '<stdin>', sys.stdin)
        else:
            with open(file_name) as test_input:
                process_file(args, file_name, test_input)
    epilogue()

if __name__ == "__main__":
    main()
