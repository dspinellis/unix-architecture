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

RE_EMPTY = re.compile(r'\s*(#.*)?$')
RE_COLOR = re.compile(r'\[?\s*color\s*=(\w+)\s*[\],]')
# Left and right adornment
RE_ADORN_LR = re.compile(r'\[?\s*adornlr\s*=(\w+)\s*[\],]')
RE_HOR_BOX = re.compile(r'\s*hbox\s*\{')
RE_HOR_BOX_LABEL = re.compile(r'\s*hbox\s+([^{\s].*)')
RE_VER_BOX = re.compile(r'\s*vbox\s*\{')
RE_PLAIN_BOX = re.compile(r'\s*pbox\s*\{')
RE_BLOCK_END = re.compile(r'\s*\}')
RE_HOR_LABEL = re.compile(r'\s*hl\s+(.*)')
RE_VER_LABEL = re.compile(r'\s*vl\s+(.*)')
RE_HOR_SPACE = re.compile(r'\s*hspace\s+(.*)')

def cell_color(color):
    """Return the color of a cell given its container and the specified color"""
    return r'\cellcolor{' + color + '}' if color else ''

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

class Contained(object):
    """An graphical element (e.g. box, label) that can be contained
    within another"""
    def __init__(self, container):
        self.container = container

    def top_container(self):
        """Container at the top of the hierarchy"""
        if self.container:
            return self.container.top_container()
        else:
            return self

    def separate_boxes(self):
        """Return true if boxes are to be presented in stand-alone form"""
        return self.top_container().separate

class HorizontalLabel(Contained):
    """A label placed horizontally"""

    def __init__(self, container, label, color):
        self.label = label
        self.container = container
        self.color = color
        super(HorizontalLabel, self).__init__(container)

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return ''

    def to_string(self):
	return (r'\multicolumn{' + str(self.container.ncol - 1) + '}{|c|}{' +
         cell_color(self.color) + self.label + "} \\\\\n")

class HorizontalSpace(Contained):
    """Spacing placed horizontally"""

    def __init__(self, container, space):
        self.space = space
        self.container = container
        super(HorizontalSpace, self).__init__(container)

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return ''

    def to_string(self):
	return (r'\multicolumn{' + str(self.container.ncol - 1) +
         '}{c@{\\hspace{' + self.space + "}}}{} \\\\\n")

class VerticalLabel(Contained):
    """A label placed vertically"""

    def __init__(self, container, label, color):
        self.label = label
        self.container = container
        self.ordinal = container.ncol
        self.color = color
        super(VerticalLabel, self).__init__(container)

    def required_columns(self):
        return 1

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return ''

    def to_string(self):
        r = ''
        if self.ordinal == 1:
            if self.separate_boxes():
                r += (r'\hhline{' + self.container.compose_repeat(
                    '-', '||', '||', '||') + "}% vl\n")
            else:
                r += "\\hline% vl\n"

        is_last = self.ordinal == self.container.ncol - 1
        is_first = self.ordinal == 1
        r += r'\multicolumn{1}{'
        if self.separate_boxes():
            r += ('||' if is_first else '') + 'c||}'
        else:
            r += '|c' + ('|' if is_last else '') + '}'
        r += r'{' + self.container.vertical_adjustbox()
        r += '{' + cell_color(self.color) + self.label + '}}'
        r += "\\\\\n" if is_last else "&\n"
        return r

class Box(Contained):
    """Contents of a box"""

    def __init__(self, container, color, separate=False):
        self.contents = []
        self.ncol = 1
        self.container = container
        self.color = color
        self.separate = separate
        super(Box, self).__init__(container)

    def required_columns(self):
        return 0

    def end_line(self):
        """String to terminate a table line consisting of this element"""
        return "\\\\\n"

    def compose_repeat(self, element, separator, left, right):
        """Return l e s e s ... e r"""
        return (left + (element + separator) * (self.ncol - 2) +
                element + right)

    def to_string(self):
        if self.color:
            r = r'\colorbox{' + self.color + "}{%\n"
        else:
            r = '{'

        vb = self.vertical_border()
        if self.separate_boxes():
            spec = self.compose_repeat('l', '||', vb, vb)
        else:
            spec = self.compose_repeat('l', '', vb, vb)
        r += (r'\begin{tabular}[t]{' + spec + "}\n" +
             self.top_horizontal_border())
        for c in self.contents:
            r +=  c.to_string()
        if self.contents:
                r += self.contents[-1].end_line()
        r += self.bottom_horizontal_border() + r'\end{tabular}}\hspace{1em}'
        return r

    def add_element(self, e):
        self.contents.append(e)
        self.ncol += e.required_columns()

    def vertical_border(self):
        if self.separate_boxes() and self.ncol > 1:
            return '||';
        else:
            return '|';

    def top_horizontal_border(self):
        return "\\hline% top box border\n";

    def bottom_horizontal_border(self):
        if self.separate_boxes() and self.ncol > 1:
            r = (r'\hhline{' + self.compose_repeat(':=:', 'b', '|b', 'b|') +
                    "}% bottom box border\n")
        else:
            r = r'\hline'
        return r + "\\noalign{\\vskip 2mm}% bottom box border\n"


