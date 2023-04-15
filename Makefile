isort:
	isort .

flake:
	flake8 .


black:
	black .

supercode: isort black flake

test:
	pytest .

