export SITEDIR=docs

all: $(SITEDIR)/index.html $(SITEDIR)/arch.pdf

$(SITEDIR)/index.html: index.html
	mkdir -p $(SITEDIR)
	cp index.html $(SITEDIR)/

arch.tex: arch.hbd
	hbd2tex.py $? >$@

arch.pdf: arch.tex
	pdflatex $?

$(SITEDIR)/arch.pdf: arch.pdf
	cp $? $@

dist: all
	./publish.sh
