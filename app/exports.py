"""History exports: a shareable PNG card and a real .xlsx workbook."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import theme as T
from .i18n import tr
from .library import plan_label


def summary(history: list[dict]) -> dict:
    total = sum(int(h.get("total_seconds", 0)) for h in history)
    poses = sum(int(h.get("poses", 0)) for h in history)
    return {
        "total": total,
        "sessions": len(history),
        "poses": poses,
        "average": total / len(history) if history else 0,
    }


def week_data(history: list[dict]) -> list[tuple]:
    today = datetime.now().date()
    days = {today - timedelta(days=i): 0 for i in range(6, -1, -1)}
    for item in history:
        try:
            day = datetime.fromisoformat(item.get("date", "")).astimezone().date()
        except (ValueError, TypeError):
            continue
        if day in days:
            days[day] += int(item.get("total_seconds", 0))
    keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    return [(day, secs, keys[day.weekday()]) for day, secs in sorted(days.items())]


def _font(size: int, bold: bool = False, serif: bool = False):
    names = []
    if serif:
        names = ["georgiab.ttf", "georgia.ttf"]
    elif bold:
        names = ["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"]
    else:
        names = ["segoeui.ttf", "arial.ttf"]
    for name in names:
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                pass
    return ImageFont.load_default()


def _plan_text(item: dict, lang: str) -> str:
    plan = item.get("plan") or []
    if item.get("mode") == "relaxed":
        return tr(lang, "history.free")
    return plan_label(plan, lang)


def export_png(path: str | Path, history: list[dict], lang: str = "es") -> None:
    s = summary(history)
    week = week_data(history)
    W, H = 1600, 1120
    img = Image.new("RGB", (W, H), T.CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 14), fill=T.ACCENT)
    d.text((80, 64), "Tpose", font=_font(64, serif=True), fill=T.INK)
    d.text((82, 142), tr(lang, "history.title"), font=_font(26, bold=True), fill=T.ACCENT)
    d.text((80, 184), tr(lang, "history.subtitle"), font=_font(18), fill=T.MUTED)
    d.text((W - 80, 88), datetime.now().strftime("%d/%m/%Y"), font=_font(18), fill=T.FAINT,
           anchor="ra")

    cards = [
        (T.fmt_total(s["total"], lang), tr(lang, "history.total_time")),
        (str(s["sessions"]), tr(lang, "history.sessions")),
        (str(s["poses"]), tr(lang, "history.poses")),
        (T.fmt_total(s["average"], lang), tr(lang, "history.average")),
    ]
    x = 80
    for i, (value, label) in enumerate(cards):
        w = 350 if i < 3 else 360
        d.rounded_rectangle((x, 238, x + w, 380), radius=14,
                            fill=T.SIDEBAR if i == 0 else T.CARD,
                            outline=T.SIDEBAR if i == 0 else T.LINE, width=1)
        d.text((x + 26, 264), value, font=_font(38, serif=True),
               fill=T.ACCENT if i == 0 else T.INK)
        d.text((x + 26, 332), label, font=_font(17),
               fill=T.SIDEBAR_MUTED if i == 0 else T.MUTED)
        x += w + 15

    d.text((80, 430), tr(lang, "history.week"), font=_font(24, bold=True), fill=T.INK)
    chart = (80, 478, W - 80, 710)
    d.rounded_rectangle(chart, radius=14, fill=T.CARD, outline=T.LINE, width=1)
    maxv = max([w[1] for w in week] + [1])
    base = chart[3] - 42
    slot = (chart[2] - chart[0] - 40) / 7
    for i, (day, secs, key) in enumerate(week):
        cx = chart[0] + 20 + slot * i + slot / 2
        bh = (base - chart[1] - 50) * secs / maxv if maxv else 0
        bw = 54
        if bh > 2:
            d.rounded_rectangle((cx - bw / 2, base - bh, cx + bw / 2, base), radius=7,
                                fill=T.ACCENT if day == datetime.now().date() else T.LINE_STRONG)
            d.text((cx, base - bh - 20), T.fmt_total(secs, lang), font=_font(15, bold=True),
                   fill=T.MUTED, anchor="ms")
        d.text((cx, base + 12), tr(lang, f"weekday.{key}"), font=_font(16, bold=True),
               fill=T.INK if day == datetime.now().date() else T.MUTED, anchor="ma")

    d.text((80, 742), tr(lang, "history.recent"), font=_font(24, bold=True), fill=T.INK)
    top = 786
    headers = [
        (80, tr(lang, "history.date")),
        (430, tr(lang, "history.plan")),
        (1120, tr(lang, "history.poses")),
        (1300, tr(lang, "history.total_time")),
    ]
    d.rectangle((80, top, W - 80, top + 40), fill=T.CREAM_DARK)
    for x, text in headers:
        d.text((x, top + 11), text, font=_font(15, bold=True), fill=T.MUTED)
    y = top + 40
    for i, item in enumerate(history[:5]):
        bg = T.CARD if i % 2 == 0 else "#F7F2E9"
        d.rectangle((80, y, W - 80, y + 38), fill=bg)
        d.text((92, y + 11), T.fmt_date(item.get("date", ""), lang), font=_font(15), fill=T.INK)
        d.text((430, y + 11), _plan_text(item, lang)[:42], font=_font(15), fill=T.MUTED)
        d.text((1120, y + 11), str(item.get("poses", 0)), font=_font(15), fill=T.INK)
        d.text((1300, y + 11), T.fmt_total(item.get("total_seconds", 0), lang), font=_font(15), fill=T.INK)
        status = tr(lang, "history.completed") if item.get("completed") else tr(lang, "history.interrupted")
        d.text((W - 94, y + 11), status, font=_font(14, bold=True),
               fill=T.GREEN if item.get("completed") else T.ACCENT_DARK, anchor="ra")
        y += 38
    if len(history) > 5:
        d.text((W - 94, y + 10), f"+ {len(history) - 5} …", font=_font(15), fill=T.FAINT, anchor="ra")

    d.text((80, H - 54), "Tpose  ·  uso libre / free to use  ·  Pchans y clued",
           font=_font(15), fill=T.FAINT)
    img.save(path, "PNG")


def export_xlsx(path: str | Path, history: list[dict], lang: str = "es") -> None:
    """Write a clear, styled and standards-compliant workbook."""
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo

    s = summary(history)
    week = week_data(history)
    summary_name = "Resumen" if lang == "es" else "Summary"
    sessions_name = "Sesiones" if lang == "es" else "Sessions"

    accent = "D65435"
    ink = "211C18"
    cream = "F3EDE3"
    card = "FBF8F2"
    muted = "7C6F63"
    soft = "FAEAE4"
    line = Side(style="thin", color="DDD0C0")
    border = Border(left=line, right=line, top=line, bottom=line)
    title_font = Font(name="Georgia", size=24, bold=True, color="FFFFFF")
    subtitle_font = Font(name="Calibri", size=11, color="FFFFFF")
    h1_font = Font(name="Calibri", size=13, bold=True, color=ink)
    h2_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Calibri", size=10, color=ink)
    muted_font = Font(name="Calibri", size=10, color=muted)
    big_font = Font(name="Georgia", size=15, bold=True, color=ink)
    header_fill = PatternFill("solid", fgColor=accent)
    soft_fill = PatternFill("solid", fgColor=soft)
    card_fill = PatternFill("solid", fgColor=card)
    stripe_fill = PatternFill("solid", fgColor="F7F2E9")

    wb = Workbook()
    ws = wb.active
    ws.title = summary_name
    ws.sheet_properties.tabColor = accent
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:G1")
    ws["A1"] = "Tpose"
    ws["A1"].font = title_font
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 42
    ws.merge_cells("A2:G2")
    ws["A2"] = tr(lang, "history.title")
    ws["A2"].font = subtitle_font
    ws["A2"].fill = header_fill
    ws["A2"].alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[2].height = 22
    ws["A3"] = tr(lang, "history.subtitle")
    ws["A3"].font = muted_font
    ws["G3"] = datetime.now().strftime("%d/%m/%Y")
    ws["G3"].font = muted_font
    ws["G3"].alignment = Alignment(horizontal="right")

    kpis = [
        (tr(lang, "history.total_time"), T.fmt_total(s["total"], lang), "C6EFCE"),
        (tr(lang, "history.sessions"), str(s["sessions"]), "DDEBF7"),
        (tr(lang, "history.poses"), str(s["poses"]), "FFF2CC"),
        (tr(lang, "history.average"), T.fmt_total(s["average"], lang), "FCE4D6"),
    ]
    for i, (label, value, color) in enumerate(kpis, 1):
        col = get_column_letter(i)
        c = ws[f"{col}5"]
        c.value = label
        c.font = h1_font
        c.fill = PatternFill("solid", fgColor=color)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border
        v = ws[f"{col}6"]
        v.value = value
        v.font = big_font
        v.fill = PatternFill("solid", fgColor=color)
        v.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        v.border = border
    ws.row_dimensions[6].height = 38

    ws["A8"] = tr(lang, "history.week")
    ws["A8"].font = h1_font
    week_headers = [tr(lang, "history.date"), tr(lang, "history.total_time")]
    for j, value in enumerate(week_headers, 1):
        c = ws.cell(row=9, column=j, value=value)
        c.font = h2_font
        c.fill = header_fill
        c.border = border
        c.alignment = Alignment(horizontal="center", vertical="center")
    for i, (day, secs, key) in enumerate(week, 10):
        ws.cell(row=i, column=1, value=day.strftime("%d/%m/%Y")).font = body_font
        ws.cell(row=i, column=2, value=secs).font = body_font
        ws.cell(row=i, column=2).number_format = '0 "s"'
        for col in (1, 2):
            c = ws.cell(row=i, column=col)
            c.border = border
            c.fill = stripe_fill if (i - 10) % 2 else card_fill

    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = tr(lang, "history.week")
    chart.y_axis.title = tr(lang, "history.total_time")
    chart.height = 7
    chart.width = 13
    data = Reference(ws, min_col=2, min_row=9, max_row=16)
    cats = Reference(ws, min_col=1, min_row=10, max_row=16)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.legend = None
    ws.add_chart(chart, "D8")
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 15
    for col in ("C", "D", "E", "F", "G"):
        ws.column_dimensions[col].width = 16
    ws.freeze_panes = "A8"

    ws2 = wb.create_sheet(sessions_name)
    ws2.sheet_properties.tabColor = "7C6F63"
    ws2.sheet_view.showGridLines = False
    headers2 = [
        tr(lang, "history.date"),
        "Modo" if lang == "es" else "Mode",
        tr(lang, "history.plan"),
        "Carpetas" if lang == "es" else "Folders",
        tr(lang, "history.poses"),
        "Tiempo (s)" if lang == "es" else "Time (s)",
        tr(lang, "history.total_time"),
        "Estado" if lang == "es" else "Status",
    ]
    for j, value in enumerate(headers2, 1):
        c = ws2.cell(row=1, column=j, value=value)
        c.font = h2_font
        c.fill = header_fill
        c.border = border
        c.alignment = Alignment(horizontal="center", vertical="center")
    for i, item in enumerate(history, 2):
        try:
            dt = datetime.fromisoformat(item.get("date", "")).replace(tzinfo=None)
        except (ValueError, TypeError):
            dt = None
        values = [
            dt,
            tr(lang, "history.mode_timed" if item.get("mode") == "timed" else "history.mode_relaxed"),
            _plan_text(item, lang),
            ", ".join(item.get("folders") or []),
            int(item.get("poses", 0)),
            int(item.get("total_seconds", 0)),
            T.fmt_total(item.get("total_seconds", 0), lang),
            tr(lang, "history.completed") if item.get("completed") else tr(lang, "history.interrupted"),
        ]
        for j, value in enumerate(values, 1):
            c = ws2.cell(row=i, column=j, value=value)
            c.font = body_font
            c.border = border
            c.alignment = Alignment(vertical="center", wrap_text=(j in (3, 4)))
            if (i - 2) % 2:
                c.fill = stripe_fill
        if dt is not None:
            ws2.cell(row=i, column=1).number_format = "dd/mm/yyyy hh:mm"
        ws2.cell(row=i, column=6).number_format = "0"

    widths2 = [22, 15, 38, 32, 11, 13, 17, 16]
    for i, width in enumerate(widths2, 1):
        ws2.column_dimensions[get_column_letter(i)].width = width
    ws2.row_dimensions[1].height = 26
    ws2.freeze_panes = "A2"
    if history:
        table = Table(displayName="TposeSesiones", ref=f"A1:H{len(history) + 1}")
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
            showRowStripes=True, showColumnStripes=False,
        )
        ws2.add_table(table)

    wb.properties.creator = "Tpose"
    wb.properties.title = "Tpose - " + tr(lang, "history.title")
    wb.save(path)
