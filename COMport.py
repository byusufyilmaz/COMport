import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QMessageBox, QLineEdit, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer

BAUD_RATELER = [4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]


# === ASCII PENCERESİ ===
class AsciiPencere(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASCII Görünümü")
        self.setGeometry(1100, 200, 500, 600)
        layout = QVBoxLayout()

        self.ascii_box_all = QTextEdit()
        self.ascii_box_all.setReadOnly(True)
        self.ascii_box_all.setPlaceholderText("🔤 Tüm gelen ASCII verileri...")

        self.ascii_box_filtered = QTextEdit()  # 🆕
        self.ascii_box_filtered.setReadOnly(True)
        self.ascii_box_filtered.setPlaceholderText("🎯 Filtrelenmiş ASCII verileri...")  # 🆕

        layout.addWidget(QLabel("ASCII (Tüm Veriler):"))
        layout.addWidget(self.ascii_box_all)
        layout.addWidget(QLabel("Filtrelenmiş ASCII (Sadece hedef paketler):"))  # 🆕
        layout.addWidget(self.ascii_box_filtered)  # 🆕

        self.setLayout(layout)

    def ascii_ekle_tum(self, veri):  # 🆕
        try:
            text = veri.decode('ascii', errors='replace')
            self.ascii_box_all.append(text)
        except Exception as e:
            self.ascii_box_all.append(f"[HATA: {e}]")

    def ascii_ekle_filtreli(self, veri):  # 🆕
        try:
            text = veri.decode('ascii', errors='replace')
            self.ascii_box_filtered.append(text)
        except Exception as e:
            self.ascii_box_filtered.append(f"[HATA: {e}]")


# === ANA PENCERE ===
class SeriPortArayuzu(QWidget):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.veri_oku)
        self.buffer = bytearray()
        self.PAKET_BOYUTU = 14

        self.target_msgids = []
        self.target_canid = None

        self.ascii_pencere = AsciiPencere()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("COM Port Okuma")
        self.setGeometry(400, 200, 900, 700)
        ana_layout = QVBoxLayout()

        ust_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.portlari_yenile()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems([str(b) for b in BAUD_RATELER])
        self.baud_combo.setCurrentText("9600")
        self.connect_button = QPushButton("🔗 Connect")
        self.connect_button.clicked.connect(self.connect_disconnect)
        self.refresh_button = QPushButton("Yenile")
        self.refresh_button.clicked.connect(self.portlari_yenile)

        self.ascii_button = QPushButton("ASCII Görüntüle")
        self.ascii_button.clicked.connect(self.ascii_pencere.show)

        ust_layout.addWidget(QLabel("Port:"))
        ust_layout.addWidget(self.port_combo)
        ust_layout.addWidget(QLabel("Baud:"))
        ust_layout.addWidget(self.baud_combo)
        ust_layout.addWidget(self.connect_button)
        ust_layout.addWidget(self.refresh_button)
        ust_layout.addWidget(self.ascii_button)
        ana_layout.addLayout(ust_layout)

        filtre_group = QGroupBox("Hedef (Target) Filtreleri")
        filtre_layout = QHBoxLayout()

        self.target_msgids_input = QLineEdit()
        self.target_msgids_input.setPlaceholderText("Message ID'ler (örn: 0x01,1E,0x10)")

        self.target_canid_input = QLineEdit()
        self.target_canid_input.setPlaceholderText("CAN ID (örn: 0x02) — boş = hepsi")

        self.apply_targets_button = QPushButton("Uygula")
        self.apply_targets_button.clicked.connect(self.apply_targets)

        filtre_layout.addWidget(QLabel("Message ID'ler:"))
        filtre_layout.addWidget(self.target_msgids_input)
        filtre_layout.addWidget(QLabel("CAN ID:"))
        filtre_layout.addWidget(self.target_canid_input)
        filtre_layout.addWidget(self.apply_targets_button)

        filtre_group.setLayout(filtre_layout)
        ana_layout.addWidget(filtre_group)

        alanlar_group = QGroupBox("Okunan Paket Alanları (Sadece filtreye uyanlar)")
        alanlar_layout = QHBoxLayout()

        self.header_combo = QComboBox()
        self.msgid_combo = QComboBox()
        self.canid_combo = QComboBox()
        self.data_combo = QComboBox()
        self.end_combo = QComboBox()

        self.header_combo.addItem("Header (0x63 0x73)")
        self.msgid_combo.addItem("CamMessageId")
        self.canid_combo.addItem("CanDevID")
        self.data_combo.addItem("Data")
        self.end_combo.addItem("End (0x59)")

        alanlar_layout.addWidget(self.header_combo)
        alanlar_layout.addWidget(self.msgid_combo)
        alanlar_layout.addWidget(self.canid_combo)
        alanlar_layout.addWidget(self.data_combo)
        alanlar_layout.addWidget(self.end_combo)
        alanlar_group.setLayout(alanlar_layout)
        ana_layout.addWidget(alanlar_group)

        self.raw_box = QTextEdit()
        self.raw_box.setReadOnly(True)
        self.raw_box.setPlaceholderText("📥 Gelen ham veriler (Hexadecimal olarak)...")
        ana_layout.addWidget(QLabel("Ham Veri:"))
        ana_layout.addWidget(self.raw_box, stretch=2)

        self.filtered_box = QTextEdit()
        self.filtered_box.setReadOnly(True)
        self.filtered_box.setPlaceholderText("🎯 Hedef paketlerin verileri burada gösterilecek...")
        ana_layout.addWidget(QLabel("Filtrelenmiş Veri:"))
        ana_layout.addWidget(self.filtered_box, stretch=1)

        self.setLayout(ana_layout)

    def portlari_yenile(self):
        self.port_combo.clear()
        portlar = serial.tools.list_ports.comports()
        if not portlar:
            self.port_combo.addItem("Hiçbir port bulunamadı")
        else:
            for p in portlar:
                self.port_combo.addItem(p.device)

    def connect_disconnect(self):
        if self.ser and self.ser.is_open:
            self.timer.stop()
            self.ser.close()
            self.ser = None
            self.connect_button.setText("🔗 Connect")
            self.raw_box.append("🔴 Bağlantı kapatıldı.")
        else:
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            try:
                self.ser = serial.Serial(port, baud, timeout=0)
                self.connect_button.setText("❌ Disconnect")
                self.raw_box.append(f"🟢 {port} bağlantısı kuruldu ({baud} baud)")
                self.timer.start(5)
            except Exception as e:
                QMessageBox.critical(self, "Bağlantı Hatası", str(e))

    def parse_hex_list(self, text):
        if not text:
            return []
        out = []
        parts = [p.strip() for p in text.split(",") if p.strip() != ""]
        for p in parts:
            try:
                out.append(int(p, 16))
            except ValueError:
                raise ValueError(f"'{p}' geçersiz değer (örn: 0x01 veya 1E)")
        return out

    def apply_targets(self):
        try:
            msgids = self.parse_hex_list(self.target_msgids_input.text())
        except ValueError as e:
            QMessageBox.warning(self, "Hata", str(e))
            return

        can_text = self.target_canid_input.text().strip()
        if can_text:
            try:
                canid = int(can_text, 16)
            except ValueError:
                QMessageBox.warning(self, "Hata", "Geçerli CAN ID girin (örn: 0x02)")
                return
            if not (0 <= canid <= 0xFF):
                QMessageBox.warning(self, "Hata", "CAN ID 0x00-0xFF aralığında olmalı.")
                return
        else:
            canid = None

        self.target_msgids = msgids
        self.target_canid = canid

        msg = f"Filtre uygulandı. MessageID'ler: {', '.join(hex(x) for x in self.target_msgids) if self.target_msgids else 'Tüm mesajlar'}; "
        msg += f"CAN ID: {hex(self.target_canid) if self.target_canid is not None else 'Hepsi'}"
        QMessageBox.information(self, "Filtre Ayarlandı", msg)

        self.filtered_box.clear()
        for combo, name in [
            (self.header_combo, "Header (0x63 0x73)"),
            (self.msgid_combo, "CamMessageId"),
            (self.canid_combo, "CanDevID"),
            (self.data_combo, "Data"),
            (self.end_combo, "End (0x59)"),
        ]:
            combo.clear()
            combo.addItem(name)

    def veri_oku(self):
        if self.ser and self.ser.is_open:
            try:
                veri = self.ser.read(64)
                if veri:
                    # Ham veri ekleme
                    self.raw_box.append(" ".join([f"0x{b:02X}" for b in veri]))
                    self.ascii_pencere.ascii_ekle_tum(veri)  # 🆕 tüm ascii’ye ekle
                    self.buffer += veri

                    while len(self.buffer) >= self.PAKET_BOYUTU:
                        if (self.buffer[0] == 0x63 and self.buffer[1] == 0x73 and
                                self.buffer[self.PAKET_BOYUTU - 1] == 0x59):
                            paket = self.buffer[:self.PAKET_BOYUTU]
                            self.buffer = self.buffer[self.PAKET_BOYUTU:]

                            header = paket[0:2]
                            msg_id_bytes = paket[2:4]
                            can_id = paket[4]
                            data = paket[5:self.PAKET_BOYUTU - 1]
                            end = paket[self.PAKET_BOYUTU - 1]

                            msg_id_val = int.from_bytes(msg_id_bytes, byteorder='big')

                            matches_msgid = True if not self.target_msgids else (msg_id_val in self.target_msgids)
                            matches_canid = True if self.target_canid is None else (can_id == self.target_canid)
                            matches = matches_msgid and matches_canid

                            if matches:
                                self.header_combo.addItem(f"0x{header[0]:02X} 0x{header[1]:02X}")
                                self.msgid_combo.addItem(f"0x{msg_id_bytes[0]:02X} 0x{msg_id_bytes[1]:02X} ({msg_id_val})")
                                self.canid_combo.addItem(f"0x{can_id:02X}")
                                self.data_combo.addItem(" ".join([f"0x{b:02X}" for b in data]))
                                self.end_combo.addItem(f"0x{end:02X}")

                                detay = (
                                    f"🎯 Paket: MsgID=0x{msg_id_val:02X} "
                                    f"CAN=0x{can_id:02X} Data={' '.join(f'0x{b:02X}' for b in data)}"
                                )
                                self.filtered_box.append(detay)

                                # 🆕 Filtreli ASCII’ye de ekle
                                self.ascii_pencere.ascii_ekle_filtreli(paket)
                        else:
                            self.buffer = self.buffer[1:]
            except serial.SerialException:
                self.timer.stop()
                QMessageBox.critical(self, "Bağlantı Hatası", "Seri port bağlantısı kesildi.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = SeriPortArayuzu()
    pencere.show()
    sys.exit(app.exec_())
    