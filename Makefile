all:
	python dumper.py dump

md:
	python dumper.py export

sql:
	sqlite3 data.sqlite

stat:
	@sqlite3 data.sqlite 'SELECT "Total: ", COUNT(*) FROM Mood;'

clean:
	rm -f *.log
