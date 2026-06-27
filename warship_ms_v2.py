import sys
import sqlite3
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QDialog, QMessageBox, QFrame, QStackedWidget)
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QPolygon, QRadialGradient, 
                         QPainterPath, QLinearGradient, QConicalGradient)
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect, QPointF

# --- SİSTEM PARAMETRELERİ ---
PİLOT_KODU = "1234"
KAPTAN_KODU = "1907"

def init_db():
    conn = sqlite3.connect("yikim_filosu_v3_3.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS gemiler")
    cursor.execute('''CREATE TABLE IF NOT EXISTS gemiler (
                        id INTEGER PRIMARY KEY,
                        gemi_adi TEXT, x INTEGER, y INTEGER)''')
    cursor.execute("DROP TABLE IF EXISTS sistem_durumu")
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistem_durumu (
                        id INTEGER PRIMARY KEY,
                        saldiri_aktif INTEGER,
                        tum_saldir INTEGER,
                        secili_id_list TEXT)''')
    
    # Filo Oluşturma
    filo = [(i, f"Yıkıcı-{i+1}", 150 + (i % 2 * 100), 100 + (i * 90)) for i in range(10)]
    cursor.executemany("INSERT INTO gemiler (id, gemi_adi, x, y) VALUES (?, ?, ?, ?)", filo)
    cursor.execute("INSERT INTO sistem_durumu (id, saldiri_aktif, tum_saldir, secili_id_list) VALUES (1, 0, 0, '')")
    conn.commit()
    conn.close()

# --- ASKERİ GİRİŞ PANELİ ---
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.role = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(450, 300)
        self.setStyleSheet("background-color: #02020a; border: 2px solid #00e5ff; border-radius: 5px;")
        
        layout = QVBoxLayout(self)
        title = QLabel("GALAKTİK SAVUNMA SİSTEMİ - GİRİŞ")
        title.setStyleSheet("color: #00e5ff; font-weight: bold; border: none; font-size: 18px; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignCenter)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("GÜVENLİK PROTOKOLÜ KODU")
        self.code_input.setEchoMode(QLineEdit.Password)
        self.code_input.setStyleSheet("background: #000; color: #fff; border: 1px solid #00e5ff; padding: 15px; font-size: 16px; font-family: 'Courier New';")
        
        btn = QPushButton("ERİŞİM YETKİSİ AL")
        btn.setStyleSheet("background: #00e5ff; color: #000; font-weight: bold; padding: 20px; font-size: 14px;")
        btn.clicked.connect(self.check_code)
        
        layout.addStretch(); layout.addWidget(title); layout.addWidget(self.code_input); layout.addWidget(btn); layout.addStretch()

    def check_code(self):
        code = self.code_input.text()
        if code == KAPTAN_KODU: self.role = "KAPTAN"; self.accept()
        elif code == PİLOT_KODU: self.role = "PİLOT"; self.accept()
        else: QMessageBox.critical(self, "ERİŞİM REDDEDİLDİ", "Geçersiz operasyonel yetki kodu!")

# --- ANA STRATEJİ MERKEZİ ---
class StratejiHaritasi(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.role = role
        self.mode = "NORMAL"
        self.gemiler = []
        self.selection_list = set()
        self.is_firing = False
        self.fire_all = False
        self.explosions = [] # Her patlama: {'x', 'y', 'life', 'ship_id'}
        
        self.bolt_offset = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.engine_tick)
        self.timer.start(20)
        
        # Uzay Atmosferi
        self.stars = [{'x': random.randint(0, 4000), 'y': random.randint(0, 3000), 
                       'size': random.uniform(0.3, 3.5), 'alpha': random.randint(50, 255)} for _ in range(500)]
        self.nebulas = [{'x': random.randint(0, 2500), 'y': random.randint(0, 2000), 
                         'color': random.choice([QColor(40, 20, 100, 25), QColor(0, 40, 100, 25)])} for _ in range(12)]

        self.load_persistence_data()
        self.init_ui()
        self.showFullScreen()

    def load_persistence_data(self):
        conn = sqlite3.connect("yikim_filosu_v3_3.db"); c = conn.cursor()
        c.execute("SELECT id, x, y, gemi_adi FROM gemiler")
        self.gemiler = [{"id": r[0], "x": r[1], "y": r[2], "name": r[3]} for r in c.fetchall()]
        c.execute("SELECT saldiri_aktif, tum_saldir, secili_id_list FROM sistem_durumu WHERE id=1")
        res = c.fetchone()
        if res:
            self.is_firing = bool(res[0]); self.fire_all = bool(res[1])
            if res[2]: self.selection_list = set(int(x) for x in res[2].split(",") if x)
        conn.close()

    def sync_to_db(self):
        conn = sqlite3.connect("yikim_filosu_v3_3.db"); c = conn.cursor()
        id_str = ",".join(map(str, self.selection_list))
        c.execute("UPDATE sistem_durumu SET saldiri_aktif=?, tum_saldir=?, secili_id_list=? WHERE id=1", 
                  (int(self.is_firing), int(self.fire_all), id_str))
        conn.commit(); conn.close()

    def init_ui(self):
        self.bottom_panel = QFrame(self)
        self.bottom_panel.setStyleSheet("background-color: rgba(2, 5, 15, 250); border-top: 1px solid #00e5ff;")
        self.stack = QStackedWidget(self.bottom_panel)
        
        # Ortak Buton Tasarımı
        btn_style = "QPushButton { background-color: #0a0a25; color: #00e5ff; border: 1px solid #00e5ff; padding: 12px; font-weight: bold; font-family: 'Consolas'; } QPushButton:hover { background: #00e5ff; color: #000; }"
        
        # Sayfa 1: Ana Kontrol
        self.page_normal = QWidget(); l1 = QHBoxLayout(self.page_normal)
        self.btn_hiz = QPushButton("FİLO KONUMLANDIRMA"); self.btn_sal = QPushButton("SİLAH KONTROL SİSTEMİ")
        self.btn_exit = QPushButton("ÇIKIŞ"); self.btn_exit.setStyleSheet("color: #ff3333; border-color: #ff3333;")
        l1.addWidget(self.btn_hiz); l1.addWidget(self.btn_sal); l1.addStretch(); l1.addWidget(self.btn_exit)
        
        # Sayfa 2: Hizalama
        self.page_align = QWidget(); l2 = QHBoxLayout(self.page_align)
        l2.addWidget(QPushButton("YENİ KOORDİNATLARI ONAYLA", clicked=self.save_align))
        l2.addWidget(QPushButton("VETO ET", clicked=self.cancel_align))

        # Sayfa 3: Saldırı
        self.page_attack = QWidget(); l3 = QHBoxLayout(self.page_attack)
        l3.addWidget(QPushButton("SALDIRI PROTOKOLÜ (SEÇİLİ)", clicked=lambda: self.set_fire(True, False)))
        l3.addWidget(QPushButton("TOPYEKÜN İMHA", clicked=lambda: self.set_fire(True, True)))
        l3.addWidget(QPushButton("ATEŞ KES", clicked=lambda: self.set_fire(False, False)))
        l3.addWidget(QPushButton("GERİ", clicked=lambda: self.change_mode("NORMAL")))

        self.stack.addWidget(self.page_normal); self.stack.addWidget(self.page_align); self.stack.addWidget(self.page_attack)
        self.setStyleSheet(btn_style)

        # GÜNCELLEME 2: Askeri Pilot Notu
        if self.role == "PİLOT":
            self.btn_hiz.hide(); self.btn_sal.hide()
            pilot_warn = QLabel("MÜDAHALE KISITLANMIŞTIR: Pilot personeli sadece sistem telemetrisini izlemekle yükümlüdür. Komuta yetkisi sadece Kaptan sınıfındadır.")
            pilot_warn.setStyleSheet("color: #ffcc00; font-style: italic; font-size: 13px; font-weight: bold; padding: 10px; border: 1px dashed #ffcc00; background: #220;")
            l1.insertWidget(0, pilot_warn)

        self.btn_hiz.clicked.connect(lambda: self.change_mode("ALIGN"))
        self.btn_sal.clicked.connect(lambda: self.change_mode("ATTACK"))
        self.btn_exit.clicked.connect(self.logout)

    def logout(self):
        self.sync_to_db(); self.close()
        login = LoginDialog()
        if login.exec_() == QDialog.Accepted: self.__init__(login.role)

    def change_mode(self, mode):
        self.mode = mode
        self.stack.setCurrentIndex(1 if mode == "ALIGN" else 2 if mode == "ATTACK" else 0)
        if mode == "ALIGN": self.original_positions = [g.copy() for g in self.gemiler]
        self.update()

    def set_fire(self, firing, all_ships):
        self.is_firing = firing; self.fire_all = all_ships; self.sync_to_db(); self.update()

    def engine_tick(self):
        if self.is_firing: self.bolt_offset = (self.bolt_offset + 40) % 200
        for exp in self.explosions[:]:
            exp['life'] -= 0.05
            if exp['life'] <= 0: self.explosions.remove(exp)
        self.update()

    def save_align(self):
        conn = sqlite3.connect("yikim_filosu_v3_3.db"); c = conn.cursor()
        for g in self.gemiler: c.execute("UPDATE gemiler SET x=?, y=? WHERE id=?", (g['x'], g['y'], g['id']))
        conn.commit(); conn.close(); self.change_mode("NORMAL")

    def cancel_align(self):
        self.gemiler = [g.copy() for g in self.original_positions]; self.change_mode("NORMAL")

    def resizeEvent(self, event):
        self.bottom_panel.setGeometry(0, self.height() - 100, self.width(), 100)
        self.stack.setGeometry(0, 0, self.width(), 100)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(2, 2, 8))
        
        # 1. Uzay ve Nebula
        for neb in self.nebulas:
            grad = QRadialGradient(neb['x'], neb['y'], 800)
            grad.setColorAt(0, neb['color']); grad.setColorAt(1, Qt.transparent)
            p.setBrush(grad); p.setPen(Qt.NoPen); p.drawEllipse(neb['x']-800, neb['y']-800, 1600, 1600)
        for s in self.stars:
            p.setPen(Qt.NoPen); p.setBrush(QColor(255, 255, 255, s['alpha']))
            p.drawEllipse(QPointF(s['x'], s['y']), s['size'], s['size'])

        # Gezegen Konumu
        target_center = QPoint(self.width() - 450, self.height() // 2)
        planet_r = 280 

        # 2. GÜNCELLEME 3: Ultra-Detaylı Gezegen
        # Atmosfer Glow (Derinlikli)
        glow = QRadialGradient(target_center, planet_r + 80)
        glow.setColorAt(0.7, QColor(0, 100, 255, 50))
        glow.setColorAt(0.85, QColor(0, 50, 200, 20))
        glow.setColorAt(1, Qt.transparent)
        p.setBrush(glow); p.drawEllipse(target_center, planet_r + 80, planet_r + 80)

        # Kırpma (Clipping)
        planet_path = QPainterPath()
        planet_path.addEllipse(QPointF(target_center), planet_r, planet_r)
        
        p.save()
        p.setClipPath(planet_path)
        
        # Taban Okyanus (Derin Mavi-Siyah Geçiş)
        sea_grad = QRadialGradient(target_center.x()-50, target_center.y()-50, planet_r*1.5)
        sea_grad.setColorAt(0, QColor(10, 80, 180)); sea_grad.setColorAt(0.8, QColor(5, 15, 40))
        p.setBrush(sea_grad); p.drawPath(planet_path)
        
        # Detaylı Kara Parçaları ve Kıyı Şeridi
        random.seed(77)
        for _ in range(25):
            cx = target_center.x() + random.randint(-250, 200)
            cy = target_center.y() + random.randint(-250, 200)
            size = random.randint(100, 300)
            
            # Kıyı Şeridi (Açık Yeşil/Sarı)
            p.setBrush(QColor(60, 150, 60, 150))
            p.drawEllipse(cx-5, cy-5, size+10, size+10)
            
            # Dağlık Alanlar ve Ormanlar (Koyu Yeşil)
            land_grad = QLinearGradient(cx, cy, cx+size, cy+size)
            land_grad.setColorAt(0, QColor(30, 90, 20)); land_grad.setColorAt(1, QColor(10, 40, 5))
            p.setBrush(land_grad)
            p.drawEllipse(cx, cy, size, size)

        # Bulut Katmanı (Hareketli Simüle Edilmiş)
        random.seed(99)
        p.setBrush(QColor(255, 255, 255, 60))
        for _ in range(40):
            p.drawEllipse(target_center.x() + random.randint(-300, 300), 
                          target_center.y() + random.randint(-300, 300), 
                          random.randint(50, 150), random.randint(20, 60))
        p.restore()

        # Terminal Shadow (Gece/Gündüz Sınırı)
        night = QRadialGradient(target_center.x() + 150, target_center.y() - 150, planet_r * 2.2)
        night.setColorAt(0.4, Qt.transparent); night.setColorAt(0.7, QColor(0, 0, 0, 240))
        p.setBrush(night); p.drawEllipse(target_center, planet_r, planet_r)

        # 3. GÜNCELLEME 1: Çoklu Gemi Bağımsız Patlama Sistemi
        for g in self.gemiler:
            is_active = g['id'] in self.selection_list
            color = QColor(255, 255, 0) if is_active else QColor(0, 255, 255)
            
            dx = target_center.x() - g['x']; dy = target_center.y() - g['y']
            dist = math.sqrt(dx**2 + dy**2); angle = math.atan2(dy, dx)
            
            if self.is_firing and (self.fire_all or is_active):
                p.setPen(QPen(QColor(0, 255, 255, 200), 2))
                # Lazerler
                for i in range(0, 2200, 160):
                    d = i + self.bolt_offset
                    if d < dist - planet_r + 10:
                        sx = g['x'] + math.cos(angle) * d; sy = g['y'] + math.sin(angle) * d
                        ex = g['x'] + math.cos(angle) * (d + 50); ey = g['y'] + math.sin(angle) * (d + 50)
                        p.drawLine(QPointF(sx, sy), QPointF(ex, ey))
                    elif random.random() > 0.93: # Her aktif gemi kendi patlamasını üretir
                        ix = target_center.x() - math.cos(angle + random.uniform(-0.1, 0.1)) * (planet_r - 5)
                        iy = target_center.y() - math.sin(angle + random.uniform(-0.1, 0.1)) * (planet_r - 5)
                        self.explosions.append({'x': ix, 'y': iy, 'life': 1.0})

            # Gemi Çizimi
            p.save(); p.translate(g['x'], g['y']); p.rotate(math.degrees(angle))
            p.setBrush(color); p.setPen(Qt.white)
            p.drawPolygon(QPolygon([QPoint(30, 0), QPoint(-15, -15), QPoint(-8, 0), QPoint(-15, 15)]))
            p.restore(); p.drawText(g['x']-20, g['y']-30, g['name'])

        # Patlamaların Çizimi
        for exp in self.explosions:
            p.setBrush(QColor(255, 100, 0, int(exp['life'] * 255)))
            p.setPen(Qt.NoPen)
            r = (1.2 - exp['life']) * 80
            p.drawEllipse(QPointF(exp['x'], exp['y']), r, r)
            # Beyaz Çekirdek
            p.setBrush(QColor(255, 255, 255, int(exp['life'] * 200)))
            p.drawEllipse(QPointF(exp['x'], exp['y']), r/3, r/3)

    def mousePressEvent(self, event):
        if self.role == "PİLOT": return
        for g in self.gemiler:
            if QRect(g['x']-30, g['y']-30, 60, 60).contains(event.pos()):
                if self.mode == "ALIGN": self.dragged_ship = g
                else:
                    if g['id'] in self.selection_list: self.selection_list.remove(g['id'])
                    else: self.selection_list.add(g['id'])
                    self.sync_to_db()
                break
        self.update()

    def mouseMoveEvent(self, event):
        if self.mode == "ALIGN" and self.dragged_ship:
            self.dragged_ship['x'] = event.pos().x(); self.dragged_ship['y'] = event.pos().y(); self.update()

    def mouseReleaseEvent(self, event): self.dragged_ship = None

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        ex = StratejiHaritasi(login.role)
        sys.exit(app.exec_())