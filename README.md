# novel

一个使用 GitHub Markdown 存放和阅读小说文本的轻量仓库。

## 阅读入口

[打开小说索引](INDEX.md)

## 内容组织

- `novels/`：小说正文目录，每本小说一个子目录。
- `INDEX.md`：自动生成的小说索引，按书名首字母和中文拼音首字母排序。
- `main_index.py`：整理目录并重新生成索引的脚本。

## 更新索引

```bash
python3 main_index.py
```
