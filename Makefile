lint:
	djlint . --lint
	ruff check .

test:
	echo "Test"

test-coverage:
	pdm run python -m coverage report --format="markdown"