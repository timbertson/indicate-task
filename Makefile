0: README
	mkzero-gfxmonk -p indicate_task.py indicate-task.xml

README: phony
	cat _README.template > README
	./indicate_task.py --help >> README

.PHONY: phony
