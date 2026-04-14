from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush, QLinearGradient, QRadialGradient
# ─── لوحة الألوان الموحدة (Midnight Slate) ───
# ─── لوحة الألوان الموحدة (Light Theme) ───
BG_DEEP     = "#FFFFFF"  # خلفية بيضاء نقية
BG_MID      = "#F8F9FA"  # رمادي فاتح جداً للجوانب
CYAN        = "#0078D7"  # أزرق ويندوز (أغمق للتباين على الأبيض)
CYAN_DIM    = "#005A9E"
BLUE        = "#003366"
VIOLET      = "#7800AD"
EMERALD     = "#059669"
AMBER       = "#D97706"
TEXT_MAIN   = "#000000"
TEXT_SUB    = "#3C4043"
TEXT_DIM    = "#5F6368"
GLASS       = "rgba(0, 0, 0, 0.04)"
BORDER_DIM  = "rgba(0, 0, 0, 0.08)"
BORDER_CYAN = "rgba(0, 120, 215, 0.3)"


# للهيكلية القديمة التي تعتمد على COLORS (للتوافق)
COLORS = {
    "bg":           BG_DEEP,
    "panel":        "#FFFFFF", # خلفية اللوحات بيضاء
    "border":       "rgba(0, 0, 0, 0.08)", # حدود داكنة رقيقة
    "ink":          TEXT_MAIN,
    "ink3":         TEXT_SUB,
    "ink4":         TEXT_DIM,
    "violet":       VIOLET,
    "violet_d":     CYAN,
    "violet_dim":   "rgba(0, 120, 215, 0.1)",
    "cyan":         CYAN,
    "cyan_dim":     "rgba(0, 120, 215, 0.12)",
    "emerald":      EMERALD,
    "emerald_dim":  "rgba(16, 185, 129, 0.1)",
    "amber":        AMBER,
    "rose":         "#FF4D4D",
    "white":        "#FFFFFF",
    "terminal_bg":  "#000000",
    "terminal_top": "#1A1A1A",
    "terminal_txt": "#00F0FF",
    "terminal_ok":  "#00D4FF",
    "toggle_on":    CYAN,
    "toggle_off":   "rgba(0, 0, 0, 0.1)",
    "toggle_knob":  "#FFFFFF",
    "card_hover":   "rgba(0, 0, 0, 0.03)",
}

# ─── الخطوط ───
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_AR = "Segoe UI"

# ─── أبعاد النافذة ───
WINDOW_WIDTH = 900
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
        background: rgba(76, 194, 255, 0.3);
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


# ─── خلفية مشتركة لجميع الشاشات ───
def paint_bg(widget):
    """رسم خلفية التدرج اللوني + التوهج الشعاعي على أي ويدجت."""
    p = QPainter(widget)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    W, H = widget.width(), widget.height()

    # 1. التدرج اللوني العمودي الهادئ
    bg = QLinearGradient(0, 0, 0, H)
    bg.setColorAt(0.0, QColor(BG_DEEP))
    bg.setColorAt(1.0, QColor(BG_MID))
    p.fillRect(widget.rect(), QBrush(bg))

    # 2. توهج علوي بسيط لإضافة عمق
    cg = QRadialGradient(W / 2, -H * 0.1, W * 0.8)
    cg.setColorAt(0.0, QColor(0, 120, 215, 15))
    cg.setColorAt(1.0, QColor(0, 120, 215, 0))
    p.fillRect(widget.rect(), QBrush(cg))
    p.end()


class GradientBase(QWidget):
    """
    كلاس أساسي يرسم صورة الخلفية.
    أي شاشة ترث منه ستحصل على نفس الخلفية الجميلة.
    """
    def paintEvent(self, event):
        paint_bg(self)


