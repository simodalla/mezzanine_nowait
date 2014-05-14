.PHONY: clean-pyc clean-build docs

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-ft - run functional tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "test-all-ft - run functional tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "coverage-console - check code coverage quickly with the default Python and display result only into console"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "sdist - package"
	@echo "celery-server - start celery server"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 --exclude=migrations nowait functional_tests

test:
	python project_template/manage.py test nowait

test-ft:
	python project_template/manage.py test functional_tests

test-all:
	tox

test-all-ft: tox-all
	tox -e py26-django16-ft,py27-django16-ft,py33-django16-ft

coverage-console:
	coverage run --source nowait --omit=nowait/migrations/*,*/tests/factories.py project_template/manage.py test nowait
	coverage report -m

coverage: coverage-console
	coverage html
	open htmlcov/index.html

docs:
	rm -f docs/mezzanine_nowait.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ mezzanine_nowait
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

sdist: clean
	python setup.py sdist
	ls -l dist

celery-server:
	celery --workdir=project_template/ -A project_template worker -l info
