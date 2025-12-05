import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    print("Creating tables...")

    # ✅ PERFECT: Users table (3 columns)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nickname TEXT NOT NULL,
            password TEXT NOT NULL
        );
    """)

    # ✅ PERFECT: Orders table (AUTO DATE!)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
    """)

    # ✅ PERFECT: Products table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            description TEXT,
            price REAL,
            image TEXT
        );
    """)

    # Clear ALL data for fresh start
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM orders")
    cur.execute("DELETE FROM users")

    # Insert ALL 60+ products (PERFECT)
    products = [
        ("10Ω Resistor", "Resistor", "10-ohm carbon film resistor", 2.00, "10r.png"),
        ("100Ω Resistor", "Resistor", "100-ohm resistor", 3.00, "100r.png"),
        ("220Ω Resistor", "Resistor", "220-ohm resistor", 2.00, "220r.png"),
        ("330Ω Resistor", "Resistor", "330-ohm resistor", 2.00, "330r.png"),
        ("1kΩ Resistor", "Resistor", "1k-ohm resistor", 4.00, "1kr.png"),
        ("10µF Capacitor", "Capacitor", "10µF electrolytic capacitor", 3.00, "10c.png"),
        ("22µF Capacitor", "Capacitor", "22µF electrolytic capacitor", 3.00, "22c.png"),
        ("47µF Capacitor", "Capacitor", "47µF electrolytic capacitor", 4.00, "47c.png"),
        ("100µF Capacitor", "Capacitor", "100µF electrolytic capacitor", 5.00, "100c.png"),
        ("220µF Capacitor", "Capacitor", "220µF electrolytic capacitor", 6.00, "220c.png"),
        ("1N4001 Diode", "Diode", "General purpose diode", 3.00, "4001d.png"),
        ("1N4007 Diode", "Diode", "General purpose diode", 3.00, "4007d.png"),
        ("1N4148 Diode", "Diode", "High-speed switching diode", 3.00, "4148d.png"),
        ("Zener 5.1V Diode", "Diode", "5.1V Zener diode", 4.00, "z5.1d.png"),
        ("Zener 12V Diode", "Diode", "12V Zener diode", 4.00, "z12d.png"),
        ("2N2222 Transistor", "Transistor", "NPN transistor", 5.00, "2n2t.png"),
        ("BC547 Transistor", "Transistor", "NPN small signal transistor", 4.00, "bc547t.png"),
        ("BC557 Transistor", "Transistor", "PNP small signal transistor", 4.00, "bc557t.png"),
        ("TIP120 Transistor", "Transistor", "NPN Darlington transistor", 6.00, "t120t.png"),
        ("TIP31 Transistor", "Transistor", "NPN power transistor", 6.00, "t31t.png"),
        ("555 Timer IC", "IC", "Timer IC for oscillators", 15.00, "555t.ic.png"),
        ("LM358 Op-Amp", "IC", "Dual operational amplifier", 18.00, "lm358.ic.png"),
        ("74HC00 IC", "IC", "Quad NAND gate IC", 20.00, "74H00.ic.png"),
        ("4017 Decade Counter IC", "IC", "Decade counter IC", 22.00, "4017.ic.png"),
        ("CD4040 Counter IC", "IC", "12-bit binary counter IC", 25.00, "cd4040.ic.png"),
        ("9V Battery", "Power", "Standard 9V battery", 25.00, "9vb.png"),
        ("5V Power Supply", "Power", "5V DC regulated power supply", 50.00, "5vb.png"),
        ("12V Power Supply", "Power", "12V DC regulated power supply", 60.00, "12vb.png"),
        ("Li-Ion 18650 Cell", "Power", "Rechargeable Li-Ion cell", 80.00, "ionb.png"),
        ("USB Power Module", "Power", "5V USB power module", 40.00, "usbpm.png"),
        ("Push Button", "Switch", "Momentary push button", 5.00, "pb.png"),
        ("Toggle Switch", "Switch", "SPDT toggle switch", 12.00, "ts.png"),
        ("Slide Switch", "Switch", "Slide switch", 10.00, "ss.png"),
        ("DIP Switch", "Switch", "4-position DIP switch", 8.00, "dips.png"),
        ("Rocker Switch", "Switch", "Rocker switch", 15.00, "rs.png"),
        ("Red LED", "LED", "Standard 5mm red LED", 2.00, "rled.png"),
        ("Green LED", "LED", "Standard 5mm green LED", 2.00, "gled.png"),
        ("Blue LED", "LED", "Standard 5mm blue LED", 2.00, "bled.png"),
        ("White LED", "LED", "Standard 5mm white LED", 2.00, "wled.png"),
        ("RGB LED", "LED", "5mm RGB LED", 5.00, "rgbled.png"),
        ("Jumper Wires", "Connector", "Male-Male jumper wires 30pcs", 40.00, "j1.png"),
        ("Female Dupont", "Connector", "Female connectors 30pcs", 35.00, "fmaled.png"),
        ("Male Header", "Connector", "Male header pins 40pcs", 30.00, "maleheader.png"),
        ("Female Header", "Connector", "Female header pins 40pcs", 30.00, "fmaleheader.png"),
        ("Terminal Block", "Connector", "2-pin terminal block 10pcs", 25.00, "tblock.png"),
        ("Relay Module", "Module", "5V 1-channel relay module", 45.00, "rmod.png"),
        ("L298 Motor Driver", "Module", "Dual H-bridge motor driver", 120.00, "l298dm.png"),
        ("Bluetooth Module", "Module", "Bluetooth communication module", 150.00, "btoothm.png"),
        ("WiFi Module", "Module", "WiFi ESP8266 module", 180.00, "wifim.png"),
        ("Ultrasonic Module", "Module", "HC-SR04 distance sensor", 100.00, "usonicm.png"),
        ("Arduino Uno", "Microcontroller", "ATmega328P development board", 350.00, "auno.png"),
        ("Arduino Nano", "Microcontroller", "ATmega328P Nano board", 300.00, "anano.png"),
        ("ESP8266", "Microcontroller", "WiFi development board", 300.00, "esp8266.png"),
        ("ESP32", "Microcontroller", "WiFi + Bluetooth development board", 600.00, "esp32.png"),
        ("Raspberry Pi Pico", "Microcontroller", "RP2040 development board", 350.00, "rberrypico.png"),
    ]

    cur.executemany("""
        INSERT INTO products (name, category, description, price, image)
        VALUES (?, ?, ?, ?, ?)
    """, products)

    conn.commit()
    print("✅ Database PERFECTLY initialized!")
    print("📅 Orders will AUTO-SAVE dates with CURRENT_TIMESTAMP!")
    conn.close()

if __name__ == "__main__":
    init_db()
