import sys
import sqlite3
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QDialog, QMessageBox, QFrame, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QPolygon, QRadialGradient, 
                         QPainterPath, QLinearGradient, QFont)
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect, QPointF

# --- SİSTEM PARAMETRELERİ ---
PİLOT_KODU = "1234"
KAPTAN_KODU = "1907"
DB_NAME = "yikim_filosu_v4_1.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS gemiler")
    cursor.execute('''CREATE TABLE IF NOT EXISTS gemiler (
                        id INTEGER PRIMARY KEY,
                        gemi_adi TEXT, x INTEGER, y INTEGER,
                        kaptan_adi TEXT, murettebat INTEGER,
                        silah_durumu TEXT, kalkan_durumu TEXT, yakit TEXT)''')
    
    cursor.execute("DROP TABLE IF EXISTS sistem_durumu")
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistem_durumu (
                        id INTEGER PRIMARY KEY,
                        saldiri_aktif INTEGER,
                        tum_saldir INTEGER,
                        secili_id_list TEXT,
                        kalkan_seviyesi REAL)''')
    
    # Amiral Gemisi tam ortaya ve biraz öne (x:300, y:500) konumlandırıldı. 
    # Diğer gemiler onun etrafında sıralandı.
    filo_verisi = [
        (0, "KRONOS LEVIATHAN (AMİRAL GEMİSİ)", 300, 500, "Büyük Amiral Targon Vex", 540, "%120 Hiper-Plazma Bataryası", "%150 Ağır Amiral Zırhı", "%98 Kuantum Çekirdeği"),
        (1, "Galaktik Azrail", 150, 100, "Kpt. Jarek Voss", 115, "%95 Termal Lazer", "%95 Reflektör", "%74 Antimadde"),
        (2, "Şafak Sökücü", 250, 190, "Kpt. Nova Prime", 210, "%88 İyon Topu", "%100 Aşama Kalkanı", "%91 Kuantum"),
        (3, "Gölge Süvarisi", 150, 280, "Kpt. Zephyr Blank", 95, "%100 Ray Topu", "%80 Sızma Modülü", "%62 Plazma"),
        (4, "Kozmik Çekiç", 250, 370, "Kpt. Brunt Ironclad", 320, "%85 Kinetik Batarya", "%100 Deflektör", "%95 Çekirdek"),
        (5, "Nebula Engereği", 150, 460, "Kpt. Sarris Thorne", 130, "%94 Asit Torpidosu", "%90 Enerji Ağı", "%81 Antimadde"),
        (6, "Yıldız Kıran", 150, 640, "Kpt. Marcus Drake", 185, "%99 Takyon Işını", "%95 Kuvvet Alanı", "%70 Kuantum"),
        (7, "Sonsuz Gece", 250, 730, "Kpt. Lyra Void", 105, "%90 Siyah Delik Bombası", "%85 Absorbe", "%66 Plazma"),
        (8, "Kıyamet Habercisi", 150, 820, "Kpt. Malakor Grim", 450, "%100 Plazma Erim", "%100 Ağır Zırh", "%99 Çekirdek"),
        (9, "Kızıl Anka", 250, 910, "Kpt. Selene Ray", 160, "%91 Termal Lazer", "%90 Reflektör", "%85 Kuantum")
    ]
    
    cursor.executemany("""INSERT INTO gemiler 
                       (id, gemi_adi, x, y, kaptan_adi, murettebat, silah_durumu, kalkan_durumu, yakit) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", filo_verisi)
    
    cursor.execute("INSERT INTO sistem_durumu (id, saldiri_aktif, tum_saldir, secili_id_list, kalkan_seviyesi) VALUES (1, 0, 0, '', 100.0)")
    conn.commit()
    conn.close()

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.role = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(450, 300)
        self.setStyleSheet("background-color: #02020a; border: 2px solid #ffaa00; border-radius: 5px;")
        
        layout = QVBoxLayout(self)
        title = QLabel("ERİŞİM PROTOKOLÜ")
        title.setStyleSheet("color: #ffaa00; font-weight: bold; border: none; font-size: 18px; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignCenter)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("GÜVENLİK PROTOKOLÜ KODU")
        self.code_input.setEchoMode(QLineEdit.Password)
        self.code_input.setStyleSheet("background: #000; color: #fff; border: 1px solid #ffaa00; padding: 15px; font-size: 16px; font-family: 'Courier New';")
        
        btn = QPushButton("SİSTEMİ BAŞLAT")
        btn.setStyleSheet("background: #ffaa00; color: #000; font-weight: bold; padding: 20px; font-size: 14px;")
        btn.clicked.connect(self.check_code)
        
        layout.addStretch(); layout.addWidget(title); layout.addWidget(self.code_input); layout.addWidget(btn); layout.addStretch()

    def check_code(self):
        code = self.code_input.text()
        if code == KAPTAN_KODU: self.role = "KAPTAN"; self.accept()
        elif code == PİLOT_KODU: self.role = "PİLOT"; self.accept()
        else: QMessageBox.critical(self, "ERİŞİM REDDEDİLDİ", "Geçersiz operasyonel yetki kodu!")

class TelemetriTablosu(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DONANMA TAKTİK TELEMETRİ VERİLERİ")
        self.setMinimumSize(1000, 500)
        self.resize(1200, 600)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet("background-color: #050510; border: 1px solid #ffaa00;")
        
        layout = QVBoxLayout(self)
        title = QLabel("MÜREKKEP SİSTEMİ REAL-TIME DONANMA VERİ TABANI SORGUSU")
        title.setStyleSheet("color: #ffaa00; font-family: 'Consolas'; font-size: 14px; font-weight: bold; border: none; padding: 5px;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Gemi ID", "Gemi Adı", "Komuta Eden Kaptan", "Aktif Mürettebat", 
            "Silah Sistemleri", "Defansif Kalkan", "Taktik Yakıt Durumu", "Konum (X, Y)"
        ])
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: #020208; color: #ffffff; gridline-color: #332200; font-family: 'Consolas'; font-size: 12px; }
            QHeaderView::section { background-color: #151525; color: #ffaa00; font-weight: bold; border: 1px solid #332200; padding: 6px; }
            QTableWidget::item { padding: 5px; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        self.verileri_yukle()
        
    def verileri_yukle(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, gemi_adi, kaptan_adi, murettebat, silah_durumu, kalkan_durumu, yakit, x, y FROM gemiler")
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{row_data[3]} Personel"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(row_data[4])))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(row_data[5])))
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(row_data[6])))
            self.table.setItem(row_idx, 7, QTableWidgetItem(f"X:{row_data[7]} / Y:{row_data[8]}"))
            
            for col_idx in range(8):
                self.table.item(row_idx, col_idx).setTextAlignment(Qt.AlignCenter)

class StratejiHaritasi(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.role = role
        self.mode = "NORMAL"
        self.gemiler = []
        self.selection_list = set()
        self.is_firing = False
        self.fire_all = False
        self.kalkan = 100.0
        
        self.explosions = []
        self.giant_explosions = []
        self.debris = []
        self.dragged_ship = None
        
        self.bolt_offset = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.engine_tick)
        self.timer.start(20)
        
        self.stars = [{'x': random.randint(0, 4000), 'y': random.randint(0, 3000), 
                       'size': random.uniform(0.3, 3.5), 'alpha': random.randint(50, 255)} for _ in range(500)]
        self.nebulas = [{'x': random.randint(0, 2500), 'y': random.randint(0, 2000), 
                         'color': random.choice([QColor(60, 20, 40, 20), QColor(20, 60, 80, 20)])} for _ in range(10)]

        self.load_persistence_data()
        self.init_ui()
        self.showFullScreen()

    def load_persistence_data(self):
        conn = sqlite3.connect(DB_NAME); c = conn.cursor()
        c.execute("SELECT id, x, y, gemi_adi FROM gemiler")
        self.gemiler = [{"id": r[0], "x": r[1], "y": r[2], "name": r[3]} for r in c.fetchall()]
        c.execute("SELECT saldiri_aktif, tum_saldir, secili_id_list, kalkan_seviyesi FROM sistem_durumu WHERE id=1")
        res = c.fetchone()
        if res:
            self.is_firing = bool(res[0]); self.fire_all = bool(res[1])
            if res[2]: self.selection_list = set(int(x) for x in res[2].split(",") if x)
            self.kalkan = res[3]
            if self.kalkan == -999.0: self.create_debris()
        conn.close()

    def sync_to_db(self):
        conn = sqlite3.connect(DB_NAME); c = conn.cursor()
        id_str = ",".join(map(str, self.selection_list))
        c.execute("UPDATE sistem_durumu SET saldiri_aktif=?, tum_saldir=?, secili_id_list=?, kalkan_seviyesi=? WHERE id=1", 
                  (int(self.is_firing), int(self.fire_all), id_str, self.kalkan))
        conn.commit(); conn.close()

    def reset_planet(self):
        self.kalkan = 100.0; self.is_firing = False; self.debris = []; self.giant_explosions = []
        self.sync_to_db(); self.update()

    def show_telemetry_window(self):
        dialog = TelemetriTablosu()
        dialog.exec_()

    def init_ui(self):
        self.bottom_panel = QFrame(self)
        self.bottom_panel.setStyleSheet("background-color: rgba(5, 5, 10, 250); border-top: 1px solid #ffaa00;")
        self.stack = QStackedWidget(self.bottom_panel)
        
        btn_style = "QPushButton { background-color: #1a1a1a; color: #ffaa00; border: 1px solid #ffaa00; padding: 12px; font-weight: bold; font-family: 'Consolas'; } QPushButton:hover { background: #ffaa00; color: #000; }"
        
        self.page_normal = QWidget(); l1 = QHBoxLayout(self.page_normal)
        self.btn_hiz = QPushButton("FİLO KONUMLANDIRMA")
        self.btn_sal = QPushButton("SİLAH KONTROL SİSTEMİ")
        
        self.btn_tel = QPushButton("FİLO TELEMETRİ TABLOSU")
        self.btn_tel.setStyleSheet("background-color: #112211; color: #00ff66; border-color: #00ff66;")
        self.btn_tel.clicked.connect(self.show_telemetry_window)
        
        self.btn_reset = QPushButton("SİMÜLASYONU SIFIRLA (YENİ HEDEF)"); self.btn_reset.setStyleSheet("color: #00e5ff; border-color: #00e5ff;")
        self.btn_exit = QPushButton("ÇIKIŞ"); self.btn_exit.setStyleSheet("color: #ff3333; border-color: #ff3333;")
        
        l1.addWidget(self.btn_hiz); l1.addWidget(self.btn_sal); l1.addWidget(self.btn_tel); l1.addWidget(self.btn_reset); l1.addStretch(); l1.addWidget(self.btn_exit)
        
        self.page_align = QWidget(); l2 = QHBoxLayout(self.page_align)
        l2.addWidget(QPushButton("YENİ KOORDİNATLARI ONAYLA", clicked=self.save_align))
        l2.addWidget(QPushButton("VETO ET", clicked=self.cancel_align))

        self.page_attack = QWidget(); l3 = QHBoxLayout(self.page_attack)
        l3.addWidget(QPushButton("SALDIRI PROTOKOLÜ (SEÇİLİ)", clicked=lambda: self.set_fire(True, False)))
        l3.addWidget(QPushButton("TOPYEKÜN İMHA", clicked=lambda: self.set_fire(True, True)))
        l3.addWidget(QPushButton("ATEŞ KES", clicked=lambda: self.set_fire(False, False)))
        l3.addWidget(QPushButton("GERİ", clicked=lambda: self.change_mode("NORMAL")))

        self.stack.addWidget(self.page_normal); self.stack.addWidget(self.page_align); self.stack.addWidget(self.page_attack)
        self.setStyleSheet(btn_style)

        if self.role == "PİLOT":
            self.btn_hiz.hide(); self.btn_sal.hide(); self.btn_reset.hide()
            pilot_warn = QLabel("MÜDAHALE KISITLANMIŞTIR: Pilot personeli sadece sistem telemetrisini izlemekle yükümlüdür.")
            pilot_warn.setStyleSheet("color: #ffaa00; font-style: italic; font-size: 13px; font-weight: bold; padding: 10px; border: 1px dashed #ffaa00; background: #220;")
            l1.insertWidget(0, pilot_warn)

        self.btn_hiz.clicked.connect(lambda: self.change_mode("ALIGN"))
        self.btn_sal.clicked.connect(lambda: self.change_mode("ATTACK"))
        self.btn_reset.clicked.connect(self.reset_planet)
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
        if self.kalkan == -999.0 and firing: return
        self.is_firing = firing; self.fire_all = all_ships; self.sync_to_db(); self.update()

    def create_debris(self):
        tc = QPoint(self.width() - 450, self.height() // 2)
        self.debris = [{'x': tc.x() + random.randint(-150, 150), 'y': tc.y() + random.randint(-150, 150),
                        'vx': random.uniform(-2, 2), 'vy': random.uniform(-2, 2),
                        'size': random.randint(10, 40)} for _ in range(30)]

    def create_massive_explosion(self):
        tc = QPoint(self.width() - 450, self.height() // 2)
        self.giant_explosions.append({'x': tc.x(), 'y': tc.y(), 'life': 1.0, 'max_size': 800})
        self.create_debris()

    def engine_tick(self):
        if self.is_firing and self.kalkan > -999.0:
            self.bolt_offset = (self.bolt_offset + 40) % 200
            active_count = len(self.gemiler) if self.fire_all else len(self.selection_list)
            
            if active_count > 0:
                if self.kalkan > 0.0:
                    # KALKAN ERİME HIZI ARTIRILDI (0.01'den 0.05'e)
                    self.kalkan -= (active_count * 0.05)
                    if self.kalkan <= 0.0:
                        self.kalkan = 0.0
                        self.is_firing = False
                        self.sync_to_db()
                        QMessageBox.information(self, "KALKAN ÇÖKTÜ", 
                                                "Gezegenin savunma hatları sıfırlandı!\nSaldırı durduruldu. Gezegeni tamamen yok etmek veya barış ilan etmek sizin emrinizde, Kaptan!")
                else:
                    # GEZEGEN DAYANIKLILIĞI ARTIRILDI (Erime Limiti -3'ten -50'ye Çıkarıldı)
                    self.kalkan -= (active_count * 0.02)
                    if self.kalkan <= -50.0: 
                        self.kalkan = -999.0
                        self.is_firing = False
                        self.create_massive_explosion()
                        self.sync_to_db()

        for exp in self.explosions[:]:
            exp['life'] -= 0.05
            if exp['life'] <= 0: self.explosions.remove(exp)
            
        for d in self.debris:
            d['x'] += d['vx']; d['y'] += d['vy']

        self.update()

    def save_align(self):
        conn = sqlite3.connect(DB_NAME); c = conn.cursor()
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
        
        for neb in self.nebulas:
            grad = QRadialGradient(neb['x'], neb['y'], 800)
            grad.setColorAt(0, neb['color']); grad.setColorAt(1, Qt.transparent)
            p.setBrush(grad); p.setPen(Qt.NoPen); p.drawEllipse(neb['x']-800, neb['y']-800, 1600, 1600)
        for s in self.stars:
            p.setPen(Qt.NoPen); p.setBrush(QColor(255, 255, 255, s['alpha']))
            p.drawEllipse(QPointF(s['x'], s['y']), s['size'], s['size'])

        target_center = QPoint(self.width() - 450, self.height() // 2)
        planet_r = 280 

        # HUD PANEL
        p.setFont(QFont("Consolas", 12, QFont.Bold))
        bar_x = self.width() - 550; bar_y = 50; bar_w = 400; bar_h = 20
        
        if self.kalkan >= 0:
            p.setBrush(QColor(0, 50, 100, 150)); p.setPen(QPen(QColor(0, 255, 255), 2))
            p.drawRect(bar_x, bar_y, bar_w, bar_h)
            current_w = int((self.kalkan / 100.0) * bar_w)
            p.setBrush(QColor(0, 255, 255) if self.kalkan > 30 else QColor(255, 100, 0))
            p.drawRect(bar_x, bar_y, current_w, bar_h)
            p.setPen(Qt.white); p.drawText(bar_x, bar_y - 10, f"ENERJİ KALKANI: %{int(self.kalkan)}")
        elif self.kalkan > -999.0:
            # Gezegen çekirdek direnci çubuğu simülasyonu
            p.setPen(QPen(QColor(255, 50, 50), 2))
            p.drawRect(bar_x, bar_y, bar_w, bar_h)
            p.setBrush(QColor(255, 0, 0))
            core_hp_w = int((50.0 + self.kalkan) / 50.0 * bar_w)
            p.drawRect(bar_x, bar_y, core_hp_w, bar_h)
            p.setPen(Qt.white)
            p.drawText(bar_x, bar_y - 10, f"GEZEGEN ÇEKİRDEĞİ (DAYANIKLILIK: %{int((50.0 + self.kalkan)*2)})")
        else:
            p.setPen(QPen(QColor(150, 150, 150), 2))
            p.drawText(bar_x, bar_y, "SİSTEM YOK EDİLDİ - HEDEF İMHA EDİLDİ")

        if self.kalkan != -999.0:
            if self.kalkan > 0:
                glow = QRadialGradient(target_center, planet_r + 80)
                glow.setColorAt(0.7, QColor(0, 100, 255, 50)); glow.setColorAt(1, Qt.transparent)
                p.setBrush(glow); p.drawEllipse(target_center, planet_r + 80, planet_r + 80)

            planet_path = QPainterPath(); planet_path.addEllipse(QPointF(target_center), planet_r, planet_r)
            p.save(); p.setClipPath(planet_path)
            
            sea_grad = QRadialGradient(target_center.x()-50, target_center.y()-50, planet_r*1.5)
            sea_grad.setColorAt(0, QColor(10, 80, 180)); sea_grad.setColorAt(0.8, QColor(5, 15, 40))
            p.setBrush(sea_grad); p.drawPath(planet_path)
            
            random.seed(77)
            for _ in range(25):
                cx = target_center.x() + random.randint(-250, 200); cy = target_center.y() + random.randint(-250, 200)
                size = random.randint(100, 300)
                p.setBrush(QColor(60, 150, 60, 150)); p.drawEllipse(cx-5, cy-5, size+10, size+10)
                land_grad = QLinearGradient(cx, cy, cx+size, cy+size)
                land_grad.setColorAt(0, QColor(30, 90, 20)); land_grad.setColorAt(1, QColor(10, 40, 5))
                p.setBrush(land_grad); p.drawEllipse(cx, cy, size, size)
            p.restore()

            night = QRadialGradient(target_center.x() + 150, target_center.y() - 150, planet_r * 2.2)
            night.setColorAt(0.4, Qt.transparent); night.setColorAt(0.7, QColor(0, 0, 0, 240))
            p.setBrush(night); p.drawEllipse(target_center, planet_r, planet_r)

            if self.kalkan > 0:
                p.setPen(QPen(QColor(0, 255, 255, 180), 3))
                shield_alpha = int((self.kalkan / 100.0) * 80) 
                p.setBrush(QColor(0, 255, 255, shield_alpha))
                p.drawEllipse(target_center, planet_r + 20, planet_r + 20)
        else:
            p.setPen(Qt.NoPen)
            for d in self.debris:
                p.setBrush(QColor(50, 40, 30))
                p.drawEllipse(QPointF(d['x'], d['y']), d['size'], d['size'])
                p.setBrush(QColor(255, 100, 0, 100))
                p.drawEllipse(QPointF(d['x'], d['y']), d['size']/2, d['size']/2)

        for g in self.gemiler:
            is_active = g['id'] in self.selection_list
            color = QColor(255, 150, 0) if is_active else QColor(0, 200, 255)
            
            dx = target_center.x() - g['x']; dy = target_center.y() - g['y']
            dist = math.sqrt(dx**2 + dy**2); angle = math.atan2(dy, dx)
            
            if self.is_firing and (self.fire_all or is_active) and self.kalkan != -999.0:
                p.setPen(QPen(QColor(0, 255, 255, 200) if g['id'] != 0 else QColor(255, 50, 50, 240), 2 if g['id'] != 0 else 4))
                for i in range(0, 2200, 160):
                    d = i + self.bolt_offset
                    impact_radius = planet_r + 20 if self.kalkan > 0 else planet_r
                    
                    if d < dist - impact_radius + 5:
                        sx = g['x'] + math.cos(angle) * d; sy = g['y'] + math.sin(angle) * d
                        ex = g['x'] + math.cos(angle) * (d + 50); ey = g['y'] + math.sin(angle) * (d + 50)
                        p.drawLine(QPointF(sx, sy), QPointF(ex, ey))
                    elif random.random() > 0.90:
                        ix = target_center.x() - math.cos(angle + random.uniform(-0.1, 0.1)) * (impact_radius)
                        iy = target_center.y() - math.sin(angle + random.uniform(-0.1, 0.1)) * (impact_radius)
                        self.explosions.append({'x': ix, 'y': iy, 'life': 1.0})

            p.save(); p.translate(g['x'], g['y']); p.rotate(math.degrees(angle))
            p.setBrush(color); p.setPen(Qt.white)
            
            if g['id'] == 0:
                p.setBrush(QColor(220, 30, 30) if is_active else QColor(255, 215, 0))
                p.drawPolygon(QPolygon([QPoint(60, 0), QPoint(0, -30), QPoint(-45, 0), QPoint(0, 30)]))
            else:
                # GÜNCELLEME: Ok formundan Üçgen formuna geçiş (Arkası düz, önü sivri)
                p.drawPolygon(QPolygon([QPoint(30, 0), QPoint(-15, -15), QPoint(-15, 15)]))
                
            p.restore()
            
            p.setFont(QFont("Consolas", 10, QFont.Bold if g['id'] == 0 else QFont.Normal))
            p.drawText(g['x']-20, g['y']-35 if g['id'] == 0 else g['y']-30, g['name'])

        for exp in self.explosions:
            p.setBrush(QColor(0, 255, 255, int(exp['life'] * 255)) if self.kalkan > 0 else QColor(255, 100, 0, int(exp['life'] * 255)))
            p.setPen(Qt.NoPen)
            r = (1.2 - exp['life']) * 60
            p.drawEllipse(QPointF(exp['x'], exp['y']), r, r)

    def mousePressEvent(self, event):
        if self.role == "PİLOT": return
        for g in self.gemiler:
            size_bound = 60 if g['id'] == 0 else 40
            if QRect(g['x']-size_bound, g['y']-size_bound, size_bound*2, size_bound*2).contains(event.pos()):
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
    init_db() # Amiral gemisinin yeni harita merkezi konumunu alabilmesi için DB sıfırlanır
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        ex = StratejiHaritasi(login.role)
        sys.exit(app.exec_())