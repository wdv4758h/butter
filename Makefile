# Most of this values here are auto deteted from setup.py and may should ot need to be
# changed

SRC=`$(PYTHON) ./setup.py --name` # this is a rough guess, override it if need be
PYTHON_VER=3.4
PYTHON=`which python$(PYTHON_VER)`
PYTEST=`which py.test-$(PYTHON_VER)`
DESTDIR=/
BUILDIR=$(CURDIR)/dist/debian/${SRC}
PROJECT=`$(PYTHON) ./setup.py --name`
VERSION=`$(PYTHON) ./setup.py --version`
TEST_PATH=tests
PREFIX=/usr

SPHINX_OPTS     =
SPHINX_BUILD    = sphinx-build
SPHINX_APIDOC   = sphinx-apidoc
PAPER           =
PAPER_OPT       =
DOC_BUILD_DIR   = docs/build
DOC_SOURCE_DIR  = docs/source
ALL_SPHINX_OPTS = -d $(DOC_BUILD_DIR)/doctrees $(PAPER_OPT$(PAPER)) $(SPHINX_OPTS) $(DOC_SOURCE_DIR)

VIRTUAL_DIR = env

TEST_CMD=start false
PROFILER=cProfile
#PROFILER=profile
PROFILE_OPTS = 
TRACE_OPTS = -c -m
TRACE_OPTS = -t -g
PROFILE_DIR = profile
TRACE_DIR = $(PROFILE_DIR)

all:

help:
	@echo Commands: virtual, init, doc, cdoc, test, clean, build, install, tar, tgz, rpm, deb

# list of 'virtual' commands that have no real backing file
.PHONY: help init virtual doc cdoc test clean tar tgz build rpm deb install coverage profile

init: requirements.txt
	pip install -r requirements.txt

# virtual virtual package :D
virtual: ${VIRTUAL_DIR}
	:
	
${VIRTUAL_DIR}:
	virtualenv -p ${PYTHON} $(VIRTUAL_DIR)

smoke: flake8 doc test dist rpm deb
	:

doc:
	rm -rf ./$(DOC_BUILD_DIR)/*
	$(SPHINX_BUILD) -b html $(ALL_SPHINX_OPTS) $(DOC_BUILD_DIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(DOC_BUILD_DIR)/html."

update-docs:
	$(SPHINX_APIDOC) -o $(DOC_SOURCE_DIR) $(PROJECT)
	@echo
	@echo "API documents updated."

cdoc:
	rm -rf ./$(DOC_BUILD_DIR)/*
	$(SPHINX_BUILD) -b html $(ALL_SPHINX_OPTS) $(DOC_BUILD_DIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(DOC_BUILD_DIR)/html."

test:
	${PYTHON} ./setup.py test
    
clean:
	$(PYTHON) ./setup.py clean
	rm -rf ./$(DOC_BUILD_DIR)/*
	rm -rf build/ debian/$(PROJECT)* debian/*stamp* debian/files MANIFEST *.egg-info *.egg
	find . -name '*.pyc' -delete
	# Cleanup __pycache__ dirs
	python -c 'from cffi.verifier import cleanup_tmpdir as f; f()'
	
	#remove tox enviroments
	-rm -rf .tox
	
dist: tar gzip bzip2 zip
	:
    
tar:
	rm dist/*.tar || true
	${PYTHON} ./setup.py sdist --formats=tar

gzip:
	rm dist/*.tar.gz || true
	$(PYTHON) ./setup.py sdist --formats=gztar

bzip2:
	rm dist/*.tar.bz2 || true
	$(PYTHON) ./setup.py sdist --formats=bztar

zip:
	rm dist/*.zip || true
	$(PYTHON) ./setup.py sdist --formats=zip
	
build:
	$(PYTHON) ./setup.py build

rpm:
	rm -rf dist/*.rpm
	$(PYTHON) setup.py sdist --formats=rpm
	rpmbuild -bb dist/${PROJECT}.spec
	mv ~/rpmbuild/RPMS/noarch/$(PROJECT)*.rpm dist

deb:
	rm -rf dist/*.deb
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	dpkg-buildpackage -b -rfakeroot -us -uc
	rm ../$(PROJECT)*.orig.tar.gz
	rm ../$(PROJECT)*.changes
	mv ../$(PROJECT)*.deb dist/

coverage: ${VIRTUAL_DIR}/bin/coverage
	${PYTEST} --cov-report=annotate --cov-report=term --cov=$(PROJECT) --doctest-modules $(TEST_PATH)
	
${VIRTUAL_DIR}/bin/coverage: ${VIRTUAL_DIR}
	${VIRTUAL_DIR}/bin/pip install pytest-cov
	
pylint: ${VIRTUAL_DIR}/bin/pylint
	${VIRTUAL_DIR}/bin/pylint $(SRC)
	
${VIRTUAL_DIR}/bin/pylint: ${VIRTUAL_DIR}
	${VIRTUAL_DIR}/bin/pip install pylint
	
flake8:
	${VIRTUAL_DIR}/bin/flake8 $(SRC)
	
${VIRTUAL_DIR}/bin/flake8: ${VIRTUAL_DIR}
	${VIRTUAL_DIR}/bin/pip install flake8
	
pep8: $(VIRTUAL_DIR)/bin/pep8
	${VIRTUAL_DIR}/bin/pep8 $(SRC)

${VIRTUAL_DIR}/bin/pep8: ${VIRTUAL_DIR}
	$(VIRTUAL_DIR)/bin/pip install pep8	

pyflakes:
	${VIRTUAL_DIR}/bin/pyflake $(SRC)

${VIRTUAL_DIR}/bin/pyflakes: ${VIRTUAL_DIR}
	$(VIRTUAL_DIR)/bin/pip install pyflakes

profile:
	$(PYTHON) -m $(PROFILER) -o $(PROFILE_DIR)/$(PROJECT).profile $(PROFILE_OPTS) $(SRC)/__main__.py $(TEST_CMD)
	$(PYTHON) -m pstats $(PROFILE_DIR)/$(PROJECT).profile

trace:
	$(PYTHON) -m trace -C $(TRACE_DIR) $(TRACE_OPTS) $(SRC)/__main__.py $(TEST_CMD)

install:
	$(PYTHON) ./setup.py install --root $(DESTDIR) $(COMPILE) --prefix $(PREFIX)

develop:
	$(PYTHON) ./setup.py develop
	
pypi:
	$(PYTHON) ./setup.py sdist --formats=zip,bztar upload
