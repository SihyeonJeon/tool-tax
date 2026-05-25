.PHONY: test report pack benchmark

test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests

report:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli scan examples --format md --out examples/report.md
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli scan examples --format json --out examples/report.json
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli benchmark docs/benchmarks/public-catalogs.yml --out docs/benchmarks/public-catalogs-2026-05-25.md
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli benchmark docs/benchmarks/public-catalogs.yml --format json --out docs/benchmarks/public-catalogs-2026-05-25.json
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli doctor --mcp-config examples/host-configs/risky-mcp-config.json --no-probe --out docs/benchmarks/doctor-risk-lint-2026-05-25.md
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli doctor --mcp-config examples/host-configs/risky-mcp-config.json --no-probe --format json --out docs/benchmarks/doctor-risk-lint-2026-05-25.json

benchmark:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli benchmark docs/benchmarks/public-catalogs.yml --out docs/benchmarks/public-catalogs-2026-05-25.md
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli benchmark docs/benchmarks/public-catalogs.yml --format json --out docs/benchmarks/public-catalogs-2026-05-25.json

pack:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m tool_tax.cli pack examples --out examples/packed