class HorizontalBox(Box):
    """Contents of a horizontal box"""
    def __init__(self, container, color, separate=False):
        super(HorizontalBox, self).__init__(container, color, separate)

    def vertical_adjustbox(self):
        if self.container:
            return self.container.vertical_adjustbox()
        else:
            return r'\adjustbox{angle=90,margin=0 0 0 0.5em}'

class PlainBox(HorizontalBox):
    """A horizontal box without a border"""
    def __init__(self, container, color, separate=False):
        super(PlainBox, self).__init__(container, color, separate)

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

def process_box(file_name, file_input, box):
    """Process a box's contents, adding them as elements to the returned box"""
    for line in file_input:
        if RE_BLOCK_END.match(line):
            return box
        else:
            e = process_line(file_name, file_input, line, box)
            if e:
                box.add_element(e)
    return box

def process_style(line, style_re):
    """Process the line for the specified style compiled regular expression,
    returning the line and style (if any) values"""
    matched = style_re.search(line)
    if matched:
        return (style_re.sub('', line), matched.group(1))
    else:
        return (line, '')

def process_line(file_name, file_input, line, container):
    """Process a single element line return an element object, None if empty"""
    line = line.rstrip()
    if line and RE_EMPTY.match(line):
        return None
    line = re.sub(r'#.*', '', line)

    if not line:
        return NewLine()

    (line, color) = process_style(line, RE_COLOR)
    (line, adorn_lr) = process_style(line, RE_ADORN_LR)

    if adorn_lr:
        adorn_left = '$\\' + adorn_lr + '$ '
        adorn_right = ' $\\' + adorn_lr + '$'
    else:
        adorn_left = adorn_right = ''

    if RE_HOR_BOX.match(line):
        return process_box(file_name, file_input,
                           HorizontalBox(container, color))

    if RE_VER_BOX.match(line):
        return process_box(file_name, file_input,
                           VerticalBox(container, color))

    if RE_PLAIN_BOX.match(line):
        return process_box(file_name, file_input,
                           PlainBox(container, color))

    matched = RE_HOR_LABEL.match(line)
    if matched:
        return HorizontalLabel(container, adorn_left + matched.group(1) +
                               adorn_right, color)

    matched = RE_HOR_SPACE.match(line)
    if matched:
        return HorizontalSpace(container, matched.group(1))

    # A box with a single horizontal label
    matched = RE_HOR_BOX_LABEL.match(line)
    if matched:
        box = HorizontalBox(container, color)
        box.add_element(HorizontalLabel(box, adorn_left + matched.group(1) +
                                        adorn_right, color))
        return box

    matched = RE_VER_LABEL.match(line)
    if matched:
        return VerticalLabel(container, matched.group(1), color)

    sys.exit('Syntax error in line: ' + line)

def process_file(args, file_name, file_input):
    """File processing function"""

    box = process_box(file_name, file_input,
                      PlainBox(None, None, args.separate_boxes))
    print(box.to_string())

def prologue(args):
    """Begin a stand-alone LaTeX document"""
    if args.prologue:
        with open(args.prologue, 'r') as fin:
            print(fin.read(), end='')
    else:
        print(r"""\documentclass{standalone}

\usepackage{adjustbox}
\usepackage{MnSymbol}
\usepackage{array}
\usepackage{graphicx}
\usepackage{hhline}
\usepackage[table,svgnames]{xcolor}
""")
    print(r"""
\begin{document}

\arrayrulewidth=1pt

\textsf{""")

def epilogue():
    """Finish the standalone LaTeX document"""
    print("}\n\end{document}\n")

def main():
    """Program entry point"""
    parser = argparse.ArgumentParser(
        description='Generic Python program')
    parser.add_argument('-s', '--separate-boxes',
                        help='Place vbox elements into separate boxes',
                        action='store_true')

    parser.add_argument('-p', '--prologue',
                        help='LaTeX prologue file', type=str)

    parser.add_argument('file',
                        help='File to process',
                        nargs='*', default='-',
                        type=str)
    args = parser.parse_args()
    prologue(args)
    for file_name in args.file:
        if file_name == '-':
            process_file(args, '<stdin>', sys.stdin)
        else:
            with open(file_name) as test_input:
                process_file(args, file_name, test_input)
    epilogue()

if __name__ == "__main__":
    main()
