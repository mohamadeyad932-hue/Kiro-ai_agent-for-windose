"""
Kiro AI - Processing Screen (PyQt6) - Bilingual
شاشة المعالجة مع شريط التقدم والتيرمنال
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QGridLayout,
                              QTextEdit, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QTextCursor
from datetime import datetime
from translations import lang_manager, t

# ── لوحة الألوان الموحدة ──────────────────────────────────────────
BG_DEEP     = "#020650"
BG_MID      = "#050F26"
CYAN        = "#00D2FF"
BLUE        = "#1A73E8"
VIOLET      = "#BD00FF"
EMERALD     = "#10B981"
TEXT_MAIN   = "#FFFFFF"
TEXT_SUB    = "#80A0C0"
GLASS       = "rgba(255, 255, 255, 0.05)"
BORDER_CYAN = "rgba(0, 210, 255, 0.4)"

# استيراد الرسائل من الثيم الأصلي أو تعريفها هنا إذا لزم الأمر
from theme import LOG_MESSAGES


class ProcRobotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 110)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = 55, 55
        
        # هالة خارجية
        glow = QColor(CYAN); glow.setAlpha(40)
        p.setPen(QPen(glow, 2, Qt.PenStyle.DashLine))
        p.drawEllipse(5, 5, 100, 100)
        
        # الجسم الزجاجي
        p.setPen(QPen(QColor(0, 210, 255, 80), 1.5))
        p.setBrush(QBrush(QColor(255, 255, 255, 15)))
        p.drawEllipse(15, 15, 80, 80)
        
        # عين الروبوت (Cyan Glow)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(CYAN)))
        p.drawRoundedRect(cx - 15, cy - 4, 30, 8, 4, 4)
        p.end()


class ProcessingScreen(QWidget):
    """شاشة المعالجة - شريط تقدم + خطوات + تيرمنال"""

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
        from PyQt6.QtGui import QRadialGradient, QLinearGradient
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        bg = QLinearGradient(0, 0, 0, H)
        bg.setColorAt(0.0, QColor(BG_DEEP)); bg.setColorAt(0.5, QColor(BG_MID)); bg.setColorAt(1.0, QColor(BG_DEEP))
        p.fillRect(self.rect(), QBrush(bg))
        cg = QRadialGradient(W/2, H*0.4, W*0.5)
        cg.setColorAt(0.0, QColor(0, 210, 255, 30)); cg.setColorAt(1.0, QColor(0, 210, 255, 0))
        p.fillRect(self.rect(), QBrush(cg))
        p.end()

    def _build(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(30, 20, 30, 20); self.main_layout.setSpacing(0)

        # ─── زر إعادة التعيين ───
        top_row = QHBoxLayout()
        self.reset_btn = QPushButton(t("proc_reset"))
        self.reset_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setFixedSize(160, 32)
        self.reset_btn.setStyleSheet(f"QPushButton {{ background: rgba(255, 255, 255, 0.05); color: #FF4D4D; border: 1px solid rgba(255, 77, 77, 0.3); border-radius: 6px; }} QPushButton:hover {{ background: rgba(255, 77, 77, 0.1); }}")
        self.reset_btn.clicked.connect(self.reset_proc)
        top_row.addWidget(self.reset_btn)
        top_row.addStretch()
        self.main_layout.addLayout(top_row)
        self.main_layout.addSpacing(10)

        robot = ProcRobotWidget()
        self.main_layout.addWidget(robot, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addSpacing(15)

        # ─── عناوين المعالجة ───
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
        self.main_layout.addSpacing(25)

        # ─── شريط التقدم ───
        self.progress = QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setRange(0, 100); self.progress.setValue(0); self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.08); border-radius: 5px; border: none; }} QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {CYAN}, stop:1 {BLUE}); border-radius: 5px; }}")
        self.main_layout.addWidget(self.progress)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.progress)
        self.main_layout.addSpacing(8)

        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
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

        # ─── خطوات المعالجة ───
        steps_widget = QWidget()
        steps_widget.setStyleSheet("background: transparent;")
        steps_grid = QGridLayout(steps_widget)
        steps_grid.setSpacing(10)
        steps_grid.setContentsMargins(5, 0, 5, 0)

        step_keys = [
            ("🔍", "proc_step1"),
            ("🧠", "proc_step2"),
            ("🧬", "proc_step3"),
            ("⚡", "proc_step4"),
        ]
        self.steps = []
        for i, (icon, key) in enumerate(step_keys):
            step_frame = QFrame()
            step_frame.setObjectName(f"step{i}")
            step_frame.setStyleSheet(f"QFrame#step{i} {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; }}")
            s_layout = QVBoxLayout(step_frame)
            s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s_layout.setContentsMargins(10, 15, 10, 15)

            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); icon_lbl.setStyleSheet("background:transparent;")
            s_layout.addWidget(icon_lbl)

            text_lbl = QLabel(t(key))
            text_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            text_lbl.setStyleSheet(f"color: {TEXT_SUB}; background:transparent;")
            text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s_layout.addWidget(text_lbl)

            steps_grid.addWidget(step_frame, 0, 3 - i)
            self.steps.append((step_frame, text_lbl, i, key))

        self.main_layout.addWidget(steps_widget)
        self.main_layout.addSpacing(20)
        self._set_step_style(0, CYAN)

        # ─── التيرمنال ───
        terminal = QFrame(); terminal.setObjectName("terminal")
        terminal.setStyleSheet(f"QFrame#terminal {{ background: rgba(0, 0, 0, 0.4); border-radius: 14px; border: 1px solid rgba(0, 210, 255, 0.15); }}")
        t_layout = QVBoxLayout(terminal); t_layout.setContentsMargins(0, 0, 0, 0); t_layout.setSpacing(0)

        term_top = QWidget(); term_top.setFixedHeight(34)
        term_top.setStyleSheet(f"background: rgba(0, 210, 255, 0.08); border-top-left-radius: 14px; border-top-right-radius: 14px;")
        tt_layout = QHBoxLayout(term_top); tt_layout.setContentsMargins(14, 0, 14, 0)

        tt_label = QLabel("KIRO AI >_ ANALYZER OUTPUT")
        tt_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold)); tt_label.setStyleSheet("color: #7090B0; background:transparent;")
        tt_layout.addStretch(); tt_layout.addWidget(tt_label)

        tt_dot = QFrame(); tt_dot.setFixedSize(6, 6)
        tt_dot.setStyleSheet(f"background-color: {CYAN}; border-radius: 3px;")
        tt_layout.addWidget(tt_dot); t_layout.addWidget(term_top)

        self.term_text = QTextEdit(); self.term_text.setReadOnly(True); self.term_text.setFont(QFont("Consolas", 10))
        self.term_text.setFixedHeight(180)
        self.term_text.setStyleSheet(f"QTextEdit {{ background: transparent; color: {CYAN}; border: none; padding: 12px; }}")
        t_layout.addWidget(self.term_text)

        term_container = QWidget()
        term_container.setStyleSheet("background: transparent;")
        tc_layout = QVBoxLayout(term_container)
        tc_layout.setContentsMargins(5, 0, 5, 0)
        tc_layout.addWidget(terminal)
        self.main_layout.addWidget(term_container)
        self.main_layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    def _set_step_style(self, index, color, bg_alpha=30):
        frame, lbl, i, _ = self.steps[index]
        frame.setStyleSheet(f"QFrame#step{i} {{ background: rgba(255, 255, 255, 0.08); border: 2px solid {color}; border-radius: 14px; }}")
        lbl.setStyleSheet(f"color: {color}; background: transparent;")

    def _reset_step_style(self, index):
        frame, lbl, i, _ = self.steps[index]
        frame.setStyleSheet(f"QFrame#step{i} {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; }}")
        lbl.setStyleSheet(f"color: {TEXT_SUB}; background: transparent;")

    def start_processing(self):
        self.reset_proc()
        self._step = 0
        self._timer.start(700)

    def _run_step(self):
        if self._step >= len(LOG_MESSAGES):
            self._timer.stop()
            QTimer.singleShot(1000, lambda: self.on_navigate("db"))
            return

        msg_type, msg = LOG_MESSAGES[self._step]
        total = len(LOG_MESSAGES)
        pct = round((self._step + 1) / total * 100)

        self.progress.setValue(pct)
        self.pct_label.setText(f"{pct}%")
        self.eta_label.setText("Processing...")

        pi = min(3, int(self._step / (total / 4)))
        phase_keys = [
            ("phase1_title", "phase1_sub"),
            ("phase2_title", "phase2_sub"),
            ("phase3_title", "phase3_sub"),
            ("phase4_title", "phase4_sub"),
        ]
        self._labels["proc_title"].setText(t(phase_keys[pi][0]))
        self._labels["proc_sub"].setText(t(phase_keys[pi][1]))

        for idx in range(len(self.steps)):
            if idx < pi:
                self._set_step_style(idx, EMERALD)
            elif idx == pi:
                self._set_step_style(idx, CYAN)
            else:
                self._reset_step_style(idx)

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.term_text.append(f"[{timestamp}]  {msg}")
        self.term_text.moveCursor(QTextCursor.MoveOperation.End)
        self._step += 1

    def reset_proc(self):
        self._timer.stop()
        self._step = 0
        self.progress.setValue(0)
        self.pct_label.setText("0%")
        self.eta_label.setText(t("proc_standby"))
        self._labels["proc_title"].setText(t("proc_ready"))
        self._labels["proc_sub"].setText(t("proc_waiting"))
        self.term_text.clear()
        for idx in range(len(self.steps)):
            self._reset_step_style(idx)
        self._set_step_style(0, CYAN)

    def _on_lang_changed(self, lang):
        self.reset_btn.setText(t("proc_reset"))
        for _, lbl, _, key in self.steps:
            lbl.setText(t(key))
        if self._step == 0:
            self._labels["proc_title"].setText(t("proc_ready"))
            self._labels["proc_sub"].setText(t("proc_waiting"))
