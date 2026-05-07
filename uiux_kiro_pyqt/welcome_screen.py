import os
import sys
import random

# ─── دعم وضع PyInstaller المجمّد ───
if getattr(sys, 'frozen', False):
    _UI_DIR = os.path.join(sys._MEIPASS, "uiux_kiro_pyqt")
else:
    _UI_DIR = os.path.dirname(os.path.abspath(__file__))
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QVariantAnimation, QAbstractAnimation
from PyQt6.QtGui import (
    QFont, QPainter, QColor, QPen, QBrush,
    QRadialGradient, QLinearGradient, QPixmap, QPainterPath
)

from translations import lang_manager, t

from theme import (
    BG_DEEP, BG_MID, CYAN, CYAN_DIM, BLUE, VIOLET,
    TEXT_MAIN, TEXT_SUB, TEXT_DIM, GLASS, BORDER_DIM, BORDER_CYAN,
    paint_bg
)


# ─── صورة الروبوت بشكل دائري ───────────────────────────────────
class RoboticCircularLogo(QWidget):
    """عرض صورة الروبوت بشكل دائري مع إطار متوهج"""
    def __init__(self, size=160, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        logo_path = os.path.join(_UI_DIR, "Gemini_Generated_Image_rrv8szrrv8szrrv8.png")
        self._pixmap = QPixmap(logo_path).scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        s = self._size

        path = QPainterPath()
        path.addEllipse(QRectF(0, 0, s, s))
        p.save()
        p.setClipPath(path)
        px_w, px_h = self._pixmap.width(), self._pixmap.height()
        x = (s - px_w) // 2
        y = (s - px_h) // 2
        p.drawPixmap(x, y, self._pixmap)
        p.restore()

        pen = QPen(QColor(0, 120, 215, 100), 3)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(1.5, 1.5, s - 3, s - 3))

        glow = QRadialGradient(s / 2, s / 2, s * 0.55)
        glow.setColorAt(0.85, QColor(0, 120, 215, 0))
        glow.setColorAt(1.0, QColor(0, 120, 215, 20))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(-5, -5, s + 10, s + 10))
        p.end()


