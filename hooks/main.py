from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Dict, List, Tuple

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.nav import Navigation, Page

TOC_MARKER = "<!-- AUTO_TOC -->"
HEADING_PATTERN = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
TAG_PATTERN = re.compile(r"<[^>]+>")
# 中文字符分单个统计；英文按单词统计
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")
ENGLISH_PATTERN = re.compile(r"[A-Za-z0-9_]+")
CALLOUT_HEADER_PATTERN = re.compile(r"^\s*>\s*\[!([A-Za-z0-9_-]+)\](?:\s*(.*))?$")
CALLOUT_BODY_PATTERN = re.compile(r"^\s*>\s?(.*)$")


def _strip_md(text: str) -> str:
    text = TAG_PATTERN.sub("", text)
    text = re.sub(r"[`*_~\[\]()]", "", text)
    return text.strip()


def _slugify(text: str) -> str:
    text = _strip_md(text).lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-\u4e00-\u9fff]", "", text)
    return text


def _build_toc_list(markdown: str) -> List[Tuple[int, str, str]]:
    items: List[Tuple[int, str, str]] = []
    for hashes, title in HEADING_PATTERN.findall(markdown):
        level = len(hashes)
        clean = _strip_md(title)
        slug = _slugify(clean)
        items.append((level, clean, slug))
    return items


def _render_toc(items: List[Tuple[int, str, str]]) -> str:
    if not items:
        return ""
    lines = ["> [!abstract] 本文导览", "> "]
    for level, title, _slug in items:
        indent = "  " * (level - 2)
        lines.append(f"> {indent}- {title}")
    lines.append("")
    return "\n".join(lines)


def _convert_obsidian_callouts(markdown: str) -> str:
    lines = markdown.splitlines()
    out: List[str] = []
    i = 0

    while i < len(lines):
        header = CALLOUT_HEADER_PATTERN.match(lines[i])
        if not header:
            out.append(lines[i])
            i += 1
            continue

        callout_type = header.group(1).lower()
        callout_title = (header.group(2) or "").strip()
        if callout_title:
            out.append(f"!!! {callout_type} \"{callout_title}\"")
        else:
            out.append(f"!!! {callout_type}")

        i += 1
        has_body = False
        while i < len(lines):
            body = CALLOUT_BODY_PATTERN.match(lines[i])
            if not body:
                break
            has_body = True
            text = body.group(1)
            out.append(f"    {text}" if text else "    ")
            i += 1

        if not has_body:
            out.append("    ")

    converted = "\n".join(out)
    if markdown.endswith("\n"):
        converted += "\n"
    return converted


def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, files):
    if TOC_MARKER in markdown:
        toc_items = _build_toc_list(markdown)
        rendered = _render_toc(toc_items)
        markdown = markdown.replace(TOC_MARKER, rendered)

    return _convert_obsidian_callouts(markdown)


class _TextExtractor(HTMLParser):
    """提取HTML文本内容，排除代码块和脚本"""
    def __init__(self):
        super().__init__()
        self.parts: List[str] = []
        self.in_code = False  # 跟踪是否在代码块内

    def handle_starttag(self, tag: str, attrs) -> None:
        # 标记进入代码块
        if tag in ("code", "pre", "script", "style"):
            self.in_code = True

    def handle_endtag(self, tag: str) -> None:
        # 标记离开代码块
        if tag in ("code", "pre", "script", "style"):
            self.in_code = False

    def handle_data(self, data: str) -> None:
        # 仅收集非代码块的文本
        if not self.in_code:
            self.parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(self.parts)


def _reading_stats(html: str) -> Dict[str, int]:
    """
    计算阅读统计
    - 中文按字数计（每个汉字为1字）
    - 英文按单词数计（连续字母数字为1词）
    - 阅读时长 = 中文字/300 + 英文词/200
    """
    parser = _TextExtractor()
    parser.feed(html)
    text = parser.text
    
    # 统计中文字数
    chinese_chars = CHINESE_PATTERN.findall(text)
    chinese_count = len(chinese_chars)
    
    # 统计英文单词数
    english_words = ENGLISH_PATTERN.findall(text)
    english_count = len(english_words)
    
    # 计算总字词数（用于显示）
    total_tokens = chinese_count + english_count
    
    # 计算阅读时长（分钟）
    # 中文按300字/分钟，英文按200词/分钟
    minutes_from_chinese = chinese_count / 300
    minutes_from_english = english_count / 200
    minutes = max(1, round(minutes_from_chinese + minutes_from_english))
    
    return {
        "words": total_tokens,
        "minutes": minutes,
        "chinese": chinese_count,
        "english": english_count,
    }


def on_page_content(html: str, page: Page, config: MkDocsConfig, files):
    stats = _reading_stats(html)
    page.meta = page.meta or {}
    page.meta["stats_words"] = stats["words"]
    page.meta["stats_minutes"] = stats["minutes"]
    return html


def on_nav(nav: Navigation, config: MkDocsConfig, files):
    # Keep original nav titles untouched for a cleaner sidebar.
    return nav
