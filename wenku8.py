import os
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
import logging as log
from novel_list import *
from multiprocessing import Pool

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

    def make_index_md(self):
        li = os.listdir('./{}-{}/'.format(self.novel_title, self.novel_author))
        if '{}.md'.format(self.novel_title) in li:
            return '- [{}](/{}-{}/{}.md)\n'.format(self.novel_title, self.novel_title.replace(' ','%20'), self.novel_author.replace(' ','%20'), self.novel_title.replace(' ','%20'))
        with open('./{}-{}/{}.md'.format(self.novel_title, self.novel_author, self.novel_title), 'w', encoding='utf-8') as f:
            for roll in self.info_dict.keys():
                f.write('- [{}](/{}-{}/{})\n'.format(roll, self.novel_title.replace(' ','%20'), self.novel_author.replace(' ','%20'), roll.replace(' ','%20')))
                for chapter in self.info_dict[roll].keys():
                    chapter = re.sub(r'\*', '＊', chapter)
                    chapter = re.sub(r'\?', '？', chapter)
                    f.write('  - [{}](/{}-{}/{}/{}.md)\n'.format(chapter, self.novel_title.replace(' ','%20'), self.novel_author.replace(' ','%20'), roll.replace(' ','%20'), chapter.replace(' ','%20')))
        
    
    def save_novel(self):
        self.get_index_html()
        self.get_title_author()
        self.get_detail_info()
        self.novel_title = re.sub(r'\?','？', self.novel_title)
        self.novel_title = re.sub(r'\.','。', self.novel_title)
        self.novel_title = re.sub(r'\:','：', self.novel_title)
        self.novel_author = re.sub(r'\?','？', self.novel_author)
        self.novel_author = re.sub(r'\.','。', self.novel_author)
        self.novel_author = re.sub(r'\:','：', self.novel_author)
        for roll in self.info_dict.keys():
            folder_roll = re.sub(r'\?','？', roll)
            os.makedirs('./{}-{}/{}/'.format(self.novel_title, self.novel_author, folder_roll), exist_ok=True)
            li = os.listdir('./{}-{}/{}/'.format(self.novel_title, self.novel_author, folder_roll))
            for chapter in self.info_dict[roll].keys():
                self.get_article(self.get_novel_url(self.info_dict[roll][chapter]))
                chapter = re.sub(r'\*', '＊', chapter)
                chapter = re.sub(r'\?', '？', chapter)
                chapter = re.sub(r'/', '-', chapter)
                chapter = re.sub(r'\"','\'',chapter)
                if '{}.md'.format(chapter) in li:
                    os.system('cls')
                    log.info('{}.md 已存在'.format(chapter))
                    break
                with open('./{}-{}/{}/{}.md'.format(self.novel_title, self.novel_author, folder_roll, chapter), 'w', encoding='utf-8') as f:
                    f.write('<p align="center">{}</p>\n\n'.format(chapter))
                    for i in self.contents:
                        if 'http://pic.wenku8.com/pictures' not in i:
                            f.write('{}\n\n'.format(i))
                        else:
                            f.write('![image]({})\n\n'.format(i))
                os.system('cls')
                log.info('{}-{} 保存成功'.format(roll, chapter))
                self.contents = []
                # time.sleep(random.random())
            self.make_index_md()
        return '- [{}](/{}-{}/{}.md)\n'.format(self.novel_title, self.novel_title.replace(' ','%20'), self.novel_author.replace(' ','%20'), self.novel_title.replace(' ','%20'))
        
def main(novel):
    return Wenku8(f'https://www.wenku8.net/novel/2/{novel}/index.htm').save_novel()
    
if __name__ == "__main__":
    # pool = Pool()
    # x = pool.map(main, sorted(novel_list, reverse=True))
    # pool.close()
    for novel in novel_list:
        x = main(novel)
        with open('README.md', 'a', encoding='utf-8') as f:
            for i in x:
                f.write(i)