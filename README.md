# 📡 COM Port Okuma ve Paket Analiz Arayüzü

**PyQt5 tabanlı gelişmiş seri port okuma -- paket filtreleme -- ASCII
görüntüleme aracı**

Bu proje, Python'un **PyQt5** kütüphanesi ile geliştirilmiş bir **COM
port okuma uygulamasıdır**.\
Program; seri portlardan gelen ham veriyi okuyabilir, paket yapısına
göre çözebilir, MessageID/CANID filtrelerine göre ayrıştırabilir ve hem
HEX hem ASCII formatında kullanıcıya sunar.

------------------------------------------------------------------------

## ✨ Özellikler

### 🔌 COM Port Yönetimi

-   Mevcut portları otomatik listeleme\
-   Baud rate seçimi (4800 -- 921600 arası)\
-   Tek tuşla bağlan / bağlantıyı kapat

### 🧩 Paket Okuma & Ayrıştırma

Program sabit 14 byte uzunluğunda paketleri işler.

    Header (2 byte)  |  MsgID (2 byte)  | CAN ID (1 byte) |
    Data (10 byte) | End (1 byte)

-   Header: **0x63 0x73**\
-   End byte: **0x59**

### 🎯 Filtreleme Sistemi

-   Birden fazla **Message ID**
-   Tek bir **CAN ID**
-   Filtre uygulanmış paketlerin ayrı gösterimi

### 🔤 ASCII Penceresi

Uygulamada iki ayrı ASCII görünümü vardır:

  -----------------------------------------------------------------------
  Bölüm                      Açıklama
  -------------------------- --------------------------------------------
  **Tüm ASCII**              Gelen tüm ham verilerin ASCII karşılığı

  **Filtrelenmiş ASCII**     Sadece filtreye uyan paketlerin ASCII
                             görünümü
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 📦 Proje Dosyası

### 1️⃣ `AsciiPencere`

ASCII verilerin (tüm ve filtrelenmiş) gösterildiği pencere.

### 2️⃣ `SeriPortArayuzu`

Ana arayüz sınıfı: - Port seçimi - Baud rate - Paket çözme -
Filtreleme - Ham veri & filtreli veri gösterimi - ASCII penceresi
yönetimi

------------------------------------------------------------------------

## 📁 Kurulum

``` bash
pip install pyqt5 pyserial
```

------------------------------------------------------------------------

## ▶ Çalıştırma

``` bash
python COMport.py
```

------------------------------------------------------------------------

## 🧪 Paket Formatı

    63 73 | 01 0A | 02 | AA BB CC DD EE FF 11 22 33 44 | 59

  Alan       Byte   Açıklama
  ---------- ------ --------------
  Header     2      63 73
  MsgID      2      Büyük endian
  CAN ID     1      Cihaz ID
  Data       10     Ham veri
  End Byte   1      59

------------------------------------------------------------------------

## 🎯 Filtreleme Örnekleri

### Message ID:

    0x01,0x1E,10

### CAN ID:

    0x02

------------------------------------------------------------------------

## 📝 Lisans

