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

* horizontal, and vertical framed boxes (hbox, vbox)
* plain (unframed) composite boxes (pbox)
* horizontal and vertical labels (hl, vl)

Boxes are put side by side; a blank line continues the layout on the next line.

The Python script generates a stand-alone LaTeX document, ehich can then be converted to PDF.
This idea has been taken on by the [boxes](https://github.com/panos1962/boxes)
project to generate HTML output.
