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

build: clean
	$(PYTHON) setup.py build -f

clean:
	-rm -f  MANIFEST etc/version
	-rm -rf dist/ build/ test/coverage rpm-build/ rho.egg-info/
	-rm -rf *~
	-rm -rf docs/*.gz

install: build
	$(PYTHON) setup.py install -f

tests:
	-py.test -v

tests-coverage:
	-py.test -v --cov=rho

lint-flake8:
	flake8 . --ignore D203

lint-pylint:
	pylint --disable=duplicate-code */*.py

lint: lint-flake8 lint-pylint
