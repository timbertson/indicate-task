0: README.md
	mkzero-gfxmonk -p indicate_task indicate-task.xml

README.md: phony
	cat _README.template > README.md
	./indicate_task/main.py --help | sed -e 's/^/    /' >> README.md

.PHONY: phony
