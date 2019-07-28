# qzone_mood_dumper

    Dump your qzone mood(说说) history to local SQL database storage
    e.g. for backup purpose or sync with your blog ([hexo](https://hexo.io/) is sweet enough)

----

## Scrrenshot
![Scrrenshot](/screenshot.png)
selenium使用无头模式，只用来登录获取cookies
拉取mood使用requests直接发异步请求
  
## Qucikstart
  - login: simply use plain method, so set envvar 'qq' for qqcode, 'passwd' for password, e.g. under windows `SET qq=137982465 && SET passwd=aWakeP@ssw0rd`
  - mode: default is update mode, it will stop scan from where last time is stopped accroding to timeline, you can `SET update=false` to force a full scan
  - dump to db: `make` or `python3 dumper.py`
  - dump to markdown: edit the (template)[/template.md], then `make to_markdown` or `python3 dumper.py to_markdown`; note that you must dump to db first

### requirements
  - `pip install selenium requests`
  - install firefox and put [geckodriver](https://github.com/mozilla/geckodriver/releases) into your %PATH% (NOTE: if you insist on using Chrome, I'm sorry you'd have to modify the source file all by yourself :(


by Kahsolt
2019/7/19
