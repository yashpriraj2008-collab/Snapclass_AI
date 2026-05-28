def attendance_color(pct: float) -> str:
    if pct >= 75:
        return "ok"
    elif pct >= 60:
        return "warn"
    return "danger"

def attendance_label(pct: float) -> str:
    if pct >= 75:
        return "✅ Good"
    elif pct >= 60:
        return "⚠️ Low"
    return "🚨 Critical"

def badge_html(text: str, kind: str = "ok") -> str:
    return f"<span class='sc-badge {kind}'>{text}</span>"

def progress_bar_html(pct: float, color: str = "#5B6CFF") -> str:
    return f"""
    <div style="background:#E5E7EB;border-radius:999px;height:8px;margin-top:6px;">
      <div style="width:{pct}%;background:{color};border-radius:999px;height:8px;transition:width .4s ease;"></div>
    </div>"""
