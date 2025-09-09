#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv, datetime as dt, os
from collections import defaultdict

# ========= 配置 =========
DATA_PATH = "data/work.csv"
SVG_PATH  = "work-stats.svg"

WEEKS = 53
ROWS  = 7
CELL  = 11      # 与 GitHub 更接近
GAP   = 2

# 留白（含左侧星期标签空间）
PADDING_LEFT  = 34
PADDING_TOP   = 34     # 给月份标签留空间
LEGEND_HEIGHT = 40

# 显示控制
SHOW_TITLES          = False   # 不在 SVG 里画标题（避免与 README 冲突）
SHOW_WEEKDAY_LABELS  = True    # 显示 Mon/Wed/Fri
SHOW_LEGEND          = True

FONT = 'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,\'Noto Sans\',sans-serif"'

# 蓝色梯度（第一个是 0h 的灰）
PALETTE = ["#ebedf0","#c6dbef","#9ecae1","#6baed6","#3182bd","#08519c"]

def bucket_color(h: float) -> str:
    if h <= 2: return PALETTE[0]
    if h <= 4: return PALETTE[1]
    if h <= 6: return PALETTE[2]
    if h <= 8: return PALETTE[3]
    if h <= 10: return PALETTE[4]
    return PALETTE[5]

def load_hours(path: str) -> dict:
    hours = defaultdict(float)
    if not os.path.exists(path): return hours
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                d = dt.date.fromisoformat(row["date"].strip())
                h = float(row["hours"])
                hours[d] += h
            except Exception:
                pass
    return hours

def start_sunday(today: dt.date):
    # 右侧对齐最近周六；回溯 53 周；起点调到周日（GitHub 布局）
    offset_to_sat = (5 - today.weekday()) % 7  # Mon=0..Sat=5
    end = today + dt.timedelta(days=offset_to_sat)
    start = end - dt.timedelta(weeks=WEEKS - 1, days=6)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # to Sunday
    return start, end

def render_svg(hours_map: dict):
    today = dt.date.today()
    start, end = start_sunday(today)

    width  = PADDING_LEFT + WEEKS * (CELL + GAP) + 8
    height = PADDING_TOP  + ROWS  * (CELL + GAP) + (LEGEND_HEIGHT if SHOW_LEGEND else 8)

    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
             f'xmlns="http://www.w3.org/2000/svg" role="img" '
             f'preserveAspectRatio="xMinYMin meet">']

    # （可选）标题：默认关闭
    if SHOW_TITLES:
        now_utc = dt.datetime.utcnow(); bj = now_utc + dt.timedelta(hours=8)
        parts.append(f'<text x="0" y="16" font-size="15" font-weight="bold" {FONT}>My Work Hours Wall</text>')
        parts.append(f'<text x="0" y="30" font-size="12" {FONT}>Updated (Beijing): {bj.date()}</text>')

    # 月份标签：仅在月份变化且与上次标注列距≥3时标注，避免拥挤
    month_labels, last_col = [], -999
    d = start; prev_month = None
    for c in range(WEEKS):
        month_first = d.replace(day=1)
        this_month = (month_first.year, month_first.month)
        if this_month != prev_month and (c - last_col) >= 3:
            x = PADDING_LEFT + c * (CELL + GAP)
            label = month_first.strftime("%b")
            month_labels.append(f'<text x="{x}" y="{PADDING_TOP-10}" font-size="10" {FONT}>{label}</text>')
            last_col = c
        prev_month = this_month
        d += dt.timedelta(days=7)
    parts += month_labels

    # 方格
    d = start; col = 0
    while d <= end:
        for row in range(ROWS):
            curr = d + dt.timedelta(days=row)
            if curr > end: break
            x = PADDING_LEFT + col * (CELL + GAP)
            y = PADDING_TOP  + row * (CELL + GAP)
            h = hours_map.get(curr, 0.0)
            color = bucket_color(h)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{color}">'
                f'<title>{curr.isoformat()}: {h:.2f}h</title></rect>'
            )
        d += dt.timedelta(days=7); col += 1

    # 星期标签（Mon / Wed / Fri）
    if SHOW_WEEKDAY_LABELS:
        weekdays = {0: "Mon", 2: "Wed", 4: "Fri", 6: "Sun"}  # Mon=0
        for r, name in weekdays.items():
            y = PADDING_TOP + r * (CELL + GAP) + 8
            parts.append(f'<text x="4" y="{y}" font-size="10" {FONT}>{name}</text>')

    # 图例
    if SHOW_LEGEND:
        legend_x = PADDING_LEFT
        legend_y = PADDING_TOP + ROWS * (CELL + GAP) + 18
        for i, col_hex in enumerate(PALETTE):
            parts.append(
                f'<rect x="{legend_x + i*(CELL+4)}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{col_hex}"/>'
            )
        legend_text = (
            f'<text x="{legend_x + len(PALETTE)*(CELL+4) + 5}" y="{legend_y+9}" font-size="10" {FONT}>'
            f'0-2, 2–4, 4–6, 6–8, 8-10, >10 h</text>'
        )
        parts.append(legend_text)

    parts.append('</svg>')

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write("".join(parts))

def main():
    hours_map = load_hours(DATA_PATH)
    render_svg(hours_map)

if __name__ == "__main__":
    main()
