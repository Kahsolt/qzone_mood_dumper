all:
	python dumper.py

markdown:
	python export.py markdown

sql:
	sqlite3 data.sqlite

stat:
	@sqlite3 data.sqlite 'SELECT "Total: ", COUNT(*) FROM Mood;'

clean:
	rm -f *.log
