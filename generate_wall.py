#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import datetime as dt
import math
import os
from collections import defaultdict

# ========= 基本配置 =========
DATA_PATH = "data/work.csv"     # 你的数据文件
SVG_PATH  = "work-stats.svg"    # 输出 SVG
WEEKS     = 53                  # 显示过去 53 周
ROWS      = 7                   # 一周 7 天
CELL      = 10                  # 单格尺寸（像素）
GAP       = 2                   # 单格间距（像素）

# 左右上下留白 & 图例高度
PADDING_LEFT  = 42
PADDING_TOP   = 40
LEGEND_HEIGHT = 48

# 字体（尽量贴近 GitHub）
FONT = 'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,\'Noto Sans\',sans-serif"'

# 蓝色梯度（浅→深），第一个为无数据/0h 的灰色
PALETTE = [
    "#ebedf0",  # 0h
    "#c6dbef",  # 0-2h
    "#9ecae1",  # 2-4h
    "#6baed6",  # 4-6h
    "#3182bd",  # 6-8h
    "#08519c",  # >8h
]

# 计算画布宽高
WIDTH  = PADDING_LEFT + WEEKS * (CELL + GAP) + 10
HEIGHT = PADDING_TOP  + ROWS  * (CELL + GAP) + LEGEND_HEIGHT


def bucket_color(h: float) -> str:
    if h <= 0: return PALETTE[0]
    if h <= 2: return PALETTE[1]
    if h <= 4: return PALETTE[2]
    if h <= 6: return PALETTE[3]
    if h <= 8: return PALETTE[4]
    return PALETTE[5]


def load_hours(path: str) -> dict:
    """读取 CSV: date,hours -> {date: total_hours}"""
    hours = defaultdict(float)
    if not os.path.exists(path):
        return hours
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                d = dt.date.fromisoformat(row["date"].strip())
                h = float(row["hours"])
                hours[d] += h
            except Exception:
                # 忽略坏行
                pass
    return hours


def start_sunday(today: dt.date):
    """
    让网格的最右一列对齐到最近的【周六】，
    然后向前回溯到覆盖 53 周（含 7*53 天）。
    再把起点对齐到周日，以符合 GitHub 贡献墙布局。
    """
    # Mon=0 ... Sat=5, Sun=6
    offset_to_sat = (5 - today.weekday()) % 7
    end = today + dt.timedelta(days=offset_to_sat)
    start = end - dt.timedelta(weeks=WEEKS - 1, days=6)
    # 将 start 调整到周日（Sun=6）
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    return start, end


def render_svg(hours_map: dict):
    today = dt.date.today()
    start, end = start_sunday(today)

    # 主/副标题（副标题显示北京时间更新日期）
    now_utc = dt.datetime.utcnow()
    beijing = now_utc + dt.timedelta(hours=8)
    title_main = f'<text x="0" y="18" font-size="16" font-weight="bold" {FONT}>My Work Hours Wall</text>'
    title_sub  = f'<text x="0" y="34" font-size="13" {FONT}>Daily Work Hours (past 53 weeks) · Updated (Beijing): {beijing.date().isoformat()}</text>'

    # 绘制方格（按列=周、行=周日到周六）
    rects = []
    d = start
    col = 0
    while d <= end:
        for row in range(ROWS):
            curr = d + dt.timedelta(days=row)
            if curr > end:
                break
            x = PADDING_LEFT + col * (CELL + GAP)
            y = PADDING_TOP  + row * (CELL + GAP)
            h = hours_map.get(curr, 0.0)
            color = bucket_color(h)
            tooltip = f"{curr.isoformat()}: {h:.2f}h"
            rects.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{color}">'
                f'<title>{tooltip}</title></rect>'
            )
        d += dt.timedelta(days=7)
        col += 1

    # 月份标签：只在“月份变化”且距离上一个标签至少 3 列时标注，避免拥挤
    month_labels = []
    last_label_col = -999
    d = start
    prev_month = None
    for c in range(WEEKS):
        month_first = d.replace(day=1)
        this_month = (month_first.year, month_first.month)
        if this_month != prev_month and (c - last_label_col) >= 3:
            x = PADDING_LEFT + c * (CELL + GAP)
            label = month_first.strftime("%b")
            month_labels.append(f'<text x="{x}" y="{PADDING_TOP-10}" font-size="10" {FONT}>{label}</text>')
            last_label_col = c
        prev_month = this_month
        d += dt.timedelta(days=7)

    # 星期标签（只标 Mon / Wed / Fri，贴近 GitHub）
    weekday_labels = []
    weekdays = {0: "Mon", 2: "Wed", 4: "Fri"}  # Mon=0
    for r, name in weekdays.items():
        y = PADDING_TOP + r * (CELL + GAP) + 8
        weekday_labels.append(f'<text x="0" y="{y}" font-size="10" {FONT}>{name}</text>')

    # 图例
    legend_items = []
    legend_x = PADDING_LEFT
    legend_y = PADDING_TOP + ROWS * (CELL + GAP) + 18
    for i, col_hex in enumerate(PALETTE):
        legend_items.append(
            f'<rect x="{legend_x + i*(CELL+4)}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{col_hex}"/>'
        )
    legend_text = (
        f'<text x="{legend_x + len(PALETTE)*(CELL+4) + 5}" y="{legend_y+9}" font-size="10" {FONT}>'
        f'0, 0–2, 2–4, 4–6, 6–8, >8 h</text>'
    )

    svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}"
  xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Daily Work Hours (past 53 weeks)">
{title_main}
{title_sub}
{''.join(month_labels)}
{''.join(weekday_labels)}
{''.join(rects)}
{''.join(legend_items)}
{legend_text}
</svg>'''

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    hours_map = load_hours(DATA_PATH)
    render_svg(hours_map)


if __name__ == "__main__":
    main()
