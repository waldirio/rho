DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= rho

BINDIR  = bin

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help           to show this message"
	@echo "  all            to to execute all following targets (except test)"
	@echo "  lint           to run all linters"
	@echo "  lint-flake8    to run the flake8 linter"
	@echo "  lint-pylint    to run the pylint linter"
	@echo "  test           to run unit tests"
	@echo "  test-coverage  to run unit tests and measure test coverage"

all: build lint tests-coverage

manpage:
	@cd doc; $(MAKE) manpage

docs:
	@cd doc; $(MAKE) gen-api; $(MAKE) html; $(MAKE) nojekyll; $(MAKE) manpage

gen-python-docs:
	@cd doc; $(MAKE) gen-python
	mv doc/fact_docs.py rho

build: clean
	$(PYTHON) setup.py build -f

build-rpm: clean
	$(PYTHON) setup.py bdist_rpm

clean:
	-rm -f  MANIFEST etc/version
	-rm -rf dist/ build/ test/coverage rpm-build/ rho.egg-info/
	-rm -rf *~
	-rm -rf docs/*.gz

install: build
	$(PYTHON) setup.py install -f

tests:
	py.test -v

tests-coverage:
	py.test -v --cov=rho --cov=library

lint-flake8:
	flake8 . --ignore D203 --exclude fact_docs.py

lint-pylint:
	pylint --disable=duplicate-code */*.py

lint: lint-flake8 lint-pylint

# Travis doesn't use the -3 prefix with Python 3 executables, so we
# need to keep these separate from the build targets that Travis will
# use.
tests-3:
	-py.test-3 -v

tests-coverage-3:
	-py.test-3 -v --cov=rho --cov=library

lint-flake8-3:
	python3 -m flake8 . --ignore D203 --exclude fact_docs.py

lint-pylint-3:
	python3 -m pylint --disable=duplicate-code,locally-disabled,bad-option-value */*.py -rn

lint-3: lint-flake8-3 lint-pylint-3

# But for local testing, we want to be able to test Python 2 and 3
# together conveniently, so we also have these targets.
tests-all: tests tests-3

lint-all: lint lint-3
