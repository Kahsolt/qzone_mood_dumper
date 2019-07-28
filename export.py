#!/usr/bin/env python3
# 2019/07/28 

from .dumper import Mood, setup_db, teardown_db

DATA_DIR = 'data'
TEMPLATE_MARKDOWN_FILE = 'template.md'

def to_markdown():
  os.makedirs(os.path.join(BASE_PATH, DATA_DIR), exist_ok=True)

  moods = Mood.all()
  for mood in moods:
    md = ('# %s\n\n%s\n\nby Kahsolt\n%s\n' 
          % (mood.title, mood.content, mood.timestamp))
    fn = '%s %s.md' % (mood.timestamp.isoformat().split('T')[0], mood.title)
    fp = os.path.join(BASE_PATH, DATA_DIR, fn)
    with open(fp, 'w') as fh:
      fh.write(md)
      fh.flush()

# main
if __name__ == '__main__':
  try:
    setup_db()
    to_markdown()
  except Exception as e:
    logging.error(e)
    import traceback; traceback.print_exc()
  finally:
    teardown_db()