"""
Kiro AI - Premium Midnight Slate Screen (PyQt6)
شاشة الترحيب - تصميم ذكاء اصطناعي احترافي بألوان ليلية فاتحة وشبكة منتثرة دوماً
"""
import math
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QGridLayout,
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QVariantAnimation, QAbstractAnimation
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QRadialGradient, QLinearGradient

# نفترض وجود هذه الملفات في مشروعك
from translations import lang_manager, t

# --- لوحة الألوان الجديدة المحدثة (تفتيح قليلاً وأكثر أناقة) ---
# تم استخدام درجات Slate أفتح (Mid-tone Slates)
BG_TOP = "#1e293b"              # Slate 800 (أفتح من 900)
BG_BOTTOM = "#334155"           # Slate 700 (أفتح من 800)
NEON_BLUE = "#38bdf8"           # أزرق سماوي ساطع للشبكات (Light Sky Blue)
NEON_VIOLET = "#a78bfa"         # بنفسجي فاتح وهادئ
NEON_CYAN = "#22d3ee"           # سيان مشرق
# زجاج بلون أفتح يتناسب مع الخلفية الجديدة لضمان التباين
GLASS_BG = "rgba(51, 65, 85, 160)" 
TEXT_MAIN = "#f8fafc"
TEXT_SUB = "#e2e8f0"            # رمادي فاتح جداً مريح للقراءة (أفتح من السابق)
NODE_COLORS = [NEON_BLUE, NEON_CYAN, "#ffffff"] # ألوان النقاط المنتثرة


class Particle:
    """كائن يمثل نقطة منتثرة في الفضاء"""
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        # سرعة بدائية بطيئة جداً لحركة هادئة
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.radius = radius
        self.color = QColor(random.choice(NODE_COLORS))
        self.color.setAlpha(random.randint(80, 200))


