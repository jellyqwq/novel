import os

os.chdir(os.path.dirname(__file__))

book_list = os.listdir(os.getcwd())
for chapter_index in book_list:
    path = os.getcwd()+os.sep+chapter_index
    if os.path.isdir(path) and chapter_index != '__pycache__':
        second_list = os.listdir(path)
        for el in second_list:
            if '.md' == el[-3:]:
                with open('README.md', 'a', encoding='utf-8') as f:
                    f.write('- [{}](/{}/{}.md)\n'.format(\
                        chapter_index, chapter_index.replace(' ','%20'), el.replace(' ','%20')))
