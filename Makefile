.PHONY: test report pack

test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests

report:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli scan examples --format md --out examples/report.md
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli scan examples --format json --out examples/report.json

pack:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli pack examples --out examples/packed
