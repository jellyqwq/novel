from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOVELS_DIR = ROOT / "novels"
INDEX_PATH = ROOT / "INDEX.md"

AUTHOR_MARK = "-作者："
EXCLUDED_ROOT_DIRS = {".git", "__pycache__", NOVELS_DIR.name}

PINYIN_RANGES = (
    (-20319, -20284, "a"),
    (-20283, -19776, "b"),
    (-19775, -19219, "c"),
    (-19218, -18711, "d"),
    (-18710, -18527, "e"),
    (-18526, -18240, "f"),
    (-18239, -17923, "g"),
    (-17922, -17418, "h"),
    (-17417, -16475, "j"),
    (-16474, -16213, "k"),
    (-16212, -15641, "l"),
    (-15640, -15166, "m"),
    (-15165, -14923, "n"),
    (-14922, -14915, "o"),
    (-14914, -14631, "p"),
    (-14630, -14150, "q"),
    (-14149, -14091, "r"),
    (-14090, -13319, "s"),
    (-13318, -12839, "t"),
    (-12838, -12557, "w"),
    (-12556, -11848, "x"),
    (-11847, -11056, "y"),
    (-11055, -10247, "z"),
)


@dataclass(frozen=True)
class NovelEntry:
    label: str
    target: Path
    group: str
    sort_key: tuple[str, str, str]


def title_from_dir(dirname: str) -> str:
    return dirname.split(AUTHOR_MARK, 1)[0].strip() or dirname


def is_cjk(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def strip_leading_marks(text: str) -> str:
    for index, char in enumerate(text.strip()):
        if char.isalnum() or is_cjk(char):
            return text.strip()[index:]
    return text.strip()


def pinyin_initial(char: str) -> str | None:
    if char.isascii() and char.isalnum():
        return char.casefold()

    try:
        encoded = char.encode("gb2312")
    except UnicodeEncodeError:
        return None

    if len(encoded) != 2:
        return None

    code = encoded[0] * 256 + encoded[1] - 65536
    for start, end, initial in PINYIN_RANGES:
        if start <= code <= end:
            return initial
    return None


def initials_for(text: str) -> str:
    initials: list[str] = []
    for char in strip_leading_marks(text):
        initial = pinyin_initial(char)
        if initial:
            initials.append(initial)
        elif char.isascii() and not char.isspace():
            initials.append(char.casefold())
        elif is_cjk(char):
            initials.append("~" + char)
    return "".join(initials) or "~"


def group_for(text: str) -> str:
    for char in strip_leading_marks(text):
        initial = pinyin_initial(char)
        if not initial:
            continue
        first = initial[0]
        if first.isdigit():
            return "0-9"
        if "a" <= first <= "z":
            return first.upper()
    return "#"


def markdown_files(book_dir: Path) -> list[Path]:
    return sorted(
        (path for path in book_dir.iterdir() if path.is_file() and path.suffix.lower() == ".md"),
        key=lambda path: (initials_for(path.stem), path.name.casefold()),
    )


def is_legacy_book_dir(path: Path) -> bool:
    if not path.is_dir() or path.name in EXCLUDED_ROOT_DIRS or path.name.startswith("."):
        return False
    return AUTHOR_MARK in path.name or bool(markdown_files(path))


def migrate_legacy_book_dirs() -> list[str]:
    NOVELS_DIR.mkdir(exist_ok=True)
    moved: list[str] = []

    candidates = sorted(
        (path for path in ROOT.iterdir() if is_legacy_book_dir(path)),
        key=lambda path: (initials_for(title_from_dir(path.name)), path.name.casefold()),
    )

    for source in candidates:
        target = NOVELS_DIR / source.name
        if target.exists():
            raise FileExistsError(f"target already exists: {target}")
        shutil.move(str(source), str(target))
        moved.append(source.name)

    return moved


def main_markdown_file(book_dir: Path) -> Path | None:
    files = markdown_files(book_dir)
    preferred = book_dir / f"{title_from_dir(book_dir.name)}.md"
    if preferred in files:
        return preferred
    if files:
        return files[0]

    nested_files = sorted(
        book_dir.rglob("*.md"),
        key=lambda path: (initials_for(path.stem), path.relative_to(book_dir).as_posix().casefold()),
    )
    preferred_name = f"{title_from_dir(book_dir.name)}.md"
    for path in nested_files:
        if path.name == preferred_name:
            return path
    return nested_files[0] if nested_files else None


def markdown_link(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return f"/{relative}".replace(" ", "%20")


def escape_label(text: str) -> str:
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def collect_entries() -> list[NovelEntry]:
    entries: list[NovelEntry] = []
    if not NOVELS_DIR.exists():
        return entries

    for book_dir in NOVELS_DIR.iterdir():
        if not book_dir.is_dir() or book_dir.name.startswith("."):
            continue

        target = main_markdown_file(book_dir)
        if target is None:
            continue

        title = title_from_dir(book_dir.name)
        group = group_for(title)
        entries.append(
            NovelEntry(
                label=book_dir.name,
                target=target,
                group=group,
                sort_key=(group, initials_for(title), book_dir.name.casefold()),
            )
        )

    group_order = {group: index for index, group in enumerate(["0-9", *"ABCDEFGHIJKLMNOPQRSTUVWXYZ", "#"])}
    return sorted(
        entries,
        key=lambda entry: (
            group_order.get(entry.group, len(group_order)),
            entry.sort_key[1],
            entry.sort_key[2],
        ),
    )


def write_index(entries: list[NovelEntry]) -> None:
    lines = [
        "# 小说索引",
        "",
        "> 本文件由 `python3 main_index.py` 自动生成；索引按书名首字母和中文拼音首字母排序。",
        "",
        f"共收录 {len(entries)} 本小说。",
        "",
    ]

    current_group = ""
    for entry in entries:
        if entry.group != current_group:
            if current_group:
                lines.append("")
            lines.extend([f"## {entry.group}", ""])
            current_group = entry.group

        lines.append(f"- [{escape_label(entry.label)}]({markdown_link(entry.target)})")

    INDEX_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    moved = migrate_legacy_book_dirs()
    entries = collect_entries()
    write_index(entries)

    print(f"moved {len(moved)} root book directories into {NOVELS_DIR.name}/")
    print(f"indexed {len(entries)} novels in {INDEX_PATH.name}")


if __name__ == "__main__":
    main()
