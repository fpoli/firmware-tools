# The ":=" definitions are executed once at startup
# The "=" definitions are executed whenever they are used
CURR_DIR := $(shell pwd)

linter:
	pep8 --ignore="E221" --max-line-length=100 *.py
