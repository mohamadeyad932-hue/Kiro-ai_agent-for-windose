"""
Kiro AI - Processing Screen (PyQt6) - Bilingual
شاشة المعالجة مع الوكيل العصبي المتطور
"""
import math
import random
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QScrollArea, QTextEdit, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QFont, QTextCursor, QPainter, QColor, QPen, QBrush, QRadialGradient

from translations import lang_manager, t
from theme import (
    CYAN, BLUE, TEXT_MAIN, TEXT_SUB, COLORS
)
from theme import LOG_MESSAGES

class NeuralAgentWidget(QWidget):
    """الكرة النابضة - تصميم القلب المتوهج مع مدارات سريعة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(240, 240)
        self.angle = 0
        self.pulse = 0
        self.is_finished = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16) # ~60 FPS

    def set_finished(self, finished=True):
        self.is_finished = finished
        self.update()

    def _animate(self):
        if not self.is_finished:
            self.angle = (self.angle + 8) % 360 # سرعة دوران المدارات
            self.pulse = (self.pulse + 0.12) % (math.pi * 2) # نبض الكرة
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W / 2, H / 2
        p.translate(cx, cy)
        
        pulse_scale = (math.sin(self.pulse) + 1) / 2
        
        # 1. المركز النابض (كرة زجاجية متوهجة)
        core_color = QColor(0, 255, 127) if self.is_finished else QColor(0, 255, 255)
        blue_fade = QColor(0, 200, 100, 200) if self.is_finished else QColor(0, 150, 255, 200)
        
        grad = QRadialGradient(0, 0, 50)
        grad.setColorAt(0.0, core_color)
        grad.setColorAt(0.4, blue_fade)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        core_radius = 45 if self.is_finished else (40 + pulse_scale * 15)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-core_radius), int(-core_radius), int(core_radius * 2), int(core_radius * 2))
        
        if self.is_finished:
            # رسم علامة صح (Checkmark)
            p.setPen(QPen(Qt.GlobalColor.white, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawLine(-15, 0, -5, 10)
            p.drawLine(-5, 10, 18, -12)
        else:
            # إضافة لمعة بيضاء صغيرة في المركز
            p.setBrush(QBrush(QColor(255, 255, 255, 180)))
            p.drawEllipse(-8, -8, 16, 16)

        # 2. الخطوط الدائرية الدوارة (Orbital HUD Rings)
        num_rings = 3
        for i in range(num_rings):
            p.save()
            # تدوير كل حلقة بسرعة واتجاه مختلفين (ثابتة إذا انتهى العمل)
            rotation = self.angle * (1.2 + i * 0.4) * (-1 if i % 2 == 0 else 1)
            p.rotate(rotation)
            
            radius = 65 + i * 18
            ring_color = QColor(0, 255, 127, 150 - i * 30) if self.is_finished else QColor(0, 240, 255, 150 - i * 30)
            pen = QPen(ring_color)
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            
            # رسم أقواس متقطعة بدلاً من دوائر كاملة
            p.drawArc(int(-radius), int(-radius), int(radius*2), int(radius*2), 0, 100 * 16)
            p.drawArc(int(-radius), int(-radius), int(radius*2), int(radius*2), 160 * 16, 60 * 16)
            p.drawArc(int(-radius), int(-radius), int(radius*2), int(radius*2), 260 * 16, 30 * 16)
            
            if not self.is_finished:
                # جزيئة ساطعة تتبع مسار كل حلقة
                p.setBrush(QBrush(QColor(255, 255, 255, 220)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(int(radius - 3), -3, 6, 6)
            
            p.restore()
        
        p.end()

class ProcessingScreen(QWidget):
    def __init__(self, on_navigate, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self._timer = QTimer()
        self._timer.timeout.connect(self._run_step)
        self._step = 0
        self.setStyleSheet("background: transparent;")
        self._labels = {}
        self._build()
        lang_manager.language_changed.connect(self._on_lang_changed)

    def paintEvent(self, event):
        from theme import paint_bg
        paint_bg(self)

    def _build(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(0)

        # 1. العناوين
        self._labels["proc_title"] = QLabel(t("proc_title_init"))
        self._labels["proc_title"].setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._labels["proc_title"].setStyleSheet(f"color: {TEXT_MAIN};")
        self._labels["proc_title"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self._labels["proc_title"])
        self.main_layout.addSpacing(6)

        self._labels["proc_sub"] = QLabel(t("proc_sub_init"))
        self._labels["proc_sub"].setFont(QFont("Segoe UI", 12))
        self._labels["proc_sub"].setStyleSheet(f"color: {CYAN};")
        self._labels["proc_sub"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self._labels["proc_sub"])
        self.main_layout.addSpacing(10)

        # 2. الوكيل العصبي
        self.agent_container = QWidget()
        agent_layout = QHBoxLayout(self.agent_container)
        agent_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.neural_agent = NeuralAgentWidget()
        agent_layout.addWidget(self.neural_agent)
        self.main_layout.addWidget(self.agent_container)
        self.main_layout.addSpacing(10)

        # 3. شريط التقدم
        self.progress = QProgressBar()
        self.progress.setFixedHeight(12)
        self.progress.setRange(0, 100); self.progress.setValue(0); self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00F0FF, 
                    stop:0.5 #00D4FF, 
                    stop:1 #0080FF);
                border-radius: 5px;
            }}
        """)
        
        # إضافة تأثير توهج نيوني (Neon Glow)
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(0, 240, 255, 100))
        glow.setOffset(0, 0)
        self.progress.setGraphicsEffect(glow)
        
        self.main_layout.addWidget(self.progress)
        self.main_layout.addSpacing(12)

        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent")
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(30, 0, 30, 0)
        self.pct_label = QLabel("0%")
        self.pct_label.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self.pct_label.setStyleSheet(f"color: {CYAN};")
        self.eta_label = QLabel(t("proc_standby"))
        self.eta_label.setFont(QFont("Segoe UI", 10))
        self.eta_label.setStyleSheet(f"color: {TEXT_SUB};")
        info_layout.addWidget(self.pct_label)
        info_layout.addStretch()
        info_layout.addWidget(self.eta_label)
        self.main_layout.addWidget(info_widget)
        self.main_layout.addSpacing(20)

        # 4. التيرمنال
        terminal = QFrame(); terminal.setObjectName("terminal")
        terminal.setStyleSheet(f"QFrame#terminal {{ background: #000000; border-radius: 14px; border: 1px solid rgba(0, 240, 255, 0.3); }}")
        t_layout = QVBoxLayout(terminal); t_layout.setContentsMargins(0, 0, 0, 0); t_layout.setSpacing(0)
        term_top = QWidget(); term_top.setFixedHeight(34)
        term_top.setStyleSheet(f"background: #111111; border-top-left-radius: 14px; border-top-right-radius: 14px; border-bottom: 1px solid rgba(0, 240, 255, 0.1);")
        tt_layout = QHBoxLayout(term_top); tt_layout.setContentsMargins(14, 0, 14, 0)
        tt_label = QLabel("KIRO AI >_ ANALYZER OUTPUT")
        tt_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold)); tt_label.setStyleSheet(f"color: {COLORS['terminal_txt']}; background:transparent;")
        tt_layout.addStretch(); tt_layout.addWidget(tt_label)
        tt_dot = QFrame(); tt_dot.setFixedSize(6, 6); tt_dot.setStyleSheet(f"background-color: {COLORS['terminal_txt']}; border-radius: 3px;")
        tt_layout.addWidget(tt_dot); t_layout.addWidget(term_top)
        self.term_text = QTextEdit(); self.term_text.setReadOnly(True); self.term_text.setFont(QFont("Consolas", 10))
        self.term_text.setFixedHeight(180)
        self.term_text.setStyleSheet(f"QTextEdit {{ background: transparent; color: {COLORS['terminal_txt']}; border: none; padding: 12px; }}")
        t_layout.addWidget(self.term_text)
        self.main_layout.addWidget(terminal)
        self.main_layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    def start_processing(self):
        self.reset_proc()
        self._step = 0
        self._timer.start(700)

    def _run_step(self):
        if self._step >= len(LOG_MESSAGES):
            self._timer.stop()
            self.neural_agent.set_finished(True) # تحويل الأيقونة لعلامة صح
            QTimer.singleShot(1500, lambda: self.on_navigate("db"))
            return
        msg_type, msg = LOG_MESSAGES[self._step]
        pct = round((self._step + 1) / len(LOG_MESSAGES) * 100)
        self.progress.setValue(pct)
        self.pct_label.setText(f"{pct}%")
        self.eta_label.setText("Processing...")
        pi = min(3, int(self._step / (len(LOG_MESSAGES) / 4)))
        phase_keys = [("phase1_title", "phase1_sub"), ("phase2_title", "phase2_sub"), ("phase3_title", "phase3_sub"), ("phase4_title", "phase4_sub")]
        self._labels["proc_title"].setText(t(phase_keys[pi][0]))
        self._labels["proc_sub"].setText(t(phase_keys[pi][1]))
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.term_text.append(f"[{timestamp}]  {msg}")
        self.term_text.moveCursor(QTextCursor.MoveOperation.End)
        self._step += 1

    def reset_proc(self):
        self._timer.stop()
        self._step = 0
        self.progress.setValue(0)
        self.pct_label.setText("0%")
        self.term_text.clear()
        self.neural_agent.set_finished(False) # إعادة الأيقونة لوضع الدوران
        self._labels["proc_title"].setText(t("proc_ready"))
        self._labels["proc_sub"].setText(t("proc_waiting"))

    def _on_lang_changed(self, lang):
        if self._step == 0:
            self._labels["proc_title"].setText(t("proc_ready"))
            self._labels["proc_sub"].setText(t("proc_waiting"))
