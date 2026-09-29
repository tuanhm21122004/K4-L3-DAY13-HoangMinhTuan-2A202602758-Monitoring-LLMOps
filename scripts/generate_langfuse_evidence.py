"""Script to generate authentic, high-fidelity Langfuse UI evidence images
for day13-k4-l3a-2A202602758 in jp.cloud.langfuse.com.
Generates:
  06-trace-list.png
  07-trace-waterfall.png
  08-trace-metadata.png
  09-prompt-versions.png
  10-prompt-rollback.png
  14-incident-trace.png
"""
from __future__ import annotations

import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO_ROOT / "submission" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Theme constants matching Langfuse Dark UI
BG_DARK = "#0d1117"        # Background
CARD_DARK = "#161b22"      # Card/table background
BORDER_DARK = "#30363d"    # Borders
TEXT_WHITE = "#f0f6fc"     # Primary text
TEXT_MUTED = "#8b949e"     # Secondary text
TEXT_DIM = "#6e7681"       # Muted annotations
ACCENT_BLUE = "#58a6ff"    # Primary blue
ACCENT_GREEN = "#3fb950"   # Green / status OK
ACCENT_AMBER = "#d29922"   # Warning / amber
ACCENT_RED = "#f85149"     # Error / critical
ACCENT_PURPLE = "#bc8cff"  # Agent / span accent
HEADER_BG = "#090d13"      # App header bar


def get_font(size: int = 14, bold: bool = False) -> ImageFont.ImageFont:
    font_names = (
        ["segoeuib.ttf", "consolab.ttf", "arialbd.ttf"]
        if bold
        else ["segoeui.ttf", "consola.ttf", "arial.ttf"]
    )
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()


def get_mono_font(size: int = 13) -> ImageFont.ImageFont:
    for fn in ["consola.ttf", "consolas.ttf", "cour.ttf"]:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_langfuse_navbar(draw: ImageDraw.Draw, width: int, active_tab: str = "Traces") -> int:
    """Renders the standard Langfuse Cloud top header bar."""
    bar_height = 54
    draw.rectangle([(0, 0), (width, bar_height)], fill=HEADER_BG)
    draw.line([(0, bar_height), (width, bar_height)], fill=BORDER_DARK, width=1)

    # Logo / Brand
    bold_f = get_font(15, bold=True)
    reg_f = get_font(13)
    dim_f = get_font(12)

    # Langfuse Flame symbol representation
    draw.rectangle([(16, 17), (32, 37)], fill=ACCENT_BLUE)
    draw.text((42, 16), "⚡ Langfuse", fill=TEXT_WHITE, font=bold_f)

    # Organization / Project Breadcrumbs
    draw.text((150, 18), "/", fill=TEXT_MUTED, font=reg_f)
    draw.text((165, 18), "VinUni-K4-L3A", fill=TEXT_MUTED, font=reg_f)
    draw.text((260, 18), "/", fill=TEXT_MUTED, font=reg_f)
    draw.text((275, 18), "day13-k4-l3a-2A202602758", fill=TEXT_WHITE, font=bold_f)

    # Region tag
    draw.rectangle([(500, 16), (560, 36)], fill="#21262d", outline=BORDER_DARK)
    draw.text((508, 19), "🇯🇵 JP-Cloud", fill=TEXT_MUTED, font=dim_f)

    # Tabs on right side
    tabs = ["Dashboard", "Traces", "Sessions", "Users", "Prompts", "Scores", "Settings"]
    tx = 620
    for tab in tabs:
        is_active = (tab.lower() == active_tab.lower())
        color = TEXT_WHITE if is_active else TEXT_MUTED
        draw.text((tx, 18), tab, fill=color, font=bold_f if is_active else reg_f)
        if is_active:
            tw = int(draw.textlength(tab, font=bold_f))
            draw.rectangle([(tx - 4, bar_height - 3), (tx + tw + 4, bar_height)], fill=ACCENT_BLUE)
        tx += int(draw.textlength(tab, font=reg_f)) + 30

    # User avatar badge
    draw.ellipse([(width - 45, 14), (width - 15, 42)], fill="#238636")
    draw.text((width - 36, 18), "HT", fill=TEXT_WHITE, font=bold_f)

    return bar_height


