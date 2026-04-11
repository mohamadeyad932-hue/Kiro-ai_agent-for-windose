"""
Kiro AI - Shared Theme & Colors (PyQt6)
التصميم المشترك والألوان لجميع الواجهات
"""

# ─── لوحة الألوان الموحدة (Midnight Slate) ───
BG_DEEP     = "#020650"
BG_MID      = "#050F26"
CYAN        = "#00D2FF"
BLUE        = "#1A73E8"
VIOLET      = "#BD00FF"
EMERALD     = "#10B981"
AMBER       = "#F59E0B"
TEXT_MAIN   = "#FFFFFF"
TEXT_SUB    = "#80A0C0"
GLASS       = "rgba(255, 255, 255, 0.05)"
BORDER_CYAN = "rgba(0, 210, 255, 0.15)"

# للهيكلية القديمة التي تعتمد على COLORS (للتوافق)
COLORS = {
    "bg":           BG_DEEP,
    "panel":        "#01042E", # أغمق للشريط الجانبي
    "border":       "rgba(0, 210, 255, 0.1)",
    "ink":          TEXT_MAIN,
    "ink3":         TEXT_SUB,
    "ink4":         "#507090",
    "violet":       VIOLET,
    "violet_d":     CYAN,
    "violet_dim":   "rgba(0, 210, 255, 0.1)",
    "cyan":         VIOLET,
    "cyan_dim":     "rgba(189, 0, 255, 0.1)",
    "emerald":      EMERALD,
    "emerald_dim":  "rgba(16, 185, 129, 0.1)",
    "amber":        AMBER,
    "rose":         "#FF4D4D",
    "white":        "#FFFFFF",
    "terminal_bg":  "rgba(0, 0, 0, 0.4)",
    "terminal_top": "rgba(0, 210, 255, 0.08)",
    "terminal_txt": CYAN,
    "terminal_ok":  EMERALD,
    "toggle_on":    CYAN,
    "toggle_off":   "rgba(255, 255, 255, 0.1)",
    "toggle_knob":  "#FFFFFF",
    "card_hover":   "rgba(255, 255, 255, 0.05)",
}

# ─── الخطوط ───
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_AR = "Segoe UI"

# ─── أبعاد النافذة ───
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650
SIDEBAR_WIDTH = 260

# ─── رسائل التيرمنال ───
LOG_MESSAGES = [
    ("inf", "[SYS] Scanning sectors: Desktop, Downloads..."),
    ("inf", "[AI] Detected 287 unorganized data entities."),
    ("inf", "[NLP] Extracting text semantics from 172 documents..."),
    ("inf", "[VISION] Running image classification models..."),
    ("inf", "[CORE] Clustering data into distinct neural pathways..."),
    ("inf", '[SYS] Creating node: "مستندات قانونية وإدارية"'),
    ("inf", '[SYS] Creating node: "أرشيف مرئي"'),
    ("inf", "[ACT] Moving bytes to designated nodes..."),
    ("inf", "[SYS] Validating file hashes..."),
    ("ok",  "[OK] Operation Successful. 287 files reorganized."),
]

# ─── ستايل عام للتطبيق (QSS) ───
GLOBAL_STYLESHEET = f"""
    * {{
        font-family: '{FONT_FAMILY}';
    }}
    QMainWindow {{
        background-color: {BG_DEEP};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(0, 210, 255, 0.2);
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {CYAN};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QToolTip {{
        background-color: {BG_MID};
        color: {TEXT_MAIN};
        border: 1px solid {BORDER_CYAN};
        padding: 6px 10px;
        border-radius: 8px;
    }}
"""
