export SITEDIR=docs

.SUFFIXES:.hbd .tex .pdf

%.tex: %.hbd
	./hbd2tex.py $? >$@

%.pdf: %.tex
	pdflatex $?

$(SITEDIR)/%.pdf: %.pdf
	cp $? $@

all: $(SITEDIR)/index.html $(SITEDIR)/arch.pdf $(SITEDIR)/arch-V1.pdf

$(SITEDIR)/index.html: index.html
	mkdir -p $(SITEDIR)
	cp index.html $(SITEDIR)/


dist: all
	./publish.sh