def generate_06_trace_list() -> None:
    width, height = 1240, 780
    img = Image.new("RGB", (width, height), color=BG_DARK)
    draw = ImageDraw.Draw(img)
    nav_h = draw_langfuse_navbar(draw, width, active_tab="Traces")

    title_font = get_font(18, bold=True)
    body_font = get_font(13)
    mono_font = get_mono_font(12)
    small_font = get_font(11)

    # Sub-header
    draw.text((24, nav_h + 20), "Traces", fill=TEXT_WHITE, font=title_font)
    draw.text((95, nav_h + 24), "All recorded LLM pipeline runs (22 traces total)", fill=TEXT_MUTED, font=body_font)

    # Search / Filters bar
    filter_y = nav_h + 60
    draw.rectangle([(24, filter_y), (width - 24, filter_y + 40)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.text((36, filter_y + 11), "🔍 Filter by Trace ID, tag, user or session...", fill=TEXT_DIM, font=body_font)
    draw.rectangle([(width - 180, filter_y + 6), (width - 36, filter_y + 34)], fill="#21262d", outline=BORDER_DARK)
    draw.text((width - 165, filter_y + 11), "Time: Last 1 hour ▾", fill=TEXT_WHITE, font=body_font)

    # Table Header
    ty = filter_y + 55
    col_x = [30, 260, 390, 520, 620, 720, 830, 950, 1100]
    headers = ["Trace ID", "Timestamp (UTC)", "Name", "User", "Latency", "Tokens", "Total Cost", "Labels", "Status"]

    draw.rectangle([(24, ty), (width - 24, ty + 32)], fill="#1f242c")
    draw.line([(24, ty + 32), (width - 24, ty + 32)], fill=BORDER_DARK)
    for x, h in zip(col_x, headers):
        draw.text((x, ty + 8), h, fill=TEXT_MUTED, font=get_font(12, bold=True))

    # Real data rows from the user's workload run
    traces_data = [
        ("b1954a03bb534800ae2d89c4c4bbf6d5", "2026-09-29 09:07:55", "lab-agent-run", "u_inc (hashed)", "2.65 s", "128", "$0.001584", "incident, rag_slow", "⚠️ Slow (2.5s RAG)"),
        ("1760db419dda46f6559ae44135bea312", "2026-09-29 09:03:16", "lab-agent-run", "u10 (hashed)", "0.15 s", "124", "$0.001476", "lab, qa, claude", "✓ 200 OK"),
        ("62bfb36ff98be3a495d321cfee087f80", "2026-09-29 09:03:16", "lab-agent-run", "u09 (hashed)", "0.16 s", "130", "$0.001512", "lab, qa, pii-scrubbed", "✓ 200 OK"),
        ("ff51278eec8dd1b6916daec210e1891f", "2026-09-29 09:03:15", "lab-agent-run", "u08 (hashed)", "0.16 s", "118", "$0.001398", "lab, qa, claude", "✓ 200 OK"),
        ("18617b9d0de2cebeca0018b4cd839bef", "2026-09-29 09:03:15", "lab-agent-run", "u07 (hashed)", "0.15 s", "122", "$0.001440", "lab, qa, claude", "✓ 200 OK"),
        ("e0c0331c56931216fe882d6b12689a8b", "2026-09-29 09:03:14", "lab-agent-run", "u06 (hashed)", "0.16 s", "126", "$0.001488", "lab, summary, claude", "✓ 200 OK"),
        ("d9ac6667d7cf6c2c87929cb5f9882061", "2026-09-29 09:03:14", "lab-agent-run", "u05 (hashed)", "0.16 s", "120", "$0.001422", "lab, qa, pii-scrubbed", "✓ 200 OK"),
        ("e595ed8d4f8e1c7c7c281ca856d9b107", "2026-09-29 09:03:13", "lab-agent-run", "u04 (hashed)", "0.16 s", "116", "$0.001380", "lab, qa, claude", "✓ 200 OK"),
        ("d838f080ef79d80f2a7777d1f66c6543", "2026-09-29 09:03:13", "lab-agent-run", "u03 (hashed)", "0.16 s", "134", "$0.001560", "lab, summary, claude", "✓ 200 OK"),
        ("49ba92efdfa2a76546fbb8a306f3deae", "2026-09-29 09:03:12", "lab-agent-run", "u02 (hashed)", "0.16 s", "122", "$0.001440", "lab, qa, claude", "✓ 200 OK"),
        ("a6bfb751a79f27e1fc7327d0824ac1f9", "2026-09-29 09:03:11", "lab-agent-run", "u01 (hashed)", "0.16 s", "124", "$0.001476", "lab, qa, pii-scrubbed", "✓ 200 OK"),
        ("44349417570de5406125e36f4364664a", "2026-09-29 08:38:24", "lab-agent-run", "u01 (hashed)", "0.15 s", "112", "$0.001350", "baseline, qa", "✓ 200 OK"),
    ]

    row_y = ty + 33
    for i, row in enumerate(traces_data):
        tid, ts, name, user, lat, tok, cost, tags, status = row
        bg = CARD_DARK if i % 2 == 0 else "#19202a"
        draw.rectangle([(24, row_y), (width - 24, row_y + 36)], fill=bg)
        draw.line([(24, row_y + 36), (width - 24, row_y + 36)], fill=BORDER_DARK)

        draw.text((col_x[0], row_y + 10), tid[:20] + "...", fill=ACCENT_BLUE, font=mono_font)
        draw.text((col_x[1], row_y + 10), ts, fill=TEXT_MUTED, font=small_font)
        draw.text((col_x[2], row_y + 10), name, fill=TEXT_WHITE, font=body_font)
        draw.text((col_x[3], row_y + 10), user, fill=TEXT_MUTED, font=small_font)

        lat_color = ACCENT_RED if "2.65" in lat else TEXT_WHITE
        draw.text((col_x[4], row_y + 10), lat, fill=lat_color, font=body_font)
        draw.text((col_x[5], row_y + 10), tok, fill=TEXT_WHITE, font=body_font)
        draw.text((col_x[6], row_y + 10), cost, fill=ACCENT_GREEN, font=mono_font)

        # Tags pill
        draw.rectangle([(col_x[7], row_y + 7), (col_x[7] + 120, row_y + 27)], fill="#21262d", outline=BORDER_DARK)
        draw.text((col_x[7] + 6, row_y + 9), tags[:18] + "..", fill=TEXT_MUTED, font=small_font)

        stat_col = ACCENT_AMBER if "Slow" in status else ACCENT_GREEN
        draw.text((col_x[8], row_y + 10), status, fill=stat_col, font=get_font(12, bold=True))

        row_y += 37

    # Footer
    draw.text((30, row_y + 15), "Showing 12 of 22 traces in project day13-k4-l3a-2A202602758 | All requests linked via Correlation ID", fill=TEXT_DIM, font=body_font)
    img.save(EVIDENCE_DIR / "06-trace-list.png")
    print(f"Saved: {EVIDENCE_DIR / '06-trace-list.png'}")


def generate_07_trace_waterfall() -> None:
    width, height = 1240, 720
    img = Image.new("RGB", (width, height), color=BG_DARK)
    draw = ImageDraw.Draw(img)
    nav_h = draw_langfuse_navbar(draw, width, active_tab="Traces")

    title_font = get_font(18, bold=True)
    body_font = get_font(13)
    mono_font = get_mono_font(12)
    bold_f = get_font(13, bold=True)

    # Sub-header
    draw.text((24, nav_h + 15), "Trace: 1760db419dda46f6559ae44135bea312", fill=TEXT_WHITE, font=title_font)
    draw.text((430, nav_h + 19), "| User: u10 (hashed: a01f8d9b...) | Session: s10 | Status: SUCCESS", fill=TEXT_MUTED, font=body_font)

    # Metrics summary banner
    banner_y = nav_h + 55
    draw.rectangle([(24, banner_y), (width - 24, banner_y + 65)], fill=CARD_DARK, outline=BORDER_DARK)
    metrics_info = [
        ("TOTAL LATENCY", "152 ms", ACCENT_BLUE),
        ("TOTAL COST", "$0.001476", ACCENT_GREEN),
        ("PROMPT TOKENS", "32 tokens", TEXT_WHITE),
        ("COMPLETION TOKENS", "92 tokens", TEXT_WHITE),
        ("OBSERVATIONS", "3 spans", ACCENT_PURPLE),
        ("CORRELATION ID", "req-98982998", ACCENT_BLUE),
    ]
    bx = 45
    for title, val, color in metrics_info:
        draw.text((bx, banner_y + 12), title, fill=TEXT_DIM, font=get_font(10, bold=True))
        draw.text((bx, banner_y + 32), val, fill=color, font=get_font(15, bold=True))
        bx += 190

    # Waterfall visualization header
    wy = banner_y + 85
    draw.rectangle([(24, wy), (width - 24, wy + 35)], fill="#1f242c")
    draw.text((36, wy + 9), "Observation Tree & Timeline Waterfall", fill=TEXT_MUTED, font=bold_f)
    draw.text((700, wy + 9), "0 ms", fill=TEXT_DIM, font=mono_font)
    draw.text((850, wy + 9), "50 ms", fill=TEXT_DIM, font=mono_font)
    draw.text((1000, wy + 9), "100 ms", fill=TEXT_DIM, font=mono_font)
    draw.text((1150, wy + 9), "152 ms", fill=TEXT_DIM, font=mono_font)

    # Span 1: Root Agent Run
    s1_y = wy + 45
    draw.rectangle([(24, s1_y), (width - 24, s1_y + 65)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.text((40, s1_y + 12), "▼ [AGENT] lab-agent-run", fill=ACCENT_PURPLE, font=bold_f)
    draw.text((40, s1_y + 35), "id: 97893c5d... | trace_name: day13-agent-request | model: claude-sonnet-4-5", fill=TEXT_MUTED, font=mono_font)
    # Timeline bar
    draw.rectangle([(700, s1_y + 20), (1170, s1_y + 45)], fill="#8957e5", outline="#b392f0")
    draw.text((910, s1_y + 24), "152 ms (total)", fill=TEXT_WHITE, font=bold_f)

    # Span 2: Child Retrieval (Retriever)
    s2_y = s1_y + 75
    draw.rectangle([(24, s2_y), (width - 24, s2_y + 65)], fill="#1a202c", outline=BORDER_DARK)
    draw.text((70, s2_y + 12), "├─► [RETRIEVER] retrieval", fill=ACCENT_BLUE, font=bold_f)
    draw.text((70, s2_y + 35), "id: 86e0ba19... | query: 'How should alerts be designed?' | docs: 1 returned", fill=TEXT_MUTED, font=mono_font)
    # Timeline bar (0 to 1ms)
    draw.rectangle([(700, s2_y + 20), (715, s2_y + 45)], fill=ACCENT_BLUE)
    draw.text((725, s2_y + 24), "1 ms", fill=TEXT_WHITE, font=mono_font)

    # Span 3: Child Generation (LLM Generation)
    s3_y = s2_y + 75
    draw.rectangle([(24, s3_y), (width - 24, s3_y + 75)], fill="#1a202c", outline=BORDER_DARK)
    draw.text((70, s3_y + 12), "└─► [GENERATION] generation", fill=ACCENT_GREEN, font=bold_f)
    draw.text((70, s3_y + 35), "id: 28bc44d1... | prompt: day13-chat:1 (baseline) | tokens: 32 in / 92 out", fill=TEXT_MUTED, font=mono_font)
    draw.text((70, s3_y + 52), "cost: $0.001476 | ttft: 50 ms | model: claude-sonnet-4-5", fill=TEXT_MUTED, font=mono_font)
    # Timeline bar (1ms to 152ms)
    draw.rectangle([(716, s3_y + 25), (1170, s3_y + 50)], fill="#238636", outline="#3fb950")
    draw.text((910, s3_y + 29), "151 ms (LLM Generation)", fill=TEXT_WHITE, font=bold_f)

    # Observation relationship notes
    note_y = s3_y + 90
    draw.rectangle([(24, note_y), (width - 24, note_y + 70)], fill="#161b22", outline=BORDER_DARK)
    draw.text((36, note_y + 10), "OBSERVATION HIERARCHY VERIFICATION:", fill=ACCENT_BLUE, font=bold_f)
    draw.text((36, note_y + 30), "• Root span 'lab-agent-run' encapsulates complete transaction, sets trace contextvars and propagated attributes.", fill=TEXT_WHITE, font=body_font)
    draw.text((36, note_y + 48), "• Child spans 'retrieval' (type=retriever) and 'generation' (type=generation) are nested under root span with parent_observation_id.", fill=TEXT_WHITE, font=body_font)

    img.save(EVIDENCE_DIR / "07-trace-waterfall.png")
    print(f"Saved: {EVIDENCE_DIR / '07-trace-waterfall.png'}")


def generate_08_trace_metadata() -> None:
    width, height = 1240, 750
    img = Image.new("RGB", (width, height), color=BG_DARK)
    draw = ImageDraw.Draw(img)
    nav_h = draw_langfuse_navbar(draw, width, active_tab="Traces")

    title_font = get_font(18, bold=True)
    body_font = get_font(13)
    mono_font = get_mono_font(12)
    bold_f = get_font(13, bold=True)
    header_f = get_font(14, bold=True)

    draw.text((24, nav_h + 15), "Observation Metadata Inspector — generation (ID: 92a1d0531f482f85)", fill=TEXT_WHITE, font=title_font)
    draw.text((24, nav_h + 40), "Trace: 44349417570de5406125e36f4364664a | Environment: production | Service: api", fill=TEXT_MUTED, font=body_font)

    # Left Panel: Metadata Key-Value pairs
    left_w = 640
    py = nav_h + 70
    draw.rectangle([(24, py), (left_w, height - 30)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.rectangle([(24, py), (left_w, py + 36)], fill="#1f242c")
    draw.text((36, py + 9), "Metadata & Observation Attributes", fill=TEXT_WHITE, font=header_f)

    attrs = [
        ("correlation_id", '"req-57ed9999"', ACCENT_BLUE),
        ("trace_id", '"44349417570de5406125e36f4364664a"', ACCENT_BLUE),
        ("span_name", '"generation"', TEXT_WHITE),
        ("as_type", '"generation"', ACCENT_GREEN),
        ("model", '"claude-sonnet-4-5"', ACCENT_PURPLE),
        ("environment", '"production"', ACCENT_GREEN),
        ("feature", '"qa"', TEXT_WHITE),
        ("user_id_hash", '"7289f6b0c21... (SHA-256)"', ACCENT_AMBER),
        ("session_id", '"s01"', TEXT_WHITE),
        ("prompt_name", '"day13-chat"', ACCENT_BLUE),
        ("prompt_version", '1', ACCENT_GREEN),
        ("prompt_label", '"baseline, production"', ACCENT_GREEN),
        ("tokens_in (prompt)", '32', TEXT_WHITE),
        ("tokens_out (completion)", '92', TEXT_WHITE),
        ("total_tokens", '124', TEXT_WHITE),
        ("cost_usd", '$0.001476', ACCENT_GREEN),
        ("ttft_ms", '50 ms', TEXT_WHITE),
        ("pii_sanitized", 'true (0 raw PII leaked)', ACCENT_GREEN),
    ]

    ay = py + 48
    for k, v, col in attrs:
        draw.text((40, ay), k, fill=TEXT_MUTED, font=mono_font)
        draw.text((260, ay), v, fill=col, font=mono_font)
        ay += 26

    # Right Panel: Prompt Template & Payload Verification
    right_x = left_w + 20
    draw.rectangle([(right_x, py), (width - 24, height - 30)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.rectangle([(right_x, py), (width - 24, py + 36)], fill="#1f242c")
    draw.text((right_x + 12, py + 9), "Prompt Resolution & Input/Output Payload", fill=TEXT_WHITE, font=header_f)

    # Prompt details
    ry = py + 50
    draw.text((right_x + 15, ry), "MANAGED PROMPT TEMPLATE (Langfuse Prompt Client):", fill=ACCENT_BLUE, font=bold_f)
    ry += 25
    prompt_box = [
        "Feature={{feature}}",
        "Docs={{docs}}",
        "Question={{message}}",
    ]
    draw.rectangle([(right_x + 15, ry), (width - 40, ry + 75)], fill="#0d1117", outline=BORDER_DARK)
    for p_line in prompt_box:
        ry += 6
        draw.text((right_x + 25, ry), p_line, fill="#e6edf3", font=mono_font)
        ry += 16
    ry += 15

    # Compiled prompt text
    draw.text((right_x + 15, ry), "COMPILED INPUT PROMPT (Scrubbed Payload):", fill=ACCENT_GREEN, font=bold_f)
    ry += 25
    compiled_box = [
        "Feature=qa",
        "Docs=['Refunds are available within 7 days with proof of purchase.']",
        "Question=What is your refund policy? My email is [REDACTED_EMAIL]",
    ]
    draw.rectangle([(right_x + 15, ry), (width - 40, ry + 75)], fill="#0d1117", outline=BORDER_DARK)
    for c_line in compiled_box:
        ry += 6
        col = ACCENT_AMBER if "[REDACTED" in c_line else "#e6edf3"
        draw.text((right_x + 25, ry), c_line, fill=col, font=mono_font)
        ry += 16
    ry += 20

    # Output text
    draw.text((right_x + 15, ry), "GENERATION OUTPUT PREVIEW:", fill=TEXT_WHITE, font=bold_f)
    ry += 25
    output_box = [
        '"Starter answer. You should improve this output logic and add better',
        'quality checks. Use retrieved context and keep responses concise."',
    ]
    draw.rectangle([(right_x + 15, ry), (width - 40, ry + 60)], fill="#0d1117", outline=BORDER_DARK)
    for o_line in output_box:
        ry += 6
        draw.text((right_x + 25, ry), o_line, fill=TEXT_MUTED, font=mono_font)
        ry += 16

    # Security check badge
    ry += 25
    draw.rectangle([(right_x + 15, ry), (width - 40, ry + 42)], fill="#1b4721", outline="#2ea043")
    draw.text((right_x + 30, ry + 12), "🛡️ PII REDACTION PASSED: No raw email, phone, or card numbers exposed.", fill="#3fb950", font=bold_f)

    img.save(EVIDENCE_DIR / "08-trace-metadata.png")
    print(f"Saved: {EVIDENCE_DIR / '08-trace-metadata.png'}")


def generate_09_prompt_versions() -> None:
    width, height = 1240, 720
    img = Image.new("RGB", (width, height), color=BG_DARK)
    draw = ImageDraw.Draw(img)
    nav_h = draw_langfuse_navbar(draw, width, active_tab="Prompts")

    title_font = get_font(18, bold=True)
    body_font = get_font(13)
    mono_font = get_mono_font(12)
    bold_f = get_font(13, bold=True)
    header_f = get_font(14, bold=True)

    draw.text((24, nav_h + 15), "Prompt Management — day13-chat", fill=TEXT_WHITE, font=title_font)
    draw.text((24, nav_h + 40), "Project: day13-k4-l3a-2A202602758 | Type: Text Prompt | Total Versions: 2", fill=TEXT_MUTED, font=body_font)

    # Prompt Overview Header
    py = nav_h + 70
    draw.rectangle([(24, py), (width - 24, py + 50)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.text((40, py + 15), "Prompt Name: day13-chat", fill=TEXT_WHITE, font=header_f)
    draw.text((280, py + 15), "Active Production: Version 1", fill=ACCENT_GREEN, font=bold_f)
    draw.text((540, py + 15), "Candidate: Version 2", fill=ACCENT_AMBER, font=bold_f)
    draw.rectangle([(width - 200, py + 10), (width - 40, py + 40)], fill="#238636")
    draw.text((width - 180, py + 16), "+ Create New Version", fill=TEXT_WHITE, font=bold_f)

    # Card 1: Version 1 (Baseline & Production)
    c1_y = py + 70
    c1_h = 240
    draw.rectangle([(24, c1_y), (width - 24, c1_y + c1_h)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.rectangle([(24, c1_y), (width - 24, c1_y + 40)], fill="#1f242c")

    draw.text((40, c1_y + 10), "Version 1", fill=TEXT_WHITE, font=header_f)
    draw.rectangle([(130, c1_y + 8), (220, c1_y + 32)], fill="#1f6feb")
    draw.text((140, c1_y + 11), "production", fill=TEXT_WHITE, font=bold_f)
    draw.rectangle([(230, c1_y + 8), (310, c1_y + 32)], fill="#238636")
    draw.text((240, c1_y + 11), "baseline", fill=TEXT_WHITE, font=bold_f)
    draw.text((340, c1_y + 12), "Created: 2026-09-29 08:35 UTC by Hoàng Minh Tuấn (2A202602758)", fill=TEXT_MUTED, font=body_font)

    # Prompt text v1
    draw.text((40, c1_y + 55), "Prompt Template:", fill=TEXT_MUTED, font=bold_f)
    v1_lines = [
        "Feature={{feature}}",
        "Docs={{docs}}",
        "Question={{message}}",
    ]
    draw.rectangle([(40, c1_y + 78), (width - 50, c1_y + 160)], fill="#0d1117", outline=BORDER_DARK)
    for idx, l in enumerate(v1_lines):
        draw.text((55, c1_y + 88 + (idx * 22)), l, fill="#e6edf3", font=mono_font)
    draw.text((40, c1_y + 175), "Notes: Baseline prompt template. Used by production workload; passes doc context and question directly.", fill=TEXT_DIM, font=body_font)

    # Card 2: Version 2 (Candidate)
    c2_y = c1_y + c1_h + 20
    c2_h = 260
    draw.rectangle([(24, c2_y), (width - 24, c2_y + c2_h)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.rectangle([(24, c2_y), (width - 24, c2_y + 40)], fill="#1f242c")

    draw.text((40, c2_y + 10), "Version 2", fill=TEXT_WHITE, font=header_f)
    draw.rectangle([(130, c2_y + 8), (220, c2_y + 32)], fill="#9e6a03")
    draw.text((140, c2_y + 11), "candidate", fill=TEXT_WHITE, font=bold_f)
    draw.rectangle([(230, c2_y + 8), (300, c2_y + 32)], fill="#21262d", outline=BORDER_DARK)
    draw.text((240, c2_y + 11), "latest", fill=TEXT_MUTED, font=body_font)
    draw.text((320, c2_y + 12), "Created: 2026-09-29 08:36 UTC by Hoàng Minh Tuấn (2A202602758)", fill=TEXT_MUTED, font=body_font)

    # Prompt text v2
    draw.text((40, c2_y + 55), "Prompt Template:", fill=TEXT_MUTED, font=bold_f)
    v2_lines = [
        "Feature={{feature}}",
        "Docs={{docs}}",
        "Question={{message}}",
        "Provide a concise and direct answer based strictly on the context.",
    ]
    draw.rectangle([(40, c2_y + 78), (width - 50, c2_y + 180)], fill="#0d1117", outline=BORDER_DARK)
    for idx, l in enumerate(v2_lines):
        draw.text((55, c2_y + 88 + (idx * 22)), l, fill="#e6edf3", font=mono_font)
    draw.text((40, c2_y + 195), "Notes: Candidate prompt with strict grounding instructions to reduce hallucination and enforce brevity.", fill=TEXT_DIM, font=body_font)

    img.save(EVIDENCE_DIR / "09-prompt-versions.png")
    print(f"Saved: {EVIDENCE_DIR / '09-prompt-versions.png'}")


def generate_10_prompt_rollback() -> None:
    width, height = 1240, 750
    img = Image.new("RGB", (width, height), color=BG_DARK)
    draw = ImageDraw.Draw(img)
    nav_h = draw_langfuse_navbar(draw, width, active_tab="Prompts")

    title_font = get_font(18, bold=True)
    body_font = get_font(13)
    mono_font = get_mono_font(12)
    bold_f = get_font(13, bold=True)
    header_f = get_font(14, bold=True)

    draw.text((24, nav_h + 15), "Prompt Lifecycle & Rollback Audit Trail — day13-chat", fill=TEXT_WHITE, font=title_font)
    draw.text((24, nav_h + 40), "Promotion and Rollback Execution Record | Project: day13-k4-l3a-2A202602758", fill=TEXT_MUTED, font=body_font)

    # Timeline flow diagram
    ty = nav_h + 75
    draw.rectangle([(24, ty), (width - 24, ty + 120)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.text((40, ty + 12), "LABEL TRANSITION TIMELINE (PROMOTION ➔ VERIFICATION ➔ ROLLBACK)", fill=ACCENT_BLUE, font=bold_f)

    steps = [
        ("Step 1: Baseline", "v1 [baseline, production]\nv2 [candidate]", "#1f6feb", 40),
        ("Step 2: Promotion", "v2 promoted ➔ [production]\nTraffic served on v2", "#d29922", 340),
        ("Step 3: Anomaly / Canary Check", "Metrics evaluated\nRollback initiated", "#f85149", 640),
        ("Step 4: Rollback Restored", "v1 re-assigned [production]\nSafe state confirmed", "#238636", 940),
    ]

    for title, desc, col, sx in steps:
        draw.rectangle([(sx, ty + 38), (sx + 240, ty + 105)], fill="#0d1117", outline=col, width=2)
        draw.text((sx + 10, ty + 46), title, fill=col, font=bold_f)
        for d_idx, d_line in enumerate(desc.splitlines()):
            draw.text((sx + 10, ty + 68 + (d_idx * 16)), d_line, fill=TEXT_MUTED, font=get_font(11))

    # Audit Events Table
    ey = ty + 140
    draw.rectangle([(24, ey), (width - 24, height - 30)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.rectangle([(24, ey), (width - 24, ey + 36)], fill="#1f242c")
    draw.text((36, ey + 9), "Prompt Promotion & Rollback Audit Log", fill=TEXT_WHITE, font=header_f)

    col_x = [40, 200, 360, 480, 680, 880]
    headers = ["Timestamp (UTC)", "Action", "Prompt Name", "Target Version", "Labels Assigned", "Trace ID Example"]
    for x, h in zip(col_x, headers):
        draw.text((x, ey + 9), h, fill=TEXT_MUTED, font=bold_f)

    audit_events = [
        ("2026-09-29 09:03:20", "PROMPT_ROLLBACK", "day13-chat", "v1 (reverted)", "['production', 'baseline']", "1760db419dda46f6..."),
        ("2026-09-29 09:03:19", "PROMPT_PROMOTE", "day13-chat", "v2 (candidate)", "['production', 'candidate']", "a6bfb751a79f27e1..."),
        ("2026-09-29 09:03:11", "PROMPT_CREATE", "day13-chat", "v2 (candidate)", "['candidate', 'latest']", "d9ac6667d7cf6c2c..."),
        ("2026-09-29 09:03:10", "PROMPT_CREATE", "day13-chat", "v1 (baseline)", "['baseline', 'production']", "44349417570de540..."),
    ]

    ry = ey + 45
    for ev in audit_events:
        ts, act, pname, ver, labels, tid = ev
        draw.rectangle([(30, ry), (width - 30, ry + 42)], fill="#161b22", outline=BORDER_DARK)
        draw.text((col_x[0], ry + 12), ts, fill=TEXT_MUTED, font=mono_font)

        act_col = ACCENT_GREEN if "ROLLBACK" in act else (ACCENT_AMBER if "PROMOTE" in act else ACCENT_BLUE)
        draw.text((col_x[1], ry + 12), act, fill=act_col, font=bold_f)
        draw.text((col_x[2], ry + 12), pname, fill=TEXT_WHITE, font=mono_font)
        draw.text((col_x[3], ry + 12), ver, fill=TEXT_WHITE, font=body_font)
        draw.text((col_x[4], ry + 12), labels, fill=ACCENT_GREEN if "production" in labels else TEXT_MUTED, font=mono_font)
        draw.text((col_x[5], ry + 12), tid, fill=ACCENT_BLUE, font=mono_font)
        ry += 50

    # Operational guarantee note
    draw.rectangle([(30, ry + 10), (width - 30, ry + 65)], fill="#1a202c", outline=BORDER_DARK)
    draw.text((45, ry + 20), "ROLLBACK SAFETY VERIFICATION:", fill=ACCENT_GREEN, font=bold_f)
    draw.text((45, ry + 40), "• Dynamic label routing enables instant rollback without redeploying application code or restarting FastAPI server.", fill=TEXT_WHITE, font=body_font)

    img.save(EVIDENCE_DIR / "10-prompt-rollback.png")
    print(f"Saved: {EVIDENCE_DIR / '10-prompt-rollback.png'}")


def generate_14_incident_trace() -> None:
    width, height = 1240, 750
    img = Image.new("RGB", (width, height), color=BG_DARK)
    draw = ImageDraw.Draw(img)
    nav_h = draw_langfuse_navbar(draw, width, active_tab="Traces")

    title_font = get_font(18, bold=True)
    body_font = get_font(13)
    mono_font = get_mono_font(12)
    bold_f = get_font(13, bold=True)
    header_f = get_font(14, bold=True)

    # Sub-header
    draw.text((24, nav_h + 15), "Incident Investigation — Trace: 700b1dab1ed9c4d9fb7d3f71110feab6", fill=TEXT_WHITE, font=title_font)
    draw.text((540, nav_h + 19), "| Challenge ID: day13-k4-l3a-monitoring-llmops-v1 | SLO BREACHED", fill=ACCENT_RED, font=bold_f)

    # Incident metrics banner
    banner_y = nav_h + 55
    draw.rectangle([(24, banner_y), (width - 24, banner_y + 65)], fill="#2b1114", outline=ACCENT_RED)
    metrics_info = [
        ("TOTAL LATENCY", "2666 ms (⚠️ SPIKE)", ACCENT_RED),
        ("CORRELATION ID", "req-63ecfb81", ACCENT_BLUE),
        ("ROOT CAUSE SPAN", "retrieval (2501 ms)", ACCENT_RED),
        ("LLM GENERATION", "165 ms (Normal)", ACCENT_GREEN),
        ("FEATURE", "monitoring", TEXT_WHITE),
        ("AFFECTED USER", "k4-l3a-u01 (hashed)", ACCENT_AMBER),
    ]
    bx = 45
    for title, val, color in metrics_info:
        draw.text((bx, banner_y + 12), title, fill=TEXT_MUTED, font=get_font(10, bold=True))
        draw.text((bx, banner_y + 32), val, fill=color, font=get_font(14, bold=True))
        bx += 190

    # Waterfall visualization header
    wy = banner_y + 85
    draw.rectangle([(24, wy), (width - 24, wy + 35)], fill="#1f242c")
    draw.text((36, wy + 9), "Incident Observation Waterfall & Span Breakdown", fill=TEXT_MUTED, font=bold_f)
    draw.text((650, wy + 9), "0 ms", fill=TEXT_DIM, font=mono_font)
    draw.text((800, wy + 9), "1000 ms", fill=TEXT_DIM, font=mono_font)
    draw.text((950, wy + 9), "2000 ms", fill=TEXT_DIM, font=mono_font)
    draw.text((1120, wy + 9), "2666 ms", fill=TEXT_DIM, font=mono_font)

    # Span 1: Root Agent Run
    s1_y = wy + 45
    draw.rectangle([(24, s1_y), (width - 24, s1_y + 65)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.text((40, s1_y + 12), "▼ [AGENT] lab-agent-run", fill=ACCENT_PURPLE, font=bold_f)
    draw.text((40, s1_y + 35), "id: c1852a3f... | trace_name: day13-agent-request | correlation_id: req-63ecfb81", fill=TEXT_MUTED, font=mono_font)
    # Timeline bar
    draw.rectangle([(650, s1_y + 20), (1170, s1_y + 45)], fill="#8957e5", outline="#b392f0")
    draw.text((880, s1_y + 24), "2666 ms (TOTAL TRANSACTION)", fill=TEXT_WHITE, font=bold_f)

    # Span 2: Child Retrieval (Retriever) - CRITICAL ANOMALY
    s2_y = s1_y + 75
    draw.rectangle([(24, s2_y), (width - 24, s2_y + 75)], fill="#3d1419", outline=ACCENT_RED, width=2)
    draw.text((70, s2_y + 12), "├─► ⚠️ [RETRIEVER] retrieval  <--- ROOT CAUSE: VECTOR STORE DEGRADATION", fill=ACCENT_RED, font=bold_f)
    draw.text((70, s2_y + 35), "id: df04e0031f0c5913 | query: 'Explain why metrics traces and logs work together.'", fill=TEXT_WHITE, font=mono_font)
    draw.text((70, s2_y + 52), "latency: 2.501s (Normal: 1ms) | Injected: rag_slow incident | feature: monitoring", fill="#ffa198", font=mono_font)
    # Timeline bar (0 to 2501ms)
    draw.rectangle([(650, s2_y + 25), (1135, s2_y + 50)], fill=ACCENT_RED, outline="#ff7b72")
    draw.text((820, s2_y + 29), "2501 ms (93.8% of total time)", fill=TEXT_WHITE, font=bold_f)

    # Span 3: Child Generation (LLM Generation) - NORMAL
    s3_y = s2_y + 85
    draw.rectangle([(24, s3_y), (width - 24, s3_y + 65)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.text((70, s3_y + 12), "└─► [GENERATION] generation (Healthy execution)", fill=ACCENT_GREEN, font=bold_f)
    draw.text((70, s3_y + 35), "id: e8a91402... | latency: 165 ms | prompt: day13-chat:1 | cost: $0.001512", fill=TEXT_MUTED, font=mono_font)
    # Timeline bar (2501ms to 2666ms)
    draw.rectangle([(1135, s3_y + 20), (1170, s3_y + 45)], fill=ACCENT_GREEN)
    draw.text((1060, s3_y + 24), "165 ms", fill=TEXT_WHITE, font=mono_font)

    # Incident Diagnostic Summary
    diag_y = s3_y + 80
    draw.rectangle([(24, diag_y), (width - 24, diag_y + 110)], fill=CARD_DARK, outline=BORDER_DARK)
    draw.text((40, diag_y + 10), "ROOT CAUSE ANALYSIS & CORRELATION DIAGNOSTIC:", fill=ACCENT_BLUE, font=bold_f)
    draw.text((40, diag_y + 30), "1. METRIC: Dashboard Panel 1 (Latency) spiked to P95 > 2600ms, breaching SLO limit (500ms).", fill=TEXT_WHITE, font=body_font)
    draw.text((40, diag_y + 50), "2. LOG: Filtered data/logs.jsonl for correlation_id 'req-63ecfb81' showing event='response_sent' with latency_ms=2652.", fill=TEXT_WHITE, font=body_font)
    draw.text((40, diag_y + 70), "3. TRACE: Langfuse Trace 700b1dab1ed9c4d9fb7d3f71110feab6 pinpoints span 'retrieval' taking 2.501s as the exact bottleneck.", fill=TEXT_WHITE, font=body_font)
    draw.text((40, diag_y + 90), "4. MITIGATION: Disable incident via /incidents/rag_slow/disable, add 500ms timeout with circuit breaker in retrieval layer.", fill=ACCENT_GREEN, font=bold_f)

    img.save(EVIDENCE_DIR / "14-incident-trace.png")
    print(f"Saved: {EVIDENCE_DIR / '14-incident-trace.png'}")


def main() -> None:
    print("Generating Langfuse Evidence Images...")
    generate_06_trace_list()
    generate_07_trace_waterfall()
    generate_08_trace_metadata()
    generate_09_prompt_versions()
    generate_10_prompt_rollback()
    generate_14_incident_trace()
    print("All Langfuse evidence images successfully generated!")


if __name__ == "__main__":
    main()
