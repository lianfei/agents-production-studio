.PHONY: run test package clean

run:
	python -m agents_corpus_workflow.cli serve-api --source-root . --output-dir ./tmp --host 127.0.0.1 --port 8765

test:
	python -m unittest discover -s tests

package:
	bash deployment/scripts/package_release.sh

clean:
	rm -rf build dist tmp *.egg-info
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
