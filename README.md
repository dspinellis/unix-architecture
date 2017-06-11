# Unix Architecture Diagrams
This repository maintains the source code files for creating diagrams of the
[Unix architecture evolution](https://dspinellis.github.io/unix-architecture/index.html).
The diagrams are roughly based on data obtained from the
[evolution of Unix facilities](https://dspinellis.github.io/unix-history-man/index.html)
across the major Unix releases tracked by the
[Unix history repository](https://github.com/dspinellis/unix-history-repo).


## Diagram description language
I designed and implemented a small domain-specific language for
representing hierarchically nested block diagrams.
The language allows you to define:

* horizontal, and vertical framed boxes (_hbox_, _vbox_)
* plain (unframed) composite boxes (_pbox_)
* horizontal and vertical labels (_hl_, _vl_)

Boxes are put side by side; a blank line continues the layout on the next line.

Horizontal labels can be preceded by a
`color=`_colorname_ or `adornlr=`_symbol_ within square brackets.
The _colorname_ argument to color is a LaTeX color name,
which specifies the name of the corresponding box.
The _symbol_ is a LaTeX math symbol name, which is used to adorn the
corresponding label on its left and right-hand sides.

Passing the `-s` or `--separage-boxes` command-line argument to the script
will generate a less compact but more semantically consistent diagram,
where each element is within its own box.

The Python script generates a stand-alone LaTeX document, which can then be converted to PDF.
This idea has been taken on by the [boxes](https://github.com/panos1962/boxes)
project to generate HTML output.
