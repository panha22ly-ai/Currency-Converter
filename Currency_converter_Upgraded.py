import sys, requests, threading, pyttsx3

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont

API_KEY = "6a7a07c1637336349edd7a7b"


class CyberCurrencyOS(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Global Currency Converter")
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)

        # ================= CORE =================
        self.currency_data = {}
        self.full_list = []
        self.active_field = None
        self.selected_index = -1

        # ================= TTS =================
        self.tts_enabled = True
        self.tts_rate = 180
        self.tts_queue = []
        self.tts_busy = False

        # =========================================================
        # ROOT
        # =========================================================
        root = QHBoxLayout(self)

        # =========================================================
        # SETTINGS PANEL
        # =========================================================
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        side = QVBoxLayout(self.sidebar)

        side.addWidget(QLabel("SETTINGS"))

        self.font_box = QComboBox()
        self.font_box.addItems(["Arial", "Verdana", "Courier New"])

        self.big_text_toggle = QCheckBox("Big Text Mode")

        self.voice_toggle = QCheckBox("Enable Voice")
        self.voice_toggle.setChecked(True)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(250)
        self.speed_slider.setValue(self.tts_rate)

        self.stop_voice_btn = QPushButton("Stop Voice")
        self.clear_queue_btn = QPushButton("Clear Queue")

        side.addWidget(self.font_box)
        side.addWidget(self.big_text_toggle)
        side.addWidget(self.voice_toggle)
        side.addWidget(QLabel("Voice Speed"))
        side.addWidget(self.speed_slider)
        side.addWidget(self.stop_voice_btn)
        side.addWidget(self.clear_queue_btn)
        side.addStretch()

        # =========================================================
        # MAIN PANEL
        # =========================================================
        self.main_panel = QWidget()
        main = QVBoxLayout(self.main_panel)

        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Enter amount")

        self.from_input = QLineEdit()
        self.from_btn = QPushButton("▼")
        self.from_btn.setFixedWidth(45)

        row1 = QHBoxLayout()
        row1.addWidget(self.from_input)
        row1.addWidget(self.from_btn)

        self.to_input = QLineEdit()
        self.to_btn = QPushButton("▼")
        self.to_btn.setFixedWidth(45)

        row2 = QHBoxLayout()
        row2.addWidget(self.to_input)
        row2.addWidget(self.to_btn)

        self.convert_btn = QPushButton("CONVERT")

        self.result = QLabel("Result will appear here")
        self.rate = QLabel("Rate will appear here")
        self.history = QListWidget()

        main.addWidget(self.amount)
        main.addLayout(row1)
        main.addLayout(row2)
        main.addWidget(self.convert_btn)
        main.addWidget(self.result)
        main.addWidget(self.rate)
        main.addWidget(self.history)

        root.addWidget(self.sidebar)
        root.addWidget(self.main_panel)

        # =========================================================
        # DROPDOWN PANEL
        # =========================================================
        self.dropdown = QFrame(self)
        self.dropdown.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.dropdown.setAttribute(Qt.WA_TranslucentBackground)

        dl = QVBoxLayout(self.dropdown)

        self.search = QLineEdit()
        self.currency_list = QListWidget()

        dl.addWidget(self.search)
        dl.addWidget(self.currency_list)

        self.dropdown.setFixedSize(340, 260)
        self.dropdown.hide()

        # =========================================================
        # SIGNALS
        # =========================================================
        self.convert_btn.clicked.connect(self.convert_currency)

        self.from_btn.clicked.connect(lambda: self.open_dropdown("from"))
        self.to_btn.clicked.connect(lambda: self.open_dropdown("to"))

        self.currency_list.itemClicked.connect(self.select_currency)
        self.search.textChanged.connect(self.filter_list)

        self.big_text_toggle.toggled.connect(self.toggle_big_text)

        self.voice_toggle.toggled.connect(self.toggle_voice)
        self.speed_slider.valueChanged.connect(self.update_speed)

        self.stop_voice_btn.clicked.connect(self.stop_voice)
        self.clear_queue_btn.clicked.connect(self.clear_queue)

        self.font_box.currentTextChanged.connect(self.change_font)

        # =========================================================
        # INIT
        # =========================================================
        self.load_currencies()
        self.apply_cyber_dark()

    # =========================================================
    # 🌑 THEME
    # =========================================================
    def apply_cyber_dark(self):
        self.base_style = """
            QWidget {
                background-color: #070b14;
                color: #cfe3ff;
                font-size: 14px;
            }

            QPushButton {
                background-color: #1b3b6f;
                border-radius: 6px;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #2d6cff;
            }

            QLineEdit, QListWidget {
                background-color: #0f1a2e;
                border: 1px solid #1f3b66;
                padding: 6px;
                border-radius: 6px;
            }

            QListWidget::item {
                padding: 8px;
            }

            QListWidget::item:hover {
                background-color: #1b3b6f;
            }

            QListWidget::item:selected {
                background-color: #2d6cff;
            }
        """
        self.setStyleSheet(self.base_style)

    # =========================================================
    # 💸 CONVERT
    # =========================================================
    def convert_currency(self):
        try:
            amount = float(self.amount.text())

            from_code = self.extract(self.from_input.text())
            to_code = self.extract(self.to_input.text())

            url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_code}/{to_code}/{amount}"
            data = requests.get(url).json()

            result = data.get("conversion_result", 0)

            text = f"{amount} {from_code} = {result} {to_code}"

            if amount != 0:
                unit_rate = result / amount
            else:
                unit_rate = 0

            rate_text = f"1 {from_code} = {unit_rate:.4f} {to_code}"

            self.result.setText(text)
            self.rate.setText(rate_text)
            self.history.addItem(text)

            self.queue_speech(text)

        except:
            self.result.setText("Error converting")

    # =========================================================
    # 🪟 DROPDOWN
    # =========================================================
    def open_dropdown(self, field):
        self.active_field = field
        self.selected_index = -1

        self.currency_list.clear()
        self.currency_list.addItems(self.full_list)

        widget = self.from_input if field == "from" else self.to_input

        pos = widget.mapToGlobal(widget.rect().bottomLeft())
        self.dropdown.move(pos)

        self.search.clear()
        self.dropdown.show()

        self.animate_dropdown()

    def animate_dropdown(self):
        self.dropdown.setWindowOpacity(0)

        self.anim = QPropertyAnimation(self.dropdown, b"geometry")
        self.anim.setDuration(160)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.anim.setStartValue(QRect(self.dropdown.x(), self.dropdown.y() - 10,
                                      self.dropdown.width(), self.dropdown.height()))
        self.anim.setEndValue(QRect(self.dropdown.x(), self.dropdown.y(),
                                    self.dropdown.width(), self.dropdown.height()))
        self.anim.start()

        self.fade = QPropertyAnimation(self.dropdown, b"windowOpacity")
        self.fade.setDuration(160)
        self.fade.setStartValue(0)
        self.fade.setEndValue(1)
        self.fade.start()

    # =========================================================
    # 🔍 FILTER
    # =========================================================
    def filter_list(self, text):
        self.currency_list.clear()
        for item in self.full_list:
            if text.lower() in item.lower():
                self.currency_list.addItem(item)

    # =========================================================
    # 🎯 SELECT
    # =========================================================
    def select_currency(self, item):
        if self.active_field == "from":
            self.from_input.setText(item.text())
        else:
            self.to_input.setText(item.text())

        self.dropdown.hide()

    # =========================================================
    # 📡 LOAD
    # =========================================================
    def load_currencies(self):
        try:
            data = requests.get(
                f"https://v6.exchangerate-api.com/v6/{API_KEY}/codes"
            ).json()

            self.currency_data = {c: n for c, n in data.get("supported_codes", [])}

        except:
            self.currency_data = {"USD": "US Dollar", "EUR": "Euro"}

        self.full_list = [f"{n} ({c})" for c, n in self.currency_data.items()]

    # =========================================================
    # 🔧 HELPERS
    # =========================================================
    def extract(self, text):
        if "(" in text:
            return text.split("(")[-1].replace(")", "").strip()
        return text.strip()

    # =========================================================
    # 👓 BIG TEXT MODE (FIXED - NO CSS OVERRIDE CONFLICT)
    # =========================================================
    def toggle_big_text(self, state):
        if state:
            font_size = 24
        else:
            font_size = 14

        font = QFont("Arial", font_size)
        self.setFont(font)

        widgets = [
            self.amount,
            self.from_input,
            self.to_input,
            self.result,
            self.rate,
            self.history,
            self.search,
            self.convert_btn
        ]

        for w in widgets:
            w.setFont(font)

        # ⚡ CRITICAL FIX: DO NOT overwrite full stylesheet
        self.setStyleSheet(self.base_style + f"""
            QLineEdit, QListWidget {{
                font-size: {font_size}px;
            }}

            QLabel {{
                font-size: {font_size}px;
            }}

            QPushButton {{
                font-size: {font_size}px;
            }}
        """)

    # =========================================================
    # 🔤 FONT
    # =========================================================
    def change_font(self, font):
        self.setFont(QFont(font, 11))

    # =========================================================
    # 🎤 TTS
    # =========================================================
    def queue_speech(self, text):
        if not self.voice_toggle.isChecked():
            return

        self.tts_queue.append(text)
        if not self.tts_busy:
            self.process_queue()

    def process_queue(self):
        if not self.tts_queue:
            self.tts_busy = False
            return

        self.tts_busy = True
        text = self.tts_queue.pop(0)

        def run():
            engine = pyttsx3.init()
            engine.setProperty("rate", self.tts_rate)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            self.process_queue()

        threading.Thread(target=run, daemon=True).start()

    # =========================================================
    # VOICE CONTROLS
    # =========================================================
    def toggle_voice(self, state):
        self.tts_enabled = state

    def update_speed(self, value):
        self.tts_rate = value

    def stop_voice(self):
        self.tts_queue.clear()

    def clear_queue(self):
        self.tts_queue.clear()


# =========================================================
# RUN
# =========================================================
app = QApplication(sys.argv)
window = CyberCurrencyOS()
window.show()
sys.exit(app.exec_())