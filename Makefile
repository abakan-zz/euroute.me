.PHONY: help demo start stop

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  deme       to start demo"
	@echo "  deme       to login to server"
	@echo "  start      to start application"
	@echo "  stop       to stop application"

demo:
	python routeme.py

login:
	ssh eurouteme -i eurouteme.pem

start:
	sudo supervisord -c supervisord.conf

stop:
	sudo kill $(cat supervisord.pid