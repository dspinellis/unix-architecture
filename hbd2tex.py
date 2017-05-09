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

RE_HOR_BOX = re.compile(r'\s*hbox\s*\{')
RE_HOR_BOX_LABEL = re.compile(r'\s*hbox\s+([^{\s].*)')
RE_VER_BOX = re.compile(r'\s*vbox\s*\{')
RE_PLAIN_BOX = re.compile(r'\s*pbox\s*\{')
RE_BLOCK_END = re.compile(r'\s*\}')
RE_HOR_LABEL = re.compile(r'\s*hl\s+(.*)')
RE_VER_LABEL = re.compile(r'\s*vl\s+(.*)')


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

    def __init__(self, container, label):
        self.label = label
        self.container = container

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return ''

    def to_string(self):
	return (r'\multicolumn{' + str(self.container.ncol - 1) + '}{|c|}{' +
        #r'\adjustbox{angle=180,margin=0 0 0 0.5em}{' + self.label + "}} \\\\\n")
         self.label + "} \\\\\n")

class VerticalLabel(object):
    """A label placed vertically"""

    def __init__(self, container, label):
        self.label = label
        self.container = container
        self.ordinal = container.ncol

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
        r += r'{\adjustbox{angle=' + self.container.vertical_angle()
        r += ',margin=0 0 0 0.5em}{' + self.label + '}}'
        r += "\\\\\n" if is_last else "&\n"
        return r

class Box(object):
    """Contents of a box"""

    def __init__(self, container):
        self.contents = []
        self.ncol = 1
        self.container = container

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return "\\\\ \\\\\n"

    def to_string(self):
        r = (r'\begin{tabular}[t]{' + self.horizontal_border() +
             ('l' * self.ncol) + self.horizontal_border() + "}\n" +
             self.vertical_border())
        for c in self.contents:
            r +=  c.to_string()
        if self.contents:
            r += self.contents[-1].end_line()
        r += self.vertical_border() + "\\end{tabular} "
        return r

    def add_element(self, e):
        self.contents.append(e)
        self.ncol += e.required_columns()

    def horizontal_border(self):
        return '|';

    def vertical_border(self):
        return "\\hline% box border\n";


class HorizontalBox(Box):
    """Contents of a horizontal box"""
    def __init__(self, container):
        super(HorizontalBox, self).__init__(container)

    def vertical_angle(self):
        return '90'

class PlainBox(HorizontalBox):
    """A horizontal box without a border"""
    def __init__(self, container):
        super(PlainBox, self).__init__(container)

    def horizontal_border(self):
        return '';

    def vertical_border(self):
        return '';

class VerticalBox(Box):
    """Contents of a horizontal box rotated by 90 degrees"""
    def __init__(self, container):
        super(VerticalBox, self).__init__(container)

    def vertical_angle(self):
        return '-90'

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

    if RE_HOR_BOX.match(line):
        return process_box(args, file_name, file_input,
                           HorizontalBox(container))

    if RE_VER_BOX.match(line):
        return process_box(args, file_name, file_input,
                           VerticalBox(container))

    if RE_PLAIN_BOX.match(line):
        return process_box(args, file_name, file_input,
                           PlainBox(container))

    matched = RE_HOR_LABEL.match(line)
    if matched:
        return HorizontalLabel(container, matched.group(1))

    # A box with a single horizontal label
    matched = RE_HOR_BOX_LABEL.match(line)
    if matched:
        box = HorizontalBox(container)
        box.add_element(HorizontalLabel(box, matched.group(1)))
        return box

    matched = RE_VER_LABEL.match(line)
    if matched:
        return VerticalLabel(container, matched.group(1))

    sys.exit('Syntax error in line: ' + line)

def process_file(args, file_name, file_input):
    """File processing function"""

    box = process_box(args, file_name, file_input, PlainBox(None))
    print(box.to_string())

def prologue():
    """Begin a stand-alone LaTeX document"""
    print(r"""\documentclass{standalone}

\usepackage{adjustbox}
\usepackage{array}
\usepackage{graphicx}

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
