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
Covnert a hirerchical box diagram into LaTeX
"""

from __future__ import absolute_import
from __future__ import print_function
import argparse
import re
import sys

RE_BOX = re.compile(r'\s*b\s*\{')
RE_BLOCK_END = re.compile(r'\s*\}')
RE_HOR_LABEL = re.compile(r'\s*hl\s+(.*)')
RE_VER_LABEL = re.compile(r'\s*vl\s+(.*)')


class NewLine:
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

class HorizontalLabel:
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
         self.label + "} \\\\\n")

class VerticalLabel:
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
        r += r'{\adjustbox{angle=90,margin=0 0 0 0.5em}{' + self.label + '}}'
        r += "\\\\\n" if is_last else "&\n"
        return r

class Box:
    """Contents of a box"""

    def __init__(self, container):
        self.contents = []
        self.ncol = 1
        self.draw_border = True if container else False
        self.container = container

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return "\\\\ \\\\\n"

    def to_string(self):
        if self.draw_border:
            hb = '|'
            vb = "\\hline% box border\n"
        else:
            hb = ''
            vb = ''
        r = r'\begin{tabular}{' + hb + ('l' * self.ncol) + hb + "}\n" + vb
        for c in self.contents:
            r +=  c.to_string()
        if self.contents:
            r += self.contents[-1].end_line()
        r += vb + "\\end{tabular}\n"
        return r

    def add_element(self, e):
        self.contents.append(e)
        self.ncol += e.required_columns()

def process_box(args, file_name, file_input, container):
    """Process a box's contents, adding them as elements to the returned box"""
    box = Box(container)
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

    if RE_BOX.match(line):
        return process_box(args, file_name, file_input, container)

    matched = RE_HOR_LABEL.match(line)
    if matched:
        return HorizontalLabel(container, matched.group(1))

    matched = RE_VER_LABEL.match(line)
    if matched:
        return VerticalLabel(container, matched.group(1))

    sys.exit('Syntax error in line: ' + line)

def process_file(args, file_name, file_input):
    """File processing function"""

    box = process_box(args, file_name, file_input, None)
    print(box.to_string())

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
    for file_name in args.file:
        if file_name == '-':
            process_file(args, '<stdin>', sys.stdin)
        else:
            with open(file_name) as test_input:
                process_file(args, file_name, test_input)

if __name__ == "__main__":
    main()
