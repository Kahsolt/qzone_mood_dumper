#!/usr/bin/env python3
# 2019/07/19

import os
import time
import json
import sqlite3
import logging
from datetime import datetime
from requests.sessions import Session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as cond
from selenium.webdriver.support.wait import WebDriverWait

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
URL_BASE = 'https://user.qzone.qq.com'
URL_API_BASE = URL_BASE + '/proxy/domain/taotao.qq.com/cgi-bin'
URL_LIST = URL_API_BASE + '/emotion_cgi_msglist_v6'
URL_DETAIL = URL_API_BASE + '/emotion_cgi_msgdetail_v6'
HEADERS = { 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1' }

DB_FILE = 'data.sqlite'
UPDATE_MODE = os.getenv('update').lower() != 'false'
PAGE_SIZE = 20

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s: [%(levelname)s] %(message)s')

# Data storage
class SQLite3:
  
  def __init__(self, dbfile=os.path.join(BASE_PATH, DB_FILE)):
    self.conn = sqlite3.connect(dbfile)
    
  def query(self, sql, params=None):
    cur = self.conn.cursor()
    if params: cur.execute(sql, params)
    else: cur.execute(sql)
    data = cur.fetchall()
    cur.close()
    self.conn.commit()
    return data
    
  def close(self):
    self.conn.close()

class Mood:

  engine = None
  
  def __init__(self, **kwargs):
    table_columns = ['id', 'title', 'content', 'timestamp']
    for col in table_columns:
      setattr(self, col, kwargs.get(col))
  
  def __repr__(self):
    return '#%s - %s\t%s: %s' % (self.id, self.timestamp.isoformat(), self.title, 
                                len(self.content) <= 50 and self.content or self.content[:50] + '...')
  
  @classmethod
  def bind(cls, engine):
    cls.engine = engine
    
    sql = ('CREATE TABLE IF NOT EXISTS %s ('
           '  id INTEGER PRIMARY KEY AUTOINCREMENT,'
           '  title TEXT,'
           '  content TEXT,'
           '  timestamp TIMESTAMP'
           ');' % cls.__name__)
    engine.query(sql)

  @classmethod
  def exists(cls, timestamp=None, title=None, content=None):
    if timestamp:
      sql = 'SELECT COUNT(*) FROM %s WHERE timestamp = ?;' % cls.__name__
      data = cls.engine.query(sql, (timestamp,))
      if data and data[0][0]: return True

    if title:
      sql = 'SELECT COUNT(*) FROM %s WHERE title = ?;' % cls.__name__
      data = cls.engine.query(sql, (title,))
      if data and data[0][0]: return True

    if content:
      sql = "SELECT COUNT(*) FROM %s WHERE content LIKE '%%?%%';" % cls.__name__
      data = cls.engine.query(sql, (content,))
      if data and data[0][0]: return True
    
    return False
  
  @classmethod
  def get(cls, id):
    sql = "SELECT id, title, content, timestamp FROM %s WHERE id = ?;" % cls.__name__
    data = cls.engine.query(sql, (id,))
    if data:
      id, title, content, timestamp = data[0]
      return Mood(id=id, title=title, content=content, timestamp=timestamp)
    return None
  
  @classmethod
  def all(cls):
    sql = "SELECT id, title, content, timestamp FROM %s;" % cls.__name__
    data = cls.engine.query(sql)
    moods = [ ]
    for row in data:
      id, title, content, timestamp = row
      mood = Mood(id=id, title=title, content=content, timestamp=timestamp)
      moods.append(mood)
    return moods

  def save(self):
    sql = 'INSERT INTO %s(title, content, timestamp) VALUES(?, ?, ?);' % self.__class__.__name__
    self.engine.query(sql, (self.title, self.content, self.timestamp))
    sql = 'SELECT last_insert_rowid();'
    data = self.engine.query(sql)
    if data: self.id = data[0][0]

# Operations
setup_db = lambda: Mood.bind(SQLite3())
teardown_db = lambda: Mood.engine.close()

def dump(update=UPDATE_MODE):
  # open browser
  profile = webdriver.FirefoxProfile()
  profile.set_preference('permissions.default.image', 2)
  profile.set_preference('browser.migration.version', 9001)
  options = webdriver.FirefoxOptions()
  options.add_argument('--disable-extensions')
  options.add_argument('-headless')
  
  browser = webdriver.Firefox(options=options, firefox_profile=profile)
  browser.implicitly_wait(5)
  wait = WebDriverWait(browser, 10, poll_frequency=1)

  # login
  qq = os.getenv('qq')
  while not qq: qq = input('输入QQ号：')
  passwd = os.getenv('passwd')
  while not passwd: passwd = input('输入QQ密码：')

  browser.get(URL_BASE)
  wait.until(cond.frame_to_be_available_and_switch_to_it('login_frame'))
  wait.until(cond.element_to_be_clickable((By.ID, 'switcher_plogin')))
  browser.find_element_by_id('switcher_plogin').click()
  browser.find_element_by_id('u').send_keys(qq)
  browser.find_element_by_id('p').send_keys(passwd)
  wait.until(cond.element_to_be_clickable((By.ID, 'login_button')))
  browser.find_element_by_id('login_button').click()
  time.sleep(5)  # await for cookies

  def getCSRFToken(skey):   # transcribed from qzone source javascript snippet
    hs = 5381
    for i in skey:
      hs += (hs << 5) + ord(i)
    return hs & 0x7fffffff
    
  cookies = { c.get('name'): c.get('value') for c in browser.get_cookies() }
  token = getCSRFToken(browser.get_cookie('p_skey').get('value'))
  qzonetoken = '6938137d34171f799bd85ccfb42b80474825b4c604adfc9adbfae0bc512241f658514dea51e79051be8f'

  browser.close()
  browser.quit()

  # dump
  http = Session()
  http.headers.update(HEADERS)
  cnt, totcnt, pid = 0, -1, 1
  params = {
    'uin': qq,
    'ftype': 0,
    'sort': 0,
    'pos': 0,
    'num': PAGE_SIZE,
    'replynum': 0,
    'g_tk': token,
    'callback': 'preloadCallback',
    'code_version': 1,
    'format': 'jsonp',
    'need_private_comment': 1,
    'qzonetoken': qzonetoken,
  }
  while pid >= 0:
    if totcnt > 0 and pid * PAGE_SIZE > totcnt: break
    logging.info('[Dumper] crawling on page %d' % pid)
    params['pos'] = (pid - 1) * PAGE_SIZE
    res = http.get(URL_LIST, params=params, cookies=cookies)

    data = json.loads(res.text[16:-2])
    if totcnt < 0:
      totcnt = data.get('total')
      logging.info('[Dumper] %d mood in total' % totcnt)
    for mood in data.get('msglist'):
      timestamp = datetime.fromtimestamp(mood.get('created_time'))
      if Mood.exists(timestamp=timestamp):
        if update: return
        else: continue
      
      if mood.get('has_more_con'):    # expand if has_more
        params['tid'] = mood.get('tid')
        params['t1_source'] = mood.get('t1_source')
        params['pos'] = 0             # reset offset
        res = http.get(URL_DETAIL, params=params)
        try: data = json.loads(res.text[16:-2])
        except json.decoder.JSONDecodeError: logging.info(res.text)
        content = data.get('content')
      else:
        content = mood.get('content')
      title = '\n' in content and content.split('\n')[0] or content[:16]
      
      mood = Mood(title=title, content=content, timestamp=timestamp)
      mood.save()
      logging.info('[Save] %r' % mood)
      cnt += 1

    pid += 1
  logging.info('[Save] updated %d items in total' % cnt)

# main
if __name__ == '__main__':
  try:
    setup_db()
    dump()
  except Exception as e:
    logging.error(e)
    import traceback; traceback.print_exc()
  finally:
    teardown_db()