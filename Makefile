RUN = poetry run
DOCTEST = $(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE


all: test
test: pytest test-docs

pytest:
	$(RUN) pytest

test-docs:
	$(DOCTEST) src/malco/runner.py src/malco/run/*.py src/malco/prepare/*.py src/malco/post_process/*.py 

%-doctest: %
	$(DOCTEST) $<
