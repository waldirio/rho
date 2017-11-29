# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = python -msphinx
SPHINXPROJ    = rho
SOURCEDIR     = source
BUILDDIR      = build
MODULEDIR			= ../$(SPHINXPROJ)/

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help clean gen-api nojekyll Makefile

clean:
	-rm -fr  "$(BUILDDIR)"

gen-api: clean
	sphinx-apidoc -f -o "$(SOURCEDIR)" "$(MODULEDIR)"

nojekyll:
	touch $(BUILDDIR)/html/.nojekyll

manpage:
	pandoc source/man.rst \
	  --standalone -t man -o rho.1 \
	  --variable=section:1 \
	  --variable=date:'November 29, 2017' \
	  --variable=footer:'version 0.0.31' \
	  --variable=header:'rho User Commands'

man-html:
	pandoc source/man.rst \
	  --standalone -o man.html

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
