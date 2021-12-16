# QueryRuankao

软考查分爬虫，使用百度OCR识别验证码，可以配合crontab自动检测是否出成绩，以及自动查分并发送邮箱进行提醒。

程序工作原理：检测是否出了成绩，如果出了成绩，就会自动查分并发到邮箱。



## 安装

运行环境：[Python3](https://www.python.org/)

安装第三方库：`pip install -r requirements.txt`



## 运行

填写config.ini，将data、mail、BaiduOCR补充完整，运行`QueryRuankao.py`

百度OCR可以根据https://cloud.baidu.com/doc/OCR/s/dk3iqnq51教程注册，将API_KEY、SECRET_KEY写到config.ini



## crontab

Linux使用crontab定期执行该程序，实现自动检测是否出成绩，以及自动查分并发送邮箱进行提醒。

参考如下，每分钟自动运行该程序，注意修改路径。

```
* * * * *	python3 /QueryRuankao/QueryRuankao.py
```

如果config.ini中`Repeat_query = false`，当查到结果时，会将考试时间保存到QueryResult.txt文件，用于防止重复查询，因此不用担心成绩查询出来后仍然不断查询。

