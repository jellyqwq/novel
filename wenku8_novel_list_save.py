import random
import time
import requests
import logging as log
import os
from multiprocessing import Pool

log.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=log.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
os.chdir(os.path.dirname(__file__))

class X:
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
        }
        self.num_list = []
        self.temp = []
        for i in range(1999,3000):
            self.temp.append(i)

    def sx(self, i):
        r = requests.get(url=f'https://www.wenku8.net/novel/2/{i}/index.htm',headers=self.headers)
        if r.status_code != 404:
            log.info('{} 200'.format(i))
            return i
        else:
            log.info('{} 404'.format(i))
        time.sleep(random.random())   
 
    def mul(self):
        pool = Pool()
        x = pool.map(self.sx,self.temp)
        pool.close()
        pool.join()
        for i in x:
            if i != None:
                self.num_list.append(i)
    
    def save(self):
        with open('list.py', 'w', encoding='utf-8') as f:
            f.write('novel_list = {}'.format(self.num_list))

if __name__ == "__main__":
    x = X()
    x.mul()
    x.save()