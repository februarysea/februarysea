#!/usr/bin/env python3
import csv, datetime as dt, math, os
from collections import defaultdict

# 配置
DATA_PATH = "data/work.csv"
SVG_PATH = "work-stats.svg"
TITLE = "Daily Work Hours (past 53 weeks)"
# GitHub 绿块配色：0 无数据/0小时；后面按强度递增
PALETTE = [
    "#ebedf0",  # 0-2
    "#9be9a8",  # 2-4
    "#40c463",  # 4-6
    "#30a14e",  # 6-8
    "#216e39",  # 8-10
    "#0e4429",  # >10
]

CELL = 11      # 单格大小
GAP  = 2       # 单格间距
WEEKS = 53     # 列数
ROWS  = 7      # 周日到周六

PADDING_LEFT = 35
PADDING_TOP  = 25
LEGEND_HEIGHT = 40
WIDTH = PADDING_LEFT + WEEKS * (CELL + GAP) + 10
HEIGHT = PADDING_TOP + ROWS * (CELL + GAP) + LEGEND_HEIGHT

def bucket_color(h):
    if h <= 0: return PALETTE[0]
    if h <= 2: return PALETTE[1]
    if h <= 4: return PALETTE[2]
    if h <= 6: return PALETTE[3]
    if h <= 8: return PALETTE[4]
    return PALETTE[5]

def load_hours(path):
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
                pass
    return hours

def start_sunday(today):
    # 以今天为终点，生成过去 53 周；GitHub 是按“周列”显示，列从周日开始
    # 找到最近的周六（列的最后一天），再回推 52 周
    # 先找到今天所在周的周六
    offset_to_sat = (5 - today.weekday()) % 7  # Mon=0..Sun=6; Sat=5
    end = today + dt.timedelta(days=offset_to_sat)
    start = end - dt.timedelta(weeks=WEEKS-1, days=6)  # 53周 * 7天
    # 将 start 调整到周日
    start -= dt.timedelta(days=(start.weekday()+1) % 7)  # Sun=6 -> 0偏移
    return start, end

def render_svg(hours_map):
    today = dt.date.today()
    start, end = start_sunday(today)

    # 生成所有日期格子
    rects = []
    d = start
    col = 0
    while d <= end:
        for row in range(ROWS):
            curr = d + dt.timedelta(days=row)
            if curr > end:
                break
            x = PADDING_LEFT + col * (CELL + GAP)
            y = PADDING_TOP + row * (CELL + GAP)
            h = hours_map.get(curr, 0.0)
            color = bucket_color(h)
            tooltip = f"{curr.isoformat()}: {h:.2f}h"
            rects.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{color}">'
                f'<title>{tooltip}</title></rect>'
            )
        d += dt.timedelta(days=7)
        col += 1

    # 月份标签（简化，按每月第一天落在哪一列来标）
    month_labels = []
    seen_months = set()
    d = start
    for c in range(WEEKS):
        month_first = (d.replace(day=1))
        mkey = (month_first.year, month_first.month)
        if mkey not in seen_months:
            seen_months.add(mkey)
            x = PADDING_LEFT + c * (CELL + GAP)
            label = month_first.strftime("%b")
            month_labels.append(f'<text x="{x}" y="{PADDING_TOP-7}" font-size="10">{label}</text>')
        d += dt.timedelta(days=7)

    # 周几标签（可选：只标周一/周三/周五，避免拥挤）
    weekday_labels = []
    weekdays = {0:"Mon", 2:"Wed", 4:"Fri"}
    for r in weekdays:
        y = PADDING_TOP + r * (CELL + GAP) + 8
        weekday_labels.append(f'<text x="0" y="{y}" font-size="10">{weekdays[r]}</text>')

    # 图例
    legend_items = []
    legend_x = PADDING_LEFT
    legend_y = PADDING_TOP + ROWS * (CELL + GAP) + 18
    for i, col_hex in enumerate(PALETTE):
        legend_items.append(
            f'<rect x="{legend_x + i*(CELL+4)}" y="{legend_y}" width="{CELL}" height="{CELL}" fill="{col_hex}"/>'
        )
    legend_text = (
        f'<text x="{legend_x + len(PALETTE)*(CELL+4) + 5}" y="{legend_y+9}" font-size="10">'
        f'0, 0-2, 2-4, 4-6, 6-8, >8 h</text>'
    )

    title = f'<text x="0" y="14" font-size="14" font-weight="bold">{TITLE}</text>'

    svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{TITLE}">
{title}
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
