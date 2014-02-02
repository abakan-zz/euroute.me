.PHONY: help demo start

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  deme       to start demo"
	@echo "  start      to start server"

demo:
	python routeme.py

start:
	sudo supervisord -c supervisord.conf