"""
Kiro AI - Processing Screen (PyQt6) - Bilingual
شاشة المعالجة مع تشغيل الـ Pipeline الحقيقي عبر QThread
"""
import math
import os
import sys
import subprocess
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QScrollArea, QTextEdit, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QPainter, QColor, QPen, QBrush, QRadialGradient

from translations import lang_manager, t
from theme import CYAN, BLUE, TEXT_MAIN, TEXT_SUB, COLORS


# ═══════════════════════════════════════════════════════════════
#  Worker Thread - يشغل الـ Pipeline في الخلفية
# ═══════════════════════════════════════════════════════════════

class PipelineWorker(QThread):
    """
    يشغل pipeline التنظيم الحقيقي بالكامل في thread منفصل
    حتى لا تتجمد الواجهة أثناء المعالجة.
    """
    log_signal    = pyqtSignal(str)        # رسالة جديدة للتيرمنال
    progress_signal = pyqtSignal(int)      # نسبة تقدم (0-100)
    phase_signal  = pyqtSignal(int)        # رقم المرحلة (0-3)
    finished_signal = pyqtSignal(bool, str)  # (نجح؟, رسالة الخطأ)

    def __init__(self, target_paths: list, mode: str, base_dir: str, parent=None):
        """
        target_paths : قائمة المسارات المختارة من شاشة التهيئة
        mode         : 'all' | 'text' | 'images'
        base_dir     : المجلد الجذر للمشروع (حيث توجد سكريبتات run_project.py)
        """
        super().__init__(parent)
        self.target_paths = target_paths
        self.mode = mode
        self.base_dir = base_dir
        self._abort = False

    def abort(self):
        self._abort = True

    # ─── خطوات الـ Pipeline ───

    def _run_script(self, script_dir: str, script_name: str, custom_path: str = None) -> bool:
        """تشغيل سكريبت واحد وإعادة stdout سطراً بسطر إلى الـ UI"""
        script_path = os.path.join(script_dir, script_name)
        if not os.path.exists(script_path):
            self.log_signal.emit(f"[!] File not found: {script_path}")
            return False

        command = [sys.executable, "-u", script_name]
        if custom_path:
            command.append(custom_path)
            self.log_signal.emit(f"[*] Path: {custom_path}")

        try:
            process = subprocess.Popen(
                command,
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if process.stdout:
                for line in process.stdout:
                    if self._abort:
                        process.terminate()
                        return False
                    line = line.rstrip()
                    if line:
                        self.log_signal.emit(line)
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.log_signal.emit(f"[!] Error: {e}")
            return False

    def _process_text(self, path: str) -> bool:
        steps = [
            ("Processing text files", "files_Embedder.py"),
            ("clustring_files",       "clustring_file_text.py"),
        ]
        for folder, script in steps:
            if self._abort:
                return False
            script_dir = os.path.join(self.base_dir, folder)
            self.log_signal.emit(f">> Running: {script}")
            if not self._run_script(script_dir, script, path):
                return False
        return True

    def _process_images(self, path: str) -> bool:
        steps = [
            ("Processing image",  "images_caption_Embedder.py"),
            ("clustring_imge",    "clustring_image_captions.py"),
        ]
        for folder, script in steps:
            if self._abort:
                return False
            script_dir = os.path.join(self.base_dir, folder)
            self.log_signal.emit(f">> Running: {script}")
            if not self._run_script(script_dir, script, path):
                return False
        return True

    def _organize_text(self) -> bool:
        folder = os.path.join(self.base_dir, "creat folders for flie_text  and name")
        self.log_signal.emit(">> Running: semantic_folder_creator.py")
        return self._run_script(folder, "semantic_folder_creator.py")

    def _organize_images(self) -> bool:
        folder = os.path.join(self.base_dir, "creat folders for image and name")
        self.log_signal.emit(">> Running: main_image_converter.py")
        return self._run_script(folder, "main_image_converter.py")

    # ─── الـ run الرئيسي ───

    def run(self):
        """
        تشغيل run_project.py كعملية فرعية وتمرير المسارات والوضع المختار.
        """
        try:
            self.phase_signal.emit(0)
            self.log_signal.emit("=" * 50)
            self.log_signal.emit("[ KIRO AI ] Starting External Project Runner...")
            self.log_signal.emit(f"[ INFO ] Mode : {self.mode.upper()}")
            
            # Read GPU settings
            from PyQt6.QtCore import QSettings
            settings = QSettings("KiroAI", "Settings")
            use_gpu = settings.value("gpu_acceleration", True, type=bool)
            
            env = os.environ.copy()
            if not use_gpu:
                env["CUDA_VISIBLE_DEVICES"] = ""
                self.log_signal.emit("[ INFO ] GPU Acceleration : DISABLED (CPU Only)")
            else:
                self.log_signal.emit("[ INFO ] GPU Acceleration : ENABLED")
                
            self.log_signal.emit("=" * 50)
            
            # بناء الأمر
            # نستخدم sys.executable لضمان استخدام نفس بيئة بايثون
            script_path = os.path.join(self.base_dir, "..", "run_project.py")
            if not os.path.exists(script_path):
                # ربما base_dir هو بالفعل المجلد الرئيسي (حيث يوجد main.py و run_project.py)
                script_path = os.path.join(self.base_dir, "run_project.py")
            
            # إذا لم يتم العثور عليه، نحاول في المجلد الأب (لأن main.py في uiux_kiro_pyqt)
            if not os.path.exists(script_path):
                parent_dir = os.path.dirname(self.base_dir)
                script_path = os.path.join(parent_dir, "run_project.py")

            command = [sys.executable, "-u", script_path, "--mode", self.mode]
            for p in self.target_paths:
                command.extend(["--path", p])

            self.log_signal.emit(f"[*] Command: {' '.join(command)}")
            
            process = subprocess.Popen(
                command,
                cwd=os.path.dirname(script_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1, # Line buffered
                env=env
            )

            if process.stdout:
                for line in process.stdout:
                    if self._abort:
                        process.terminate()
                        self.finished_signal.emit(False, "Aborted by user")
                        return
                    
                    line = line.rstrip()
                    if line:
                        self.log_signal.emit(line)
                        
                        # تحديث وهمي للمراحل بناءً على مخرجات السكريبت
                        if "Collecting Text Data" in line or "Collecting Image Data" in line:
                            self.phase_signal.emit(1)
                            self.progress_signal.emit(20)
                        elif "Merging and clustering" in line or "Clustering" in line:
                            self.phase_signal.emit(2)
                            self.progress_signal.emit(60)
                        elif "FINAL STEP: Organizing" in line:
                            self.phase_signal.emit(3)
                            self.progress_signal.emit(90)

            process.wait()
            
            if process.returncode == 0:
                self.progress_signal.emit(100)
                self.log_signal.emit("\n[ DONE ] run_project.py finished successfully ✓")
                self.finished_signal.emit(True, "")
            else:
                self.finished_signal.emit(False, f"run_project.py failed with code {process.returncode}")

        except Exception as e:
            self.log_signal.emit(f"\n[CRITICAL] Unexpected error: {e}")
            self.finished_signal.emit(False, str(e))


# ═══════════════════════════════════════════════════════════════
#  النبضة البصرية
# ═══════════════════════════════════════════════════════════════

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
        self.timer.start(16)

    def set_finished(self, finished=True):
        self.is_finished = finished
        self.update()

    def _animate(self):
        if not self.is_finished:
            self.angle = (self.angle + 8) % 360
            self.pulse = (self.pulse + 0.12) % (math.pi * 2)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W / 2, H / 2
        p.translate(cx, cy)

        pulse_scale = (math.sin(self.pulse) + 1) / 2

        core_color = QColor(0, 255, 127) if self.is_finished else QColor(0, 255, 255)
        blue_fade  = QColor(0, 200, 100, 200) if self.is_finished else QColor(0, 150, 255, 200)

        grad = QRadialGradient(0, 0, 50)
        grad.setColorAt(0.0, core_color)
        grad.setColorAt(0.4, blue_fade)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        core_radius = 45 if self.is_finished else (40 + pulse_scale * 15)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-core_radius), int(-core_radius), int(core_radius * 2), int(core_radius * 2))

        if self.is_finished:
            p.setPen(QPen(Qt.GlobalColor.white, 5, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawLine(-15, 0, -5, 10)
            p.drawLine(-5, 10, 18, -12)
        else:
            p.setBrush(QBrush(QColor(255, 255, 255, 180)))
            p.drawEllipse(-8, -8, 16, 16)

        num_rings = 3
        for i in range(num_rings):
            p.save()
            rotation = self.angle * (1.2 + i * 0.4) * (-1 if i % 2 == 0 else 1)
            p.rotate(rotation)
            radius = 65 + i * 18
            ring_color = QColor(0, 255, 127, 150 - i * 30) if self.is_finished else QColor(0, 240, 255, 150 - i * 30)
            pen = QPen(ring_color)
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(int(-radius), int(-radius), int(radius*2), int(radius*2), 0, 100 * 16)
            p.drawArc(int(-radius), int(-radius), int(radius*2), int(radius*2), 160 * 16, 60 * 16)
            p.drawArc(int(-radius), int(-radius), int(radius*2), int(radius*2), 260 * 16, 30 * 16)
            if not self.is_finished:
                p.setBrush(QBrush(QColor(255, 255, 255, 220)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(int(radius - 3), -3, 6, 6)
            p.restore()

        p.end()


# ═══════════════════════════════════════════════════════════════
#  شاشة المعالجة
# ═══════════════════════════════════════════════════════════════

class ProcessingScreen(QWidget):
    def __init__(self, on_navigate, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self._worker: PipelineWorker | None = None
        self.setStyleSheet("background: transparent;")
        self._labels = {}
        self._build()
        lang_manager.language_changed.connect(self._on_lang_changed)

    def paintEvent(self, event):
        from theme import paint_bg
        paint_bg(self)

    # ─── بناء الواجهة ───

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

        # العناوين
        self._labels["proc_title"] = QLabel(t("proc_title_init") if "proc_title_init" in dir() else "Kiro AI")
        self._labels["proc_title"].setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._labels["proc_title"].setStyleSheet(f"color: {TEXT_MAIN};")
        self._labels["proc_title"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self._labels["proc_title"])
        self.main_layout.addSpacing(6)

        self._labels["proc_sub"] = QLabel("")
        self._labels["proc_sub"].setFont(QFont("Segoe UI", 12))
        self._labels["proc_sub"].setStyleSheet(f"color: {CYAN};")
        self._labels["proc_sub"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self._labels["proc_sub"])
        self.main_layout.addSpacing(10)

        # الوكيل العصبي
        agent_container = QWidget()
        agent_layout = QHBoxLayout(agent_container)
        agent_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.neural_agent = NeuralAgentWidget()
        agent_layout.addWidget(self.neural_agent)
        self.main_layout.addWidget(agent_container)
        self.main_layout.addSpacing(10)

        # شريط التقدم
        self.progress = QProgressBar()
        self.progress.setFixedHeight(12)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00F0FF, stop:0.5 #00D4FF, stop:1 #0080FF);
                border-radius: 5px;
            }}
        """)
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
        self.eta_label = QLabel("Standby")
        self.eta_label.setFont(QFont("Segoe UI", 10))
        self.eta_label.setStyleSheet(f"color: {TEXT_SUB};")
        info_layout.addWidget(self.pct_label)
        info_layout.addStretch()
        info_layout.addWidget(self.eta_label)
        self.main_layout.addWidget(info_widget)
        self.main_layout.addSpacing(20)

        # التيرمنال
        terminal = QFrame()
        terminal.setObjectName("terminal")
        terminal.setStyleSheet(
            "QFrame#terminal { background: #000000; border-radius: 14px;"
            " border: 1px solid rgba(0, 240, 255, 0.3); }"
        )
        t_layout = QVBoxLayout(terminal)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(0)

        term_top = QWidget()
        term_top.setFixedHeight(34)
        term_top.setStyleSheet(
            f"background: #111111; border-top-left-radius: 14px;"
            f" border-top-right-radius: 14px;"
            f" border-bottom: 1px solid rgba(0, 240, 255, 0.1);"
        )
        tt_layout = QHBoxLayout(term_top)
        tt_layout.setContentsMargins(14, 0, 14, 0)
        tt_label = QLabel("KIRO AI >_ ANALYZER OUTPUT")
        tt_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        tt_label.setStyleSheet(f"color: {COLORS['terminal_txt']}; background:transparent;")
        tt_layout.addStretch()
        tt_layout.addWidget(tt_label)
        tt_dot = QFrame()
        tt_dot.setFixedSize(6, 6)
        tt_dot.setStyleSheet(f"background-color: {COLORS['terminal_txt']}; border-radius: 3px;")
        tt_layout.addWidget(tt_dot)
        t_layout.addWidget(term_top)

        self.term_text = QTextEdit()
        self.term_text.setReadOnly(True)
        self.term_text.setFont(QFont("Consolas", 10))
        self.term_text.setFixedHeight(200)
        self.term_text.setStyleSheet(
            f"QTextEdit {{ background: transparent; color: {COLORS['terminal_txt']};"
            f" border: none; padding: 12px; }}"
        )
        t_layout.addWidget(self.term_text)
        self.main_layout.addWidget(terminal)
        self.main_layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    # ─── واجهة عامة ───

    def start_processing(self, target_paths: list = None, mode: str = "all"):
        """
        استدعاء من main.py عند الانتقال لشاشة المعالجة.
        target_paths : قائمة المسارات المختارة
        mode         : 'all' | 'text' | 'images'
        """
        self._reset()

        if not target_paths:
            self._log("[!] No paths provided to pipeline.")
            return

        # تحديد المجلد الجذر للمشروع (نفس مكان main.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # مسح نتائج الجلسة السابقة لضمان عرض نتيجة هذه العملية فقط في لوحة التحكم
        json_path = os.path.join(os.path.dirname(base_dir), "created_folders.json")
        if os.path.exists(json_path):
            try:
                os.remove(json_path)
            except Exception as e:
                self._log(f"[!] Failed to clear previous results: {e}")

        self._labels["proc_title"].setText(t("phase1_title"))
        self._labels["proc_sub"].setText(t("phase1_sub"))
        self.eta_label.setText("Processing...")
        
        # ضبط شريط التقدم لوضع الحركة اللانهائية (Indeterminate)
        self.progress.setRange(0, 0)
        self.pct_label.setText("") 

        self._worker = PipelineWorker(target_paths, mode, base_dir)
        self._worker.log_signal.connect(self._log)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.phase_signal.connect(self._on_phase)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    def _reset(self):
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait()
        self._worker = None
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.pct_label.setText("0%")
        self.eta_label.setText("Standby")
        self.term_text.clear()
        self.neural_agent.set_finished(False)
        self._labels["proc_title"].setText(t("phase1_title"))
        self._labels["proc_sub"].setText(t("phase1_sub"))

    # ─── Slots ───

    def _log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.term_text.append(f"[{timestamp}]  {msg}")
        self.term_text.moveCursor(QTextCursor.MoveOperation.End)

    def _on_progress(self, pct: int):
        # لا نعرض النسبة أثناء العمل كما طلب المستخدم، فقط نترك الشريط يتحرك
        pass

    def _on_phase(self, phase: int):
        phase_keys = [
            ("phase1_title", "phase1_sub"),
            ("phase2_title", "phase2_sub"),
            ("phase3_title", "phase3_sub"),
            ("phase4_title", "phase4_sub"),
        ]
        k = phase_keys[min(phase, 3)]
        # نبقي العنوان دائماً "جاري العمل" أثناء المعالجة كما طلب المستخدم
        self._labels["proc_title"].setText(t("phase1_title")) 
        self._labels["proc_sub"].setText(t(k[1]))

    def _on_finished(self, success: bool, error_msg: str):
        if success:
            self.neural_agent.set_finished(True)
            self.progress.setRange(0, 100) # إعادة الوضع العادي
            self.progress.setValue(100)
            self.pct_label.setText("100%")
            self.eta_label.setText("Done ✓")
            self._labels["proc_title"].setText(t("phase4_title"))
            self._labels["proc_sub"].setText(t("phase4_sub"))
            # الانتقال للداشبورد بعد ثانية ونصف
            QTimer.singleShot(1500, lambda: self.on_navigate("db"))
        else:
            self.eta_label.setText("Error ✗")
            self._labels["proc_title"].setText("Pipeline Error")
            self._labels["proc_sub"].setText(error_msg or "An error occurred.")
            self._log(f"\n[FAILED] {error_msg}")

    def _on_lang_changed(self, lang):
        pass  # العناوين تُحدَّث عبر phase_signal أثناء التشغيل