import sys
import sqlite3
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QFrame, QProgressBar)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPolygon
from PyQt5.QtCore import Qt, QPoint

# --- VERİTABANI KURULUMU ---
def init_db():
    conn = sqlite3.connect("yikim_filosu.db")
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS gemiler")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS murettebat (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        isim TEXT, soyisim TEXT, yildiz_kimlik TEXT UNIQUE)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS gemiler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        gemi_adi TEXT, kaptan TEXT, yakit INTEGER, 
                        kalkan INTEGER, silah_durumu TEXT, 
                        filo_sirasi INTEGER, murettebat_sayisi INTEGER)''')
    
   
    filo = [
        ("Kıyamet Sancaktarı", "Koramiral Vorgath", 100, 100, "Tam Güç", 0, 5000),
        ("Gölge Avcısı", "Kaptan Thalax", 85, 90, "Hazır", 1, 320),
        ("Plazma Fırtınası", "Kaptan Zephyrus", 90, 85, "Aşırı Yüklü", 2, 350),
        ("Yıldızların ışığı", "Kaptan Nova", 80, 80, "Saldırı Modu", 3, 300), 
        ("Yıldız Kıran", "Kaptan Mordred", 70, 75, "Hazır", 4, 310),
        ("Sonsuz Karanlık", "Kaptan Draven", 65, 70, "Bakımda", 5, 290),
        ("Demir Kıran", "Kaptan Ömer", 95, 95, "Tam Güç", 6, 320),
        ("Nebula Celladı", "Kaptan Xylos", 88, 90, "Hazır", 7, 300),
        ("Kızıl Şafak", "Kaptan Solaris", 82, 85, "Hazır", 8, 315),
        ("Sessiz Ölüm", "Kaptan Nyx", 78, 80, "Kalkan Modu", 9, 295),
    ]
    cursor.executemany("INSERT INTO gemiler (gemi_adi, kaptan, yakit, kalkan, silah_durumu, filo_sirasi, murettebat_sayisi) VALUES (?, ?, ?, ?, ?, ?, ?)", filo)
    
    conn.commit()
    conn.close()

# --- STİL VE ARKA PLAN ---
STYLE_SHEET = """
    QPushButton {
        background-color: rgba(20, 30, 50, 220);
        color: #00e5ff;
        border: 2px solid #00e5ff;
        border-radius: 5px;
        font-weight: bold;
        padding: 12px;
        font-family: 'Consolas';
    }
    QPushButton:hover { background-color: #00e5ff; color: #000; }
    QLabel { color: #00e5ff; font-family: 'Consolas'; }
    QLineEdit { background-color: #0a0a20; border: 1px solid #00e5ff; color: #fff; padding: 5px; }
    QTableWidget { background-color: rgba(5, 5, 20, 220); color: #fff; gridline-color: #005577; }
    QProgressBar { border: 1px solid #00e5ff; border-radius: 5px; text-align: center; color: white; background-color: #050510;}
    QProgressBar::chunk { background-color: #00e5ff; }
"""

class BaseSpaceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.stars = [(random.randint(0, 1920), random.randint(0, 1080), random.randint(1, 3)) for _ in range(120)]
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(5, 5, 15))
        p.setBrush(QBrush(QColor(255, 255, 255, 150)))
        p.setPen(Qt.NoPen)
        for x, y, s in self.stars: p.drawEllipse(x % self.width(), y % self.height(), s, s)

# --- ANA PENCERE ---
class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YIKIM FİLOSU KOMUTA MERKEZİ")
        self.resize(500, 650)
        self.bg = BaseSpaceWidget()
        self.setCentralWidget(self.bg)
        layout = QVBoxLayout(self.bg)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("Savaş Gemisi Yönetim Sistemi")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff0055; background: rgba(0,0,0,180); padding: 10px; border-radius: 5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        menus = [("PERSONEL KAYIT/SİL", self.ac_murettebat), ("STRATEJİK RADAR", self.ac_harita), 
                 ("GEMİ TELEMETRİSİ", self.ac_gemi_bilgi), ("FİLO VERİ AĞI", self.ac_filo), ("HEDEF ANALİZİ", self.ac_gezegen)]
        for t, f in menus:
            btn = QPushButton(t); btn.clicked.connect(f); layout.addWidget(btn)
        self.setStyleSheet(STYLE_SHEET)

    def ac_murettebat(self): self.w1 = MurettebatPenceresi(); self.w1.show()
    def ac_harita(self): self.w2 = HaritaPenceresi(); self.w2.show()
    def ac_gemi_bilgi(self): self.w3 = KendiGemimPenceresi(); self.w3.show()
    def ac_filo(self): self.w4 = FiloPenceresi(); self.w4.show()
    def ac_gezegen(self): self.w5 = GezegenPenceresi(); self.w5.show()

# --- HARİTA  ---
class HaritaPenceresi(BaseSpaceWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Taktik Radar")
        self.resize(900, 600)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        
        grad = QLinearGradient(600, 200, 900, 500)
        grad.setColorAt(0, QColor(0, 150, 255)); grad.setColorAt(1, QColor(0, 20, 50))
        painter.setBrush(grad); painter.setPen(QPen(QColor(0, 200, 255), 2))
        painter.drawEllipse(650, 150, 300, 300)
        
        coords = [(480, 300), (400, 220), (400, 380), (320, 140), (320, 460), (240, 60), (240, 540), (160, 220), (160, 380), (360, 300)]
        for i, (x, y) in enumerate(coords):
            color = QColor(255, 50, 50) if i == 3 else (QColor(255, 200, 0) if i == 0 else QColor(0, 255, 255))
            painter.setBrush(color)
            b = 24 if i == 0 else 16
            poly = QPolygon([QPoint(x+b, y), QPoint(x, y-(b//2)), QPoint(x+(b//4), y), QPoint(x, y+(b//2))])
            painter.drawPolygon(poly)
            painter.setPen(Qt.white); painter.drawText(x-10, y-15, f"V-{i}")

# --- GEMİ BİLGİ ---
class KendiGemimPenceresi(BaseSpaceWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yıkıcı-3 Telemetri")
        self.resize(450, 500); self.setStyleSheet(STYLE_SHEET)
        l = QVBoxLayout(self)
        panel = QFrame(); panel.setStyleSheet("background: rgba(10, 20, 40, 230); border: 1px solid #0e5ff; border-radius: 10px;")
        pl = QVBoxLayout(panel)
        
        conn = sqlite3.connect("yikim_filosu.db"); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM murettebat")
        ekstra = c.fetchone()[0]
        c.execute("SELECT * FROM gemiler WHERE filo_sirasi=3")
        g = c.fetchone()
        conn.close()

        lbl = QLabel(f"KAPTAN: {g[2]}\nGEMİ: {g[1]}\nMÜRETTEBAT: {g[7] + ekstra}\nSİLAH: {g[5]}")
        lbl.setStyleSheet("font-size: 15px; color: white; border: none;")
        pl.addWidget(lbl)
        
        pl.addWidget(QLabel("YAKIT"))
        b1 = QProgressBar(); b1.setValue(g[3]); pl.addWidget(b1)
        pl.addWidget(QLabel("KALKAN"))
        b2 = QProgressBar(); b2.setValue(g[4]); pl.addWidget(b2)
        
        l.addWidget(panel)

# --- MÜRETTEBAT ---
class MurettebatPenceresi(BaseSpaceWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personel İşlemleri"); self.resize(600, 500); self.setStyleSheet(STYLE_SHEET)
        l = QVBoxLayout(self)
        f = QHBoxLayout()
        self.ad = QLineEdit(placeholderText="AD"); self.soy = QLineEdit(placeholderText="SOYAD"); self.id = QLineEdit(placeholderText="YILDIZ ID")
        f.addWidget(self.ad); f.addWidget(self.soy); f.addWidget(self.id); l.addLayout(f)
        
        btns = QHBoxLayout()
        b1 = QPushButton("SİSTEME EKLE"); b1.clicked.connect(self.ekle); btns.addWidget(b1)
        b2 = QPushButton("SEÇİLİ PERSONELİ SİL"); b2.setStyleSheet("color: #ff4444; border-color: #ff4444;"); b2.clicked.connect(self.sil); btns.addWidget(b2)
        l.addLayout(btns)
        
        self.t = QTableWidget(0, 3); self.t.setHorizontalHeaderLabels(["AD", "SOYAD", "ID"]); self.t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.t.setSelectionBehavior(QTableWidget.SelectRows); l.addWidget(self.t); self.yukle()

    def yukle(self):
        self.t.setRowCount(0); conn = sqlite3.connect("yikim_filosu.db"); c = conn.cursor()
        c.execute("SELECT isim, soyisim, yildiz_kimlik FROM murettebat")
        for r_idx, r_data in enumerate(c.fetchall()):
            self.t.insertRow(r_idx)
            for c_idx, d in enumerate(r_data): self.t.setItem(r_idx, c_idx, QTableWidgetItem(str(d)))
        conn.close()

    def ekle(self):
        if not self.ad.text() or not self.id.text(): return
        try:
            conn = sqlite3.connect("yikim_filosu.db"); c = conn.cursor()
            c.execute("INSERT INTO murettebat (isim, soyisim, yildiz_kimlik) VALUES (?,?,?)", (self.ad.text(), self.soy.text(), self.id.text()))
            conn.commit(); conn.close(); self.yukle()
        except: QMessageBox.critical(self, "Hata", "Bu ID sistemde kayıtlı!")

    def sil(self):
        row = self.t.currentRow()
        if row == -1: return
        val = self.t.item(row, 2).text()
        conn = sqlite3.connect("yikim_filosu.db"); c = conn.cursor()
        c.execute("DELETE FROM murettebat WHERE yildiz_kimlik=?", (val,))
        conn.commit(); conn.close(); self.yukle()

# --- DİĞER PENCERELER ---
class GezegenPenceresi(BaseSpaceWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hedef Analiz"); self.resize(450, 400); self.setStyleSheet(STYLE_SHEET)
        l = QVBoxLayout(self)
        panel = QFrame(); panel.setStyleSheet("background: rgba(0, 30, 0, 230); border: 2px solid #00ff00; border-radius: 10px;")
        pl = QVBoxLayout(panel)
        txt = QLabel("HEDEF: OMEGA-Z\n\nTehdit Seviyesi: KRİTİK\nAtmosfer: Toksik Gaz\n\nİstihbarat: Gezegen savunması sadece Koramiral Vorgath'ın gemisi tarafından kırılabilecek bir iyon kalkanına sahip.")
        txt.setWordWrap(True); txt.setStyleSheet("color: #00ff00; font-size: 14px; border: none;"); pl.addWidget(txt)
        l.addWidget(panel)

class FiloPenceresi(BaseSpaceWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Filo Veri Ağı"); self.resize(800, 450); self.setStyleSheet(STYLE_SHEET)
        l = QVBoxLayout(self)
        t = QTableWidget(0, 6); t.setHorizontalHeaderLabels(["GEMİ", "KAPTAN", "YAKIT", "KALKAN", "SİLAH", "PERSONEL"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); l.addWidget(t)
        conn = sqlite3.connect("yikim_filosu.db"); c = conn.cursor()
        c.execute("SELECT gemi_adi, kaptan, yakit, kalkan, silah_durumu, murettebat_sayisi FROM gemiler")
        for r_idx, r_data in enumerate(c.fetchall()):
            t.insertRow(r_idx)
            for c_idx, d in enumerate(r_data): t.setItem(r_idx, c_idx, QTableWidgetItem(str(d)))
        conn.close()

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = AnaPencere(); window.show()
    sys.exit(app.exec_())