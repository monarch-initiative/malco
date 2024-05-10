RUN = poetry run
DOCTEST = $(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE


all: test
test: pytest test-docs

pytest:
	$(RUN) pytest

test-docs:
	$(DOCTEST) src/malco/*.py src/malco/*/*.py

%-doctest: %
	$(DOCTEST) $<