# ─── أيقونة دوارة متحركة ────────────────────────────────────────
class CoreLogo(QWidget):
    """أيقونة مركزية متحركة تمثل قلب النظام"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self.a1 = self.a2 = self.a3 = 0.0
        self.pulse = 0.0
        self._pd = 1
        self._frame = 0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(16)

    def _tick(self):
        self.a1 = (self.a1 + 8.5) % 360
        self.a2 = (self.a2 - 12.0) % 360
        self.a3 = (self.a3 + 6.0) % 360
        self.pulse += 0.3 * self._pd
        if self.pulse > 7: self._pd = -1
        elif self.pulse < 0: self._pd = 1
        self._frame += 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2

        glow = QRadialGradient(cx, cy, 36 + self.pulse)
        glow.setColorAt(0.0, QColor(0, 120, 215, 150))
        glow.setColorAt(0.4, QColor(0, 120, 215, 60))
        glow.setColorAt(1.0, QColor(0, 120, 215, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        r = int(36 + self.pulse)
        p.drawEllipse(int(cx - r), int(cy - r), r * 2, r * 2)

        p.translate(cx, cy)
        for angle, radius, color, dash in [
            (self.a1, 52, CYAN, [10, 18, 4, 18]),
            (self.a2, 38, BLUE, [25, 15, 8, 15]),
            (self.a3, 68, VIOLET, [40, 20]),
        ]:
            p.rotate(angle)
            pen = QPen(QColor(color), 1.2)
            pen.setDashPattern(dash)
            p.setPen(pen)
            p.drawEllipse(-radius, -radius, radius * 2, radius * 2)
            p.rotate(-angle)

        dot = QRadialGradient(0, 0, 14)
        dot.setColorAt(0.0, QColor(255, 255, 255, 255))
        dot.setColorAt(0.5, QColor(0, 120, 215, 150))
        dot.setColorAt(1.0, QColor(0, 120, 215, 0))
        p.setBrush(QBrush(dot)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(-14, -14, 28, 28)
        p.end()


# ─── بطاقة المميزات ───────────────────────────────────────────
class FeatureCard(QFrame):
    """بطاقة مميزات بتأثير زجاجي حديث"""
    ACCENTS = [CYAN, BLUE, VIOLET]
    ICONS   = ["★", "◎", "⊞"]

    def __init__(self, title, desc, idx, parent=None):
        super().__init__(parent)
        self._accent = QColor(self.ACCENTS[idx % 3])
        self._border = QColor(0, 0, 0, 40)
        self._idx = idx
        self._apply()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # إضافة ظل لزيادة التباين والعمق
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        anim = QVariantAnimation(self)
        anim.setDuration(300)
        anim.setStartValue(QColor(0, 0, 0, 40))
        anim.setEndValue(self._accent)
        anim.valueChanged.connect(lambda c: (setattr(self, '_border', c), self._apply()))
        self._anim = anim

        self.lo = QVBoxLayout(self)
        self.lo.setContentsMargins(15, 15, 15, 15)
        self.lo.setSpacing(8)

        hex_color = self.ACCENTS[idx % 3].lstrip('#')
        r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)

        self.icon = QLabel(self.ICONS[idx % 3])
        self.icon.setFixedSize(34, 34)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setFont(QFont("Segoe UI", 14))
        self.icon.setStyleSheet(f"background:rgba({r},{g},{b},30); border:1px solid rgba({r},{g},{b},70); border-radius:9px; color:{self.ACCENTS[idx%3]};")

        self.tl = QLabel()
        self.tl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.tl.setStyleSheet(f"color:{TEXT_MAIN}; background:transparent; border:none;")
        
        self.dl = QLabel()
        self.dl.setFont(QFont("Segoe UI", 10))
        self.dl.setStyleSheet(f"color:{TEXT_SUB}; background:transparent; border:none;")
        self.dl.setWordWrap(True)

        self.lo.addWidget(self.icon)
        self.lo.addWidget(self.tl)
        self.lo.addWidget(self.dl)
        self.lo.addStretch()

        self.update_text(title, desc)

    def update_text(self, title, desc):
        align = lang_manager.align
        self.tl.setText(title)
        self.dl.setText(desc)
        self.tl.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        self.dl.setAlignment(align | Qt.AlignmentFlag.AlignTop)
        self.lo.setAlignment(self.icon, align)

    def _apply(self):
        c = self._border
        self.setStyleSheet(f"QFrame {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(0,0,0,0.04), stop:1 rgba(0,0,0,0.02)); border-radius:18px; border:1px solid rgba({c.red()},{c.green()},{c.blue()},60); border-top:1px solid rgba(0,0,0,0.08); }}")

    def enterEvent(self, e): self._anim.setDirection(QAbstractAnimation.Direction.Forward); self._anim.start(); super().enterEvent(e)
    def leaveEvent(self, e): self._anim.setDirection(QAbstractAnimation.Direction.Backward); self._anim.start(); super().leaveEvent(e)


# ─── شاشة الترحيب ────────────────────────────────────────────
class WelcomeScreen(QWidget):
    def __init__(self, on_navigate, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self._labels = {}; self._cards = []
        self._build()
        lang_manager.language_changed.connect(self._on_lang_changed)

    def paintEvent(self, event):
        paint_bg(self)

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        content = QWidget(); content.setStyleSheet("background:transparent;"); lo = QVBoxLayout(content)
        lo.setAlignment(Qt.AlignmentFlag.AlignTop); lo.setContentsMargins(30, 20, 30, 20); lo.setSpacing(6)
        
        header = QHBoxLayout()
        l_line = QFrame(); l_line.setFixedHeight(1); l_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed); l_line.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 transparent,stop:1 {CYAN});border:none;"); header.addWidget(l_line)
        self._labels["badge"] = QLabel(t("welcome_badge").upper()); self._labels["badge"].setFont(QFont("Segoe UI", 9, QFont.Weight.Bold)); self._labels["badge"].setStyleSheet(f"color:{CYAN}; background:rgba(0, 120, 215, 0.08); border:1px solid {CYAN}; border-radius:3px; padding:4px 16px; letter-spacing:2px;"); header.addWidget(self._labels["badge"])
        r_line = QFrame(); r_line.setFixedHeight(1); r_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed); r_line.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {CYAN},stop:1 transparent);border:none;"); header.addWidget(r_line)
        self._lang_btn = QPushButton(t("lang_btn")); self._lang_btn.setFixedSize(45, 30); self._lang_btn.setCursor(Qt.CursorShape.PointingHandCursor); self._lang_btn.setStyleSheet(f"background:rgba(0,0,0,0.05); color:{CYAN}; border:1px solid {BORDER_CYAN}; border-radius:4px; font-weight:bold;"); self._lang_btn.clicked.connect(lang_manager.toggle); header.addWidget(self._lang_btn)
        
        lo.addLayout(header); lo.addSpacing(15)
        
        # شعار الروبوت الدائري
        robot = RoboticCircularLogo(160)
        lo.addWidget(robot, alignment=Qt.AlignmentFlag.AlignCenter); lo.addSpacing(10)
        
        sub = QLabel("AI DESKTOP ASSISTANT"); sub.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); sub.setStyleSheet(f"color:{CYAN}; letter-spacing:3px;"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter); lo.addWidget(sub)
        self._labels["title"] = QLabel(); self._labels["title"].setFont(QFont("Arial Black", 24, QFont.Weight.Black)); self._labels["title"].setAlignment(Qt.AlignmentFlag.AlignCenter); self._update_title_text(); lo.addWidget(self._labels["title"])
        self._labels["desc"] = QLabel(t("welcome_desc")); self._labels["desc"].setFont(QFont("Segoe UI", 10)); self._labels["desc"].setStyleSheet(f"color:{TEXT_SUB};"); self._labels["desc"].setAlignment(Qt.AlignmentFlag.AlignCenter); self._labels["desc"].setWordWrap(True); self._labels["desc"].setMaximumWidth(650); lo.addWidget(self._labels["desc"], alignment=Qt.AlignmentFlag.AlignCenter)
        lo.addSpacing(20)
        
        # الكروت الثلاثة
        gw = QWidget(); grid = QHBoxLayout(gw); grid.setSpacing(16); grid.setContentsMargins(0, 0, 0, 0)
        for i, (tt, dd) in enumerate([(t("feat1_title"), t("feat1_desc")), (t("feat2_title"), t("feat2_desc")), (t("feat3_title"), t("feat3_desc"))]):
            card = FeatureCard(tt, dd, i); self._cards.append(card); grid.addWidget(card)
        lo.addWidget(gw); lo.addSpacing(25)
        
        row = QHBoxLayout(); row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._start_btn = QPushButton(t("welcome_btn")); self._start_btn.setFixedSize(240, 56); self._start_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold)); self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor); self._start_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {CYAN},stop:1 {BLUE}); color:{BG_DEEP}; border-radius:8px; border:none; }} QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33ffcc,stop:1 #33ccff); }}"); self._start_btn.clicked.connect(lambda: self.on_navigate("cf")); row.addWidget(self._start_btn)
        lo.addLayout(row); lo.addStretch(); root.addWidget(content)

    def _update_title_text(self):
        txt = t("welcome_title")
        # تلوين الكلمة المحددة فقط باستخدام HTML
        colored_txt = txt.replace("Kiro AI", f"<span style='color:{CYAN};'>Kiro AI</span>")
        self._labels["title"].setText(colored_txt)
        self._labels["title"].setStyleSheet(f"color:{TEXT_MAIN}; font-weight: bold;")

    def _on_lang_changed(self, lang):
        self._labels["badge"].setText(t("welcome_badge").upper()); self._update_title_text(); self._labels["desc"].setText(t("welcome_desc")); self._start_btn.setText(t("welcome_btn")); self._lang_btn.setText(t("lang_btn"))
        feats = [(t("feat1_title"), t("feat1_desc")), (t("feat2_title"), t("feat2_desc")), (t("feat3_title"), t("feat3_desc"))]
        for card, (tt, dd) in zip(self._cards, feats): card.update_text(tt, dd)