class DynamicCoreLogo(QWidget):
    """شعار النواة المضيء"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self.angle1 = 0
        self.angle2 = 360
        self.pulse = 0
        self.pulse_dir = 1
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)

    def _animate(self):
        self.angle1 = (self.angle1 + 1.2) % 360
        self.angle2 = (self.angle2 - 2.0) % 360
        self.pulse += 0.05 * self.pulse_dir
        if self.pulse > 5: self.pulse_dir = -1
        elif self.pulse < 0: self.pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        cx, cy = rect.width() / 2, rect.height() / 2

        # 1. الدائرة المركزية
        center_glow = QRadialGradient(cx, cy, 35 + self.pulse)
        center_glow.setColorAt(0, QColor(NEON_BLUE))
        center_glow.setColorAt(1, QColor(56, 189, 248, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(center_glow))
        p.drawEllipse(int(cx - 40), int(cy - 40), 80, 80)

        # 2. الحلقة الداخلية
        p.translate(cx, cy)
        p.rotate(self.angle1)
        pen1 = QPen(QColor(NEON_CYAN), 2.5)
        pen1.setDashPattern([15, 20, 35, 20])
        p.setPen(pen1)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(-50, -50, 100, 100)
        p.rotate(-self.angle1)

        # 3. الحلقة الخارجية
        p.rotate(self.angle2)
        pen2 = QPen(QColor(NEON_VIOLET), 1.5)
        pen2.setDashPattern([40, 20, 15, 20])
        p.setPen(pen2)
        p.drawEllipse(-70, -70, 140, 140)
        p.end()


class GlassCard(QFrame):
    """بطاقة زجاجية بألوان متناسقة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.current_border_color = QColor(255, 255, 255, 20)
        self.update_style()

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(350)
        self.anim.setStartValue(QColor(255, 255, 255, 20))
        self.anim.setEndValue(QColor(NEON_CYAN))
        self.anim.valueChanged.connect(self._on_color_change)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        # ظل أغمق قليلاً للتباين مع الخلفية التي أصبحت أفتح
        self.shadow.setColor(QColor(0, 0, 0, 90)) 
        self.shadow.setOffset(0, 8)
        self.setGraphicsEffect(self.shadow)

    def _on_color_change(self, color):
        self.current_border_color = color
        self.update_style()

    def update_style(self):
        c = self.current_border_color
        border_rgba = f"rgba({c.red()}, {c.green()}, {c.blue()}, {c.alpha()})"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {GLASS_BG};
                border-radius: 16px;
                border: 1px solid {border_rgba};
                border-top: 1px solid rgba(255, 255, 255, 40);
            }}
        """)

    def enterEvent(self, event):
        self.anim.setDirection(QAbstractAnimation.Direction.Forward)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.setDirection(QAbstractAnimation.Direction.Backward)
        self.anim.start()
        super().leaveEvent(event)


class PremiumButton(QPushButton):
    """زر مستقبلي بألوان فاتحة وساطعة"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(300, 60)
        self.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_MAIN};
                border-radius: 30px;
                border: 2px solid {NEON_CYAN};
            }}
            QPushButton:hover {{
                background-color: rgba(34, 211, 238, 0.15);
                border: 2px solid {NEON_BLUE};
                color: {NEON_BLUE};
            }}
            QPushButton:pressed {{
                background-color: rgba(34, 211, 238, 0.3);
            }}
        """)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(34, 211, 238, 70))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)


class WelcomeScreen(QWidget):
    """الشاشة الرئيسية"""
    def __init__(self, on_navigate, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self._labels = {}
        
        self.particles = []
        # زيادة تكرار المؤقت للحصول على فيزياء أنعم (اختياري، حالياً 60 إطار في الثانية)
        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self.update_physics)
        self.physics_timer.start(16)
        
        self._build()
        lang_manager.language_changed.connect(self._on_lang_changed)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.particles:
            area = self.width() * self.height()
            count = min(max(int(area / 18000), 25), 60) 
            for _ in range(count):
                x = random.randint(0, self.width())
                y = random.randint(0, self.height())
                r = random.randint(2, 6) 
                self.particles.append(Particle(x, y, r))

    def update_physics(self):
        # تتبع الماوس
        local_pos = self.mapFromGlobal(self.cursor().pos())
        mx, my = local_pos.x(), local_pos.y()
        mouse_inside = self.rect().contains(local_pos)

        for p in self.particles:
            # 1. التفاعل التنافري مع الماوس (Anti-gravity)
            if mouse_inside:
                dx = p.x - mx
                dy = p.y - my
                dist = math.hypot(dx, dy)
                if 0 < dist < 220: 
                    force = (220 - dist) / 220.0
                    p.vx += (dx / dist) * force * 1.5
                    p.vy += (dy / dist) * force * 1.5

            # ─── التحديث الجديد: حركة عشوائية مستمرة ───
            # إضافة قوى دفع عشوائية خفيفة جداً في كل إطار لضمان الحركة المستمرة
            # زدت الحدود هنا من 0.08 إلى 0.15 لضمان حيوية أكبر
            p.vx += random.uniform(-0.15, 0.15)
            p.vy += random.uniform(-0.15, 0.15)

            # 2. تحديث الموقع وتطبيق الاحتكاك
            p.x += p.vx
            p.y += p.vy
            # تم زيادة معامل الاحتكاك قليلاً (0.97 بدلاً من 0.94) للحفاظ على الزخم لفترة أطول
            p.vx *= 0.97 
            p.vy *= 0.97

            # 3. تحديد السرعة القصوى (للحفاظ على هدوء الحركة المنتثرة)
            speed = math.hypot(p.vx, p.vy)
            if speed > 2.5:
                p.vx = (p.vx / speed) * 2.5
                p.vy = (p.vy / speed) * 2.5

            # 4. الارتداد عن الحدود (Strict Boundary checking)
            margin = 5
            if p.x < margin or p.x > self.width() - margin:
                p.vx *= -1
                # تصحيح الموقع لضمان عدم التعلق خارج الحدود عند تصغير النافذة
                p.x = max(margin, min(p.x, self.width() - margin))
            if p.y < margin or p.y > self.height() - margin:
                p.vy *= -1
                p.y = max(margin, min(p.y, self.height() - margin))

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. تدرج الخلفية الليلية (الجديدة الأفتح)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(BG_TOP))
        gradient.setColorAt(1, QColor(BG_BOTTOM))
        p.fillRect(self.rect(), QBrush(gradient))

        # 2. الخطوط الشبكية (طويلة ومنتثرة)
        # تم زيادة الشفافية قليلاً للخطوط لتناسب الخلفية الأفتح
        p.setPen(QPen(QColor(56, 189, 248, 15), 1))
        for i, p1 in enumerate(self.particles):
            for p2 in self.particles[i+1:]:
                dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
                if dist < 220: 
                    # تدرج ناعم للشفافية بناءً على المسافة
                    alpha = int(120 * (1 - dist / 220))
                    p.setPen(QPen(QColor(56, 189, 248, alpha), 1.0))
                    p.drawLine(int(p1.x), int(p1.y), int(p2.x), int(p2.y))

        # 3. الجزيئات الطافية
        p.setPen(Qt.PenStyle.NoPen)
        for part in self.particles:
            p.setBrush(QBrush(part.color))
            p.drawEllipse(int(part.x - part.radius), int(part.y - part.radius), 
                          part.radius * 2, part.radius * 2)
        p.end()

    def _build(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(0)
        # تم زيادة الهامش العلوي قليلاً للتنفس
        layout.setContentsMargins(40, 60, 40, 60)

        # ─── اللوجو الديناميكي المتحرك ───
        logo = DynamicCoreLogo()
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(40)

        # ─── شارة النظام (System Badge) ───
        badge = QFrame()
        badge.setStyleSheet(f"background-color: rgba(34, 211, 238, 0.1); border: 1px solid {NEON_CYAN}; border-radius: 16px;")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(20, 8, 20, 8)
        badge_layout.setSpacing(10)

        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {NEON_CYAN}; border-radius: 5px; border: none;")
        
        dot_shadow = QGraphicsDropShadowEffect()
        dot_shadow.setBlurRadius(15)
        dot_shadow.setColor(QColor(NEON_CYAN))
        dot_shadow.setOffset(0, 0)
        dot.setGraphicsEffect(dot_shadow)

        self._labels["badge"] = QLabel(t("welcome_badge").upper())
        self._labels["badge"].setFont(QFont("Segoe UI", 10, QFont.Weight.Black))
        self._labels["badge"].setStyleSheet(f"color: {NEON_CYAN}; background: transparent; border: none; letter-spacing: 2px;")

        badge_layout.addWidget(dot)
        badge_layout.addWidget(self._labels["badge"])

        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(25)

        # ─── العنوان الرئيسي ───
        self._labels["title"] = QLabel(t("welcome_title"))
        self._labels["title"].setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        self._labels["title"].setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        self._labels["title"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._labels["title"])
        layout.addSpacing(15)

        # ─── الوصف ───
        self._labels["desc"] = QLabel(t("welcome_desc"))
        self._labels["desc"].setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        self._labels["desc"].setStyleSheet(f"color: {TEXT_SUB}; line-height: 1.6; background: transparent;")
        self._labels["desc"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._labels["desc"].setWordWrap(True)
        self._labels["desc"].setMaximumWidth(700)
        layout.addWidget(self._labels["desc"], alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(60)

        # ─── شبكة الميزات (Dark Glass Cards) ───
        features_widget = QWidget()
        features_widget.setStyleSheet("background: transparent;")
        features_grid = QGridLayout(features_widget)
        features_grid.setSpacing(30) # زيادة التباعد بين البطاقات لانتثار أفضل
        features_grid.setContentsMargins(0, 0, 0, 0)

        feat_keys = [
            ("🛡️", "feat1_title", "feat1_desc"),
            ("🧬", "feat2_title", "feat2_desc"),
            ("⚡", "feat3_title", "feat3_desc"),
        ]

        for i, (icon, title_key, desc_key) in enumerate(feat_keys):
            card = GlassCard()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(28, 32, 28, 32)
            card_layout.setSpacing(15)

            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI Emoji", 28))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft if lang_manager.align == Qt.AlignmentFlag.AlignLeft else Qt.AlignmentFlag.AlignRight)
            icon_label.setStyleSheet("background: transparent; border: none;")

            self._labels[f"ft{i}"] = QLabel(t(title_key))
            self._labels[f"ft{i}"].setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            self._labels[f"ft{i}"].setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")

            self._labels[f"fd{i}"] = QLabel(t(desc_key))
            self._labels[f"fd{i}"].setFont(QFont("Segoe UI", 11))
            # تم تعديل لون وصف البطاقة ليتناسب مع الخلفية الأفتح
            self._labels[f"fd{i}"].setStyleSheet(f"color: {TEXT_SUB}; background: transparent; border: none;")
            self._labels[f"fd{i}"].setWordWrap(True)

            card_layout.addWidget(icon_label, alignment=lang_manager.align)
            card_layout.addWidget(self._labels[f"ft{i}"])
            card_layout.addWidget(self._labels[f"fd{i}"])
            card_layout.addStretch()

            features_grid.addWidget(card, 0, 2 - i)

        layout.addWidget(features_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(70)

        # ─── زر البدء الفاخر ───
        self._start_btn = PremiumButton(t("welcome_btn"))
        self._start_btn.clicked.connect(lambda: self.on_navigate("cf"))
        layout.addWidget(self._start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        # مسافة إضافية في الأسفل للتمرير
        layout.addSpacing(40) 
        layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    def _on_lang_changed(self, lang):
        self._labels["badge"].setText(t("welcome_badge").upper())
        self._labels["title"].setText(t("welcome_title"))
        self._labels["desc"].setText(t("welcome_desc"))
        self._start_btn.setText(t("welcome_btn"))

        for i in range(3):
            self._labels[f"ft{i}"].setText(t(f"feat{i+1}_title"))
            self._labels[f"fd{i}"].setText(t(f"feat{i+1}_desc"))
            self._labels[f"ft{i}"].setAlignment(lang_manager.align)
            self._labels[f"fd{i}"].setAlignment(lang_manager.align)