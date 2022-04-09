import os
import random
import time
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
import logging as log

log.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=log.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
os.chdir(os.path.dirname(__file__))

class Wenku8():
    def __init__(self, index_html_url):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
        }
        self.soup = None
        self.novel_title = None
        self.novel_author = None
        self.info_list = None
        self.info_dict = {}
        self.index_html_url = index_html_url
        self.article = None
        self.article_title = None
        self.contents = []

    def get_html_encoding(self, response):
        return re.findall(r'<meta.*content=".*charset=(.*?)"', response.text)[0]

    # 获取soup对象
    def get_index_html(self):
        r = requests.get(url=self.index_html_url,headers=self.headers)
        # 正则匹配原始网页的编码,并重新设置,为了下面bs4解析做准备
        r.encoding = self.get_html_encoding(r)
        self.soup = BeautifulSoup(r.text, 'html.parser')
    
    # 获取小说的名字和作者
    def get_title_author(self):
        self.novel_title = self.soup.find(id='title').get_text()
        self.novel_author = self.soup.find(id='info').get_text()
        
    def get_detail_info(self):
        self.info_list = self.soup.table.find_all('td')
        # # 初始化
        for i in self.info_list:
            if i['class'] == ['vcss']:
                key_lock = str(i.string)
                self.info_dict[key_lock] = {}
            if i['class'] == ['ccss'] and i.a:
                self.info_dict[key_lock][str(i.string)] = i.a['href']
            
    def get_novel_url(self, short_url):
        # return self.index_html_url.replace('index.htm', short_url)
        return re.sub(r'index.htm', short_url, self.index_html_url)

    def get_article(self, url):
        r = requests.get(url, headers=self.headers)
        r.encoding = self.get_html_encoding(r)
        self.article = BeautifulSoup(r.text, 'html.parser')
        # self.article_title = self.article.find(id='title').get_text()
        __temp = self.article.find(id='content').contents
        for i in __temp:
            if i != '\n' and i.name != 'ul' and i.name != 'br':
                if not isinstance(i,Tag):
                    i = re.sub('\r\n\xa0\xa0\xa0\xa0','', i)
                    self.contents.append(re.sub('\r\n','', i))
                elif i.name == 'div':
                    self.contents.append(i.a['href'])

    def save_novel(self):
        self.get_index_html()
        self.get_title_author()
        self.get_detail_info()
        for roll in self.info_dict.keys():
            os.makedirs('./{}-{}/{}/'.format(self.novel_title, self.novel_author, roll), exist_ok=True)
            for chapter in self.info_dict[roll].keys():
                self.get_article(self.get_novel_url(self.info_dict[roll][chapter]))
                with open('./{}-{}/{}/{}-{}.md'.format(self.novel_title, self.novel_author, roll, roll, chapter), 'w', encoding='utf-8') as f:
                    f.write('<p align="center">{}</p>\n'.format(chapter))
                    for i in self.contents:
                        f.write('{}\n'.format(i))
                log.info('{}-{}保存成功'.format(roll, chapter))
                self.contents = []
                time.sleep(random.random())

if __name__ == "__main__":
    w = Wenku8(input('输入小说索引页的URL:'))
    # w = Wenku8('https://www.wenku8.net/novel/2/2255/index.htm')
    w.save_novel()
    input('按任意键继续...')

