.PHONY: help demo start stop

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  deme       to start demo"
	@echo "  start      to start server"
	@echo "  stop       to stop server"

demo:
	python routeme.py

start:
	sudo supervisord -c supervisord.conf

stop:
	sudo kill $(cat supervisord.pid