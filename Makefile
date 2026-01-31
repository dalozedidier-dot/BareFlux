SHELL := /usr/bin/env bash

.PHONY: help orchestrate riftlens nulltrace voidmark

help:
	@echo "Targets:"
	@echo "  make orchestrate   Run BareFlux orchestrator (expects modules as siblings or ./modules/)"
	@echo "  make riftlens      Run RiftLens only"
	@echo "  make nulltrace     Run NullTrace only"
	@echo "  make voidmark      Run VoidMark only"

orchestrate:
	chmod +x run_modules.sh
	./run_modules.sh --out _bareflux_out

riftlens:
	cd ../RiftLens && python src/rift_lens.py tests/data/test_multi.csv --corr-threshold 0.7 --output-dir outputs

nulltrace:
	cd ../NullTrace && python src/null_trace.py tests/data/current.csv --previous-shadow tests/data/previous_shadow.csv --output-dir outputs

voidmark:
	@if [ -f ../RiftLens/outputs/graph_report.json ]; then \
	  cd ../VoidMark && python src/void_mark.py ../RiftLens/outputs/graph_report.json --vault-dir vault_test; \
	else \
	  echo "RiftLens report absent, fallback payload"; \
	  echo '{"payload":"fallback"}' > /tmp/bareflux_payload.json; \
	  cd ../VoidMark && python src/void_mark.py /tmp/bareflux_payload.json --vault-dir vault_test; \
	fi
