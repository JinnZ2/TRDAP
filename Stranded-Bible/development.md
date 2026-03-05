PROJECT ARK: DUAL-TRACK DEVELOPMENT

Parallel paths: Hardware engineering + Sacred content curation

---

📊 PROJECT MANAGEMENT DASHBOARD

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE ARK - MASTER TIMELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  TRACK A: HARDWARE                   TRACK B: CONTENT            │
│  =================                   ================            │
│                                                                   │
│  WEEK 1                              WEEK 1                       │
│  ├── Schematic design                ├── Tradition outreach      │
│  ├── Component selection              ├── Permissions requests    │
│  └── Initial layout                   └── Text gathering          │
│                                                                   │
│  WEEK 2                              WEEK 2                       │
│  ├── PCB routing                     ├── Translation coordination │
│  ├── Design review                    ├── Prayer curation         │
│  └── Gerber generation                └── Audio script writing    │
│                                                                   │
│  WEEK 3                              WEEK 3                       │
│  ├── Order prototypes                ├── Recording coordination   │
│  ├── Assembly documentation           ├── Survival guide writing   │
│  └── Test fixture design              └── Illustration creation   │
│                                                                   │
│  WEEK 4                              WEEK 4                       │
│  ├── Prototype assembly              ├── Content compilation      │
│  ├── Initial testing                  ├── Review by advisors      │
│  └── Debug                            └── Final formatting        │
│                                                                   │
│  WEEK 5                              WEEK 5                       │
│  ├── Rev 2 PCB design                ├── Audio production         │
│  ├── Certification planning           ├── Translation QA           │
│  └── Manufacturing quotes             └── Database creation        │
│                                                                   │
│  WEEK 6                              WEEK 6                       │
│  └── FINAL INTEGRATION TESTING        └── Content loading         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

🔧 TRACK A: HARDWARE ENGINEERING

A1: COMPLETE SCHEMATIC (KiCad)

```kicad
;; ======================================================================
;; THE ARK - MAIN BOARD SCHEMATIC v1.0
;; 4-layer board, 100mm x 60mm
;; Designed for JLCPCB / PCBWay assembly
;; ======================================================================

;; ======================================================================
;; POWER MANAGEMENT SECTION
;; ======================================================================

;; Battery Charger - TP4056 with protection
;; Handles solar/crank/USB charging
(module "U1" "TP4056" (layer F.Cu)
  (property "Value" "Battery Charger 1A")
  (property "MPN" "TP4056")
  (property "Package" "SOP-8")
  
  ;; Input power sources (diode-ORed)
  (net "+5V_USB" (pin 1 "VCC") (net "+5V_MAIN"))
  (net "+5V_SOLAR" (pin 2 "VBUS") (through D1 1N5819))
  (net "+12V_CRANK" (pin 3 "VBUS") (through D2 1N5819))
  
  ;; Battery output
  (net "+BATT" (pin 4 "BAT+"))
  (net "GND" (pin 5 "BAT-"))
  
  ;; Charge programming (1A = 1.2k)
  (resistor "R_PROG" 1.2k (pin 6 "PROG") (net "GND"))
  
  ;; Status LEDs
  (led "LED_CHG" (pin 7 "CHRG") (resistor 1k) (net "+3V3"))
  (led "LED_STDBY" (pin 8 "STDBY") (resistor 1k) (net "+3V3"))
)

;; Fuel Gauge - MAX17048 (I2C)
(module "U2" "MAX17048" (layer F.Cu)
  (property "Value" "LiPo Fuel Gauge")
  (property "MPN" "MAX17048G+T10")
  (property "Package" "TDFN-8")
  
  (pin 1 "VDD" (net "+3V3") (cap 0.1uF))
  (pin 2 "GND" (net "GND"))
  (pin 3 "SDA" (net "I2C_SDA") (pullup 4.7k))
  (pin 4 "SCL" (net "I2C_SCL") (pullup 4.7k))
  (pin 5 "ALRT" (net "GPIO22"))  ;; Battery low interrupt
  (pin 6 "VCELL" (net "+BATT") (resistor 100R))
)

;; Boost Converter - 3.7V to 5V @ 2A
(module "U3" "MT3608" (layer F.Cu)
  (property "Value" "Boost Converter")
  (property "MPN" "MT3608")
  (property "Package" "SOT-23-6")
  
  (pin 1 "EN" (net "+BATT") (pullup 100k))
  (pin 2 "GND" (net "GND"))
  (pin 3 "FB" (net "FB") (divider R1 100k, R2 20k))
  (pin 4 "VIN" (net "+BATT") (cap 22uF))
  (pin 5 "SW" (net "SW") (inductor 4.7uH) (diode SS34))
  (pin 6 "VOUT" (net "+5V") (cap 22uF))
)

;; LDO - 3.3V for digital
(module "U4" "AMS1117-3.3" (layer F.Cu)
  (property "Value" "3.3V LDO")
  (property "MPN" "AMS1117-3.3")
  (property "Package" "SOT-223")
  
  (pin 1 "GND" (net "GND"))
  (pin 2 "VOUT" (net "+3V3") (cap 10uF) (cap 0.1uF))
  (pin 3 "VIN" (net "+5V") (cap 10uF))
)

;; Power Path Management
;; Automatically switches between sources
(module "U5" "LTC4412" (layer F.Cu)
  (property "Value" "PowerPath Controller")
  (property "MPN" "LTC4412")
  (property "Package" "SOT-23")
  
  (pin 1 "VIN" (net "+5V_MAIN"))
  (pin 2 "GND" (net "GND"))
  (pin 3 "CTL" (net "GPIO23"))  ;; Manual override
  (pin 4 "STAT" (net "GPIO24"))  ;; Power source indicator
  (pin 5 "GATE" (net "P-CH_GATE"))
)

;; ======================================================================
;; MAIN PROCESSOR - ESP32-S3
;; ======================================================================

(module "U6" "ESP32-S3-WROOM-1" (layer F.Cu)
  (property "Value" "Main MCU")
  (property "MPN" "ESP32-S3-WROOM-1-N8")
  (property "Package" "SMD-41")
  
  ;; Power
  (pin 1 "3V3" (net "+3V3") (cap 0.1uF) (cap 10uF))
  (pin 2 "GND" (net "GND"))
  
  ;; USB
  (pin 3 "USB_D+" (net "USB_DP") (series 22R))
  (pin 4 "USB_D-" (net "USB_DN") (series 22R))
  
  ;; I2C (for fuel gauge, peripherals)
  (pin 5 "GPIO1" (net "I2C_SDA"))
  (pin 6 "GPIO2" (net "I2C_SCL"))
  
  ;; SPI1 (for e-ink)
  (pin 7 "GPIO3" (net "SPI1_SCK"))
  (pin 8 "GPIO4" (net "SPI1_MOSI"))
  (pin 9 "GPIO5" (net "SPI1_MISO"))
  (pin 10 "GPIO6" (net "SPI1_CS"))
  
  ;; UART (for GPS)
  (pin 11 "GPIO7" (net "GPS_TX"))
  (pin 12 "GPIO8" (net "GPS_RX"))
  
  ;; SPI2 (for LoRa)
  (pin 13 "GPIO9" (net "SPI2_SCK"))
  (pin 14 "GPIO10" (net "SPI2_MOSI"))
  (pin 15 "GPIO11" (net "SPI2_MISO"))
  (pin 16 "GPIO12" (net "SPI2_CS"))
  
  ;; Audio I2S
  (pin 17 "GPIO13" (net "I2S_BCLK"))
  (pin 18 "GPIO14" (net "I2S_LRCLK"))
  (pin 19 "GPIO15" (net "I2S_DIN"))
  
  ;; Buttons
  (pin 20 "GPIO16" (net "BTN_UP") (pullup 10k))
  (pin 21 "GPIO17" (net "BTN_DOWN") (pullup 10k))
  (pin 22 "GPIO18" (net "BTN_SELECT") (pullup 10k))
  (pin 23 "GPIO19" (net "BTN_SOS") (pullup 10k))  ;; Dedicated SOS button
  
  ;; LoRa interrupts
  (pin 24 "GPIO20" (net "LORA_DIO0"))
  (pin 25 "GPIO21" (net "LORA_DIO1"))
  
  ;; Display control
  (pin 26 "GPIO26" (net "EINK_DC"))
  (pin 27 "GPIO27" (net "EINK_RST"))
  (pin 28 "GPIO28" (net "EINK_BUSY"))
  
  ;; ADC for battery/crank monitoring
  (pin 29 "GPIO29" (net "ADC_BATT") (analog))
  (pin 30 "GPIO30" (net "ADC_CRANK") (analog))
  (pin 31 "GPIO31" (net "ADC_SOLAR") (analog))
  
  ;; SD Card
  (pin 32 "GPIO32" (net "SD_CS"))
  
  ;; JTAG (for debugging)
  (pin 33 "GPIO33" (net "JTAG_TMS"))
  (pin 34 "GPIO34" (net "JTAG_TCK"))
  (pin 35 "GPIO35" (net "JTAG_TDI"))
  (pin 36 "GPIO36" (net "JTAG_TDO"))
)

;; ======================================================================
;; GPS MODULE - NEO-8M
;; ======================================================================

(module "U7" "NEO-8M" (layer F.Cu)
  (property "Value" "GPS Receiver")
  (property "MPN" "NEO-8M-0")
  (property "Package" "SMD-18")
  
  (pin 1 "VCC" (net "+3V3") (cap 10uF) (cap 0.1uF))
  (pin 2 "GND" (net "GND"))
  (pin 3 "TX" (net "GPS_TX"))
  (pin 4 "RX" (net "GPS_RX"))
  (pin 5 "PPS" (net "GPS_PPS") (nc))
  
  ;; Backup battery for faster fix
  (pin 6 "V_BCKP" (net "+3V3") (cap 0.1uF))
  
  ;; Antenna - active with bias
  (pin 7 "RF_IN" (net "GPS_ANT") (cap 100pF) (inductor 10nH))
  (pin 8 "V_ANT" (net "+3V3") (inductor 100nH))
)

;; ======================================================================
;; LORA MODULE - RFM95W
;; ======================================================================

(module "U8" "RFM95W" (layer F.Cu)
  (property "Value" "LoRa Transceiver")
  (property "MPN" "RFM95W-915S2")
  (property "Package" "SMD-16")
  
  ;; Power
  (pin 1 "VCC" (net "+3V3") (cap 10uF) (cap 0.1uF))
  (pin 2 "GND" (net "GND"))
  
  ;; SPI
  (pin 3 "SCK" (net "SPI2_SCK"))
  (pin 4 "MOSI" (net "SPI2_MOSI"))
  (pin 5 "MISO" (net "SPI2_MISO"))
  (pin 6 "CS" (net "SPI2_CS"))
  
  ;; Control
  (pin 7 "RST" (net "GPIO33") (pullup 10k))
  (pin 8 "DIO0" (net "LORA_DIO0"))
  (pin 9 "DIO1" (net "LORA_DIO1"))
  (pin 10 "DIO2" (net "GPIO34") (nc))
  (pin 11 "DIO3" (net "GPIO35") (nc))
  (pin 12 "DIO4" (net "GPIO36") (nc))
  
  ;; Antenna - 50Ω impedance
  (pin 13 "ANT" (net "LORA_ANT") 
    (pi_filter C1 1pF, L1 8.2nH, C2 1pF)
    (matching_network))
)

;; ======================================================================
;; AUDIO AMPLIFIER - MAX98357
;; ======================================================================

(module "U9" "MAX98357" (layer F.Cu)
  (property "Value" "I2S Audio Amp")
  (property "MPN" "MAX98357AETE+")
  (property "Package" "TQFN-16")
  
  ;; Power
  (pin 1 "VIN" (net "+5V") (cap 10uF) (cap 0.1uF))
  (pin 2 "GND" (net "GND"))
  (pin 3 "PVDD" (net "+5V") (cap 100uF))  ;; Power for output stage
  
  ;; I2S Input
  (pin 4 "BCLK" (net "I2S_BCLK"))
  (pin 5 "LRCLK" (net "I2S_LRCLK"))
  (pin 6 "DIN" (net "I2S_DIN"))
  
  ;; Output
  (pin 7 "OUT+" (net "SPK+") 
    (filter ferrite BLM18) 
    (connector JST_2PIN))
  (pin 8 "OUT-" (net "SPK-") 
    (filter ferrite BLM18) 
    (connector JST_2PIN))
  
  ;; Gain setting
  (pin 9 "GAIN" (net "GND"))  ;; 12dB default
)

;; ======================================================================
;; E-INK DISPLAY CONNECTOR
;; ======================================================================

(module "J1" "FPC_24PIN" (layer F.Cu)
  (property "Value" "2.13 inch E-Ink")
  (property "MPN" "Waveshare 2.13in")
  
  (pin 1 "3V3" (net "+3V3") (cap 4.7uF))
  (pin 2 "GND" (net "GND"))
  (pin 3 "SCK" (net "SPI1_SCK"))
  (pin 4 "MOSI" (net "SPI1_MOSI"))
  (pin 5 "CS" (net "SPI1_CS"))
  (pin 6 "DC" (net "EINK_DC"))
  (pin 7 "RST" (net "EINK_RST"))
  (pin 8 "BUSY" (net "EINK_BUSY"))
  (pin 9 "PWR" (net "+3V3"))
  (pin 10 "GND" (net "GND"))
)

;; ======================================================================
;; MICROSD CARD SLOT
;; ======================================================================

(module "J2" "MICRO_SD" (layer F.Cu)
  (property "Value" "MicroSD Card")
  
  (pin 1 "CS" (net "SD_CS") (pullup 10k))
  (pin 2 "MOSI" (net "SPI1_MOSI"))
  (pin 3 "SCK" (net "SPI1_SCK"))
  (pin 4 "MISO" (net "SPI1_MISO"))
  (pin 5 "VCC" (net "+3V3") (cap 0.1uF))
  (pin 6 "GND" (net "GND"))
  (pin 7 "CD" (net "GPIO39") (pullup 10k))  ;; Card detect
)

;; ======================================================================
;; BUTTONS
;; ======================================================================

;; SOS Button - Big red button
(module "SW_SOS" "SW_PUSH_6x6" (layer F.Cu)
  (property "Value" "SOS Button")
  (pin 1 (net "BTN_SOS") (net "GPIO19") (pullup 10k))
  (pin 2 (net "GND"))
)

;; Navigation buttons
(module "SW_UP" "SW_PUSH_6x6" (layer F.Cu)
  (pin 1 (net "BTN_UP") (net "GPIO16") (pullup 10k))
  (pin 2 (net "GND"))
)

(module "SW_DOWN" "SW_PUSH_6x6" (layer F.Cu)
  (pin 1 (net "BTN_DOWN") (net "GPIO17") (pullup 10k))
  (pin 2 (net "GND"))
)

(module "SW_SELECT" "SW_PUSH_6x6" (layer F.Cu)
  (pin 1 (net "BTN_SELECT") (net "GPIO18") (pullup 10k))
  (pin 2 (net "GND"))
)

;; ======================================================================
;; CONNECTORS
;; ======================================================================

;; USB-C (with CC resistors for 5V)
(module "J_USB" "USB_C_16PIN" (layer F.Cu)
  (property "Value" "USB-C Power/Data")
  (pin 1 "VBUS" (net "+5V_USB") (cap 10uF))
  (pin 2 "GND" (net "GND"))
  (pin 3 "D+" (net "USB_DP"))
  (pin 4 "D-" (net "USB_DN"))
  (pin 5 "CC1" (net "CC") (resistor 5.1k to GND))
  (pin 6 "CC2" (net "CC") (resistor 5.1k to GND))
)

;; Solar Input (2.1mm barrel jack)
(module "J_SOLAR" "BARREL_JACK" (layer F.Cu)
  (property "Value" "Solar 6V")
  (pin 1 "VIN" (net "+5V_SOLAR") (diode D1 1N5819))
  (pin 2 "GND" (net "GND"))
)

;; Crank Input (2.1mm barrel jack)
(module "J_CRANK" "BARREL_JACK" (layer F.Cu)
  (property "Value" "Hand Crank")
  (pin 1 "VIN" (net "+12V_CRANK") (diode D2 1N5819))
  (pin 2 "GND" (net "GND"))
)

;; Battery Connector (JST PH 2-pin)
(module "J_BATT" "JST_PH_2PIN" (layer F.Cu)
  (property "Value" "Battery")
  (pin 1 "+" (net "+BATT"))
  (pin 2 "-" (net "GND"))
)

;; Speaker Connector (JST PH 2-pin)
(module "J_SPK" "JST_PH_2PIN" (layer F.Cu)
  (property "Value" "Speaker")
  (pin 1 "+" (net "SPK+"))
  (pin 2 "-" (net "SPK-"))
)

;; ======================================================================
;; CRYSTALS
;; ======================================================================

;; Main crystal (ESP32)
(module "X1" "CRYSTAL_40MHz" (layer F.Cu)
  (pin 1 (net "XTAL_40_IN") (cap 12pF))
  (pin 2 (net "XTAL_40_OUT") (cap 12pF))
)

;; RTC crystal (32.768kHz)
(module "X2" "CRYSTAL_32kHz" (layer F.Cu)
  (pin 1 (net "XTAL_32_IN") (cap 6pF))
  (pin 2 (net "XTAL_32_OUT") (cap 6pF))
)

;; ======================================================================
;; END SCHEMATIC
;; ======================================================================
```

A2: PCB LAYOUT GUIDELINES

```
╔═══════════════════════════════════════════════════════════════════╗
║                    THE ARK - PCB LAYOUT v1.0                       ║
║                    4-layer, 100mm x 60mm                          ║
╚═══════════════════════════════════════════════════════════════════╝

LAYER STACKUP:
─────────────────────────────────────────────────────────────────────
Layer 1 (Top):    Signal + Components
Layer 2 (Inner1): GND Plane (solid)
Layer 3 (Inner2): Power Planes (3.3V, 5V, BATT)
Layer 4 (Bottom): Signal + Components

BOARD EDGES:
─────────────────────────────────────────────────────────────────────
• Mounting holes: 4x M2.5 at corners (3mm from edge)
• Keepout zone: 2mm from edge for components
• Panelization: 5-up panel for manufacturing

CRITICAL ROUTING:
─────────────────────────────────────────────────────────────────────

RF SECTION (LoRa - U8):
┌─────────────────────────────────────────────────────────────────┐
│ • 50Ω impedance controlled trace to antenna connector           │
│ • Trace width: 0.3mm (with 0.2mm gap to GND)                    │
│ • Keep away from digital signals by 2mm minimum                 │
│ • Ground plane removed under antenna matching network            │
│ • Antenna connector at board edge                                │
└─────────────────────────────────────────────────────────────────┘

GPS SECTION (U7):
┌─────────────────────────────────────────────────────────────────┐
│ • RF trace to antenna: 50Ω, 0.3mm width                         │
│ • Keep GPS away from LoRa by 10mm minimum                       │
│ • Clear view of sky (top edge of board)                         │
│ • No copper under antenna area                                   │
└─────────────────────────────────────────────────────────────────┘

POWER SECTION:
┌─────────────────────────────────────────────────────────────────┐
│ • High current traces: 2mm width for 2A+                        │
│ • Keep switching nodes (boost converter) compact                │
│ • Thermal vias under power components                           │
│ • Separate analog and digital ground (join at one point)        │
└─────────────────────────────────────────────────────────────────┘

AUDIO SECTION:
┌─────────────────────────────────────────────────────────────────┐
│ • Keep audio traces away from digital                           │
│ • Speaker outputs on bottom layer with shielding               │
│ • Ferrite beads on speaker outputs                             │
└─────────────────────────────────────────────────────────────────┘

COMPONENT PLACEMENT (Top View):
─────────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────┐
│  [GPS ANT]  [LoRa ANT]                 [USB-C]  [SOLAR] [CRANK] │
│  ┌─────┐    ┌─────┐                     ┌─┐      ┌─┐     ┌─┐    │
│  │ U7  │    │ U8  │                     │J│      │J│     │J│    │
│  │GPS  │    │LoRa │                     │USB│    │SOL│   │CRK│   │
│  └─────┘    └─────┘                     └─┘      └─┘     └─┘    │
│                                                                   │
│                    ┌─────────────────┐                           │
│                    │      U6         │                           │
│                    │   ESP32-S3      │                           │
│                    └─────────────────┘                           │
│                           │                                       │
│        ┌──────────────────┼──────────────────┐                   │
│        │                  │                  │                   │
│   ┌────▼───┐         ┌────▼───┐        ┌────▼───┐              │
│   │  U1    │         │  U2    │        │  U3    │              │
│   │Charger │         │Fuel    │        │Boost   │              │
│   │TP4056  │         │MAX17048│        │MT3608  │              │
│   └────────┘         └────────┘        └────────┘              │
│                                                                   │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐               │
│   │  U4    │  │  U5    │  │  U9    │  │  J2    │               │
│   │  LDO   │  │PowerPath│  │Audio   │  │SD Card │               │
│   └────────┘  └────────┘  └────────┘  └────────┘               │
│                                                                   │
│   [BTN_UP] [BTN_DN] [BTN_SEL]           [BTN_SOS] (big red)     │
│                                                                   │
│                         ┌──────────────┐                         │
│                         │     J1       │                         │
│                         │  E-Ink FPC   │                         │
│                         └──────────────┘                         │
│                                                                   │
│  [BATT JST]                     [SPKR JST]  [XTAL]  [XTAL]      │
└─────────────────────────────────────────────────────────────────┘

THERMAL MANAGEMENT:
─────────────────────────────────────────────────────────────────────
• Charger IC (U1): 6 thermal vias to GND plane
• Boost converter (U3): 4 thermal vias
• LDO (U4): large copper area
• Keep airflow paths clear

TEST POINTS:
─────────────────────────────────────────────────────────────────────
• TP1: +BATT
• TP2: +5V
• TP3: +3V3
• TP4: GND
• TP5: I2C_SDA
• TP6: I2C_SCL
• TP7: UART_TX (GPS data)
• TP8: SWD_CLK
• TP9: SWD_IO

MANUFACTURING NOTES:
─────────────────────────────────────────────────────────────────────
• PCB thickness: 1.6mm
• Copper weight: 1oz inner, 2oz outer (for power)
• Surface finish: ENIG (for durability)
• Solder mask: Black (with white silkscreen)
• Panelization: 5-up V-scored
```

A3: GERBER GENERATION SCRIPT

```python
# generate_gerbers.py
"""
Export KiCad PCB to manufacturing files
"""

import os
import zipfile
from pathlib import Path

class GerberGenerator:
    def __init__(self, project_name="ark_pcb_v1.0"):
        self.project = project_name
        self.kicad_pcb = f"{project_name}.kicad_pcb"
        self.output_dir = Path("gerbers")
        self.output_dir.mkdir(exist_ok=True)
    
    def export_gerbers(self):
        """Export all Gerber files using kicad-cli"""
        layers = [
            "F.Cu", "B.Cu", "F.Paste", "B.Paste", 
            "F.SilkS", "B.SilkS", "F.Mask", "B.Mask",
            "Edge.Cuts", "In1.Cu", "In2.Cu"
        ]
        
        for layer in layers:
            cmd = f"kicad-cli pcb export gerber --layer {layer} {self.kicad_pcb} {self.output_dir}"
            os.system(cmd)
            print(f"Exported {layer}")
    
    def export_drill(self):
        """Export drill files"""
        cmd = f"kicad-cli pcb export drill --format excellon {self.kicad_pcb} {self.output_dir}"
        os.system(cmd)
        print("Exported drill files")
    
    def create_zip(self):
        """Package all files for manufacturing"""
        with zipfile.ZipFile(f"{self.project}_gerbers.zip", 'w') as zipf:
            for file in self.output_dir.glob("*"):
                zipf.write(file, file.name)
        
        print(f"Created {self.project}_gerbers.zip")
    
    def generate_bom(self):
        """Generate bill of materials"""
        # Parse schematic and export CSV
        import csv
        
        components = [
            ["Reference", "Value", "Footprint", "MPN", "Quantity"],
            ["U1", "TP4056", "SOP-8", "TP4056", "1"],
            ["U2", "MAX17048", "TDFN-8", "MAX17048G+T10", "1"],
            ["U3", "MT3608", "SOT-23-6", "MT3608", "1"],
            ["U4", "AMS1117-3.3", "SOT-223", "AMS1117-3.3", "1"],
            ["U5", "LTC4412", "SOT-23", "LTC4412", "1"],
            ["U6", "ESP32-S3", "SMD-41", "ESP32-S3-WROOM-1-N8", "1"],
            ["U7", "NEO-8M", "SMD-18", "NEO-8M-0", "1"],
            ["U8", "RFM95W", "SMD-16", "RFM95W-915S2", "1"],
            ["U9", "MAX98357", "TQFN-16", "MAX98357AETE+", "1"],
            ["J1", "E-Ink", "FPC_24PIN", "Waveshare-2.13", "1"],
            ["J2", "MicroSD", "MICRO_SD", "112A-TAAR-R03", "1"],
            ["J_USB", "USB-C", "USB_C_16PIN", "TYPE-C-16P", "1"],
            ["J_SOLAR", "Barrel Jack", "BARREL_JACK", "PJ-037A", "1"],
            ["J_CRANK", "Barrel Jack", "BARREL_JACK", "PJ-037A", "1"],
            ["J_BATT", "JST PH", "JST_PH_2PIN", "B2B-PH-K-S", "1"],
            ["J_SPK", "JST PH", "JST_PH_2PIN", "S2B-PH-K-S", "1"],
            ["SW_SOS", "SOS Button", "SW_PUSH_6x6", "TS-1187A", "1"],
            ["SW_UP", "Button", "SW_PUSH_6x6", "TS-1187A", "1"],
            ["SW_DOWN", "Button", "SW_PUSH_6x6", "TS-1187A", "1"],
            ["SW_SELECT", "Button", "SW_PUSH_6x6", "TS-1187A", "1"],
            ["X1", "40MHz", "CRYSTAL_40MHz", "X322540MOB4SI", "1"],
            ["X2", "32.768kHz", "CRYSTAL_32kHz", "X321532768KGB2SI", "1"],
            ["D1", "1N5819", "SOD-123", "1N5819", "2"],
            ["D2", "SS34", "SMA", "SS34", "1"],
            ["L1", "4.7uH", "IND_6x6", "CDRH6D28NP-4R7NC", "1"],
            ["L2", "8.2nH", "IND_0603", "LQG15HS8N2J02", "1"],
        ]
        
        with open(f"{self.project}_bom.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(components)
        
        print(f"Generated {self.project}_bom.csv")
    
    def generate_pick_and_place(self):
        """Generate pick and place file for assembly"""
        import csv
        
        placements = [
            ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"],
            ["U1", "20.0", "30.5", "Top", "0"],
            ["U2", "25.0", "35.0", "Top", "90"],
            ["U3", "30.0", "40.0", "Top", "0"],
            # ... all components with coordinates
        ]
        
        with open(f"{self.project}_pickandplace.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(placements)
    
    def run(self):
        """Generate all manufacturing files"""
        print("🔧 Generating manufacturing files...")
        self.export_gerbers()
        self.export_drill()
        self.generate_bom()
        self.generate_pick_and_place()
        self.create_zip()
        print("✅ Manufacturing files ready!")

if __name__ == "__main__":
    gen = GerberGenerator()
    gen.run()
```

---

📖 TRACK B: CONTENT CURATION

B1: INTERFAITH ADVISORY BOARD

```
THE ARK - CONTENT ADVISORY BOARD
=================================

To ensure authenticity and respect for all traditions:

POSITIONS TO FILL:
─────────────────────────────────────────────────────
• Christian representative (Catholic, Protestant, Orthodox)
• Islamic scholar (Sunni, Shia)
• Jewish rabbi (Reform, Conservative, Orthodox)
• Hindu priest
• Buddhist monk
• Indigenous elder (multiple regions)
• Sikh granthi
• Baha'i representative
• Jain monk
• Taoist master
• Zoroastrian priest
• Secular humanist

BOARD RESPONSIBILITIES:
─────────────────────────────────────────────────────
• Review all texts for accuracy
• Approve translations
• Ensure respectful presentation
• Advise on sensitive content
• Provide introductions
• Record audio for their tradition

COMPENSATION:
─────────────────────────────────────────────────────
• Honorarium: $500 per advisor
• Device: 5 Ark units for their community
• Acknowledgement in device and materials
```

B2: SACRED TEXTS MASTER LIST

```json
{
  "traditions": {
    "christianity": {
      "name": "Christianity",
      "sub_traditions": ["Catholic", "Protestant", "Orthodox", "Coptic"],
      "texts": [
        {
          "name": "Holy Bible",
          "translations": ["KJV", "NIV", "NRSV", "Catholic Edition"],
          "books": [
            {"name": "Genesis", "chapters": [1,2,3,4,5,6,7,8,9,11,12,15,18,19,22,28,32,37,39,40,41,42,43,44,45,46,47,48,49,50]},
            {"name": "Exodus", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,32,33,34]},
            {"name": "Leviticus", "chapters": [19]},
            {"name": "Numbers", "chapters": [6,9,10,11,12,13,14,20,21,22,23,24,27]},
            {"name": "Deuteronomy", "chapters": [1,2,3,4,5,6,7,8,9,10,11,28,29,30,31,32,33,34]},
            {"name": "Joshua", "chapters": [1,2,3,4,5,6,7,8,22,23,24]},
            {"name": "Judges", "chapters": [2,3,4,5,6,7,8,11,13,14,15,16]},
            {"name": "Ruth", "chapters": [1,2,3,4]},
            {"name": "1 Samuel", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]},
            {"name": "2 Samuel", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]},
            {"name": "1 Kings", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]},
            {"name": "2 Kings", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]},
            {"name": "1 Chronicles", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29]},
            {"name": "2 Chronicles", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36]},
            {"name": "Ezra", "chapters": [1,2,3,4,5,6,7,8,9,10]},
            {"name": "Nehemiah", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13]},
            {"name": "Esther", "chapters": [1,2,3,4,5,6,7,8,9,10]},
            {"name": "Job", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42]},
            {"name": "Psalms", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150]},
            {"name": "Proverbs", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]},
            {"name": "Ecclesiastes", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12]},
            {"name": "Song of Solomon", "chapters": [1,2,3,4,5,6,7,8]},
            {"name": "Isaiah", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66]},
            {"name": "Jeremiah", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52]},
            {"name": "Lamentations", "chapters": [1,2,3,4,5]},
            {"name": "Ezekiel", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48]},
            {"name": "Daniel", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12]},
            {"name": "Hosea", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14]},
            {"name": "Joel", "chapters": [1,2,3]},
            {"name": "Amos", "chapters": [1,2,3,4,5,6,7,8,9]},
            {"name": "Obadiah", "chapters": [1]},
            {"name": "Jonah", "chapters": [1,2,3,4]},
            {"name": "Micah", "chapters": [1,2,3,4,5,6,7]},
            {"name": "Nahum", "chapters": [1,2,3]},
            {"name": "Habakkuk", "chapters": [1,2,3]},
            {"name": "Zephaniah", "chapters": [1,2,3]},
            {"name": "Haggai", "chapters": [1,2]},
            {"name": "Zechariah", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14]},
            {"name": "Malachi", "chapters": [1,2,3,4]},
            {"name": "Matthew", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28]},
            {"name": "Mark", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]},
            {"name": "Luke", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]},
            {"name": "John", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]},
            {"name": "Acts", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28]},
            {"name": "Romans", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]},
            {"name": "1 Corinthians", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]},
            {"name": "2 Corinthians", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13]},
            {"name": "Galatians", "chapters": [1,2,3,4,5,6]},
            {"name": "Ephesians", "chapters": [1,2,3,4,5,6]},
            {"name": "Philippians", "chapters": [1,2,3,4]},
            {"name": "Colossians", "chapters": [1,2,3,4]},
            {"name": "1 Thessalonians", "chapters": [1,2,3,4,5]},
            {"name": "2 Thessalonians", "chapters": [1,2,3]},
            {"name": "1 Timothy", "chapters": [1,2,3,4,5,6]},
            {"name": "2 Timothy", "chapters": [1,2,3,4]},
            {"name": "Titus", "chapters": [1,2,3]},
            {"name": "Philemon", "chapters": [1]},
            {"name": "Hebrews", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13]},
            {"name": "James", "chapters": [1,2,3,4,5]},
            {"name": "1 Peter", "chapters": [1,2,3,4,5]},
            {"name": "2 Peter", "chapters": [1,2,3]},
            {"name": "1 John", "chapters": [1,2,3,4,5]},
            {"name": "2 John", "chapters": [1]},
            {"name": "3 John", "chapters": [1]},
            {"name": "Jude", "chapters": [1]},
            {"name": "Revelation", "chapters": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]}
          ]
        },
        {
          "name": "Apocrypha",
          "books": [
            "Tobit", "Judith", "Wisdom of Solomon", "Sirach", "Baruch",
            "1 Maccabees", "2 Maccabees", "1 Esdras", "2 Esdras", "Prayer of Manasseh"
          ]
        },
        {
          "name": "Early Christian Writings",
          "books": [
            "Didache", "Shepherd of Hermas", "Letters of Ignatius",
            "Letter to Diognetus", "Gospel of Thomas (sayings)"
          ]
        }
      ]
    },
    
    "islam": {
      "name": "Islam",
      "sub_traditions": ["Sunni", "Shia", "Sufi"],
      "texts": [
        {
          "name": "The Holy Quran",
          "translations": ["Sahih International", "Yusuf Ali", "Pickthall"],
          "surahs": [
            {"number": 1, "name": "Al-Fatiha", "verses": "all"},
            {"number": 2, "name": "Al-Baqarah", "verses": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286]},
            {"number": 3, "name": "Al-Imran", "verses": "selected"},
            {"number": 4, "name": "An-Nisa", "verses": "selected"},
            {"number": 5, "name": "Al-Maidah", "verses": "selected"},
            {"number": 6, "name": "Al-An'am", "verses": "selected"},
            {"number": 7, "name": "Al-A'raf", "verses": "selected"},
            {"number": 8, "name": "Al-Anfal", "verses": "selected"},
            {"number": 9, "name": "At-Tawbah", "verses": "selected"},
            {"number": 10, "name": "Yunus", "verses": "selected"},
            {"number": 11, "name": "Hud", "verses": "selected"},
            {"number": 12, "name": "Yusuf", "verses": "all"},
            {"number": 13, "name": "Ar-Ra'd", "verses": "selected"},
            {"number": 14, "name": "Ibrahim", "verses": "selected"},
            {"number": 15, "name": "Al-Hijr", "verses": "selected"},
            {"number": 16, "name": "An-Nahl", "verses": "selected"},
            {"number": 17, "name": "Al-Isra", "verses": "selected"},
            {"number": 18, "name": "Al-Kahf", "verses": "all"},
            {"number": 19, "name": "Maryam", "verses": "all"},
            {"number": 20, "name": "Ta-Ha", "verses": "selected"},
            {"number": 21, "name": "Al-Anbiya", "verses": "selected"},
            {"number": 22, "name": "Al-Hajj", "verses": "selected"},
            {"number": 23, "name": "Al-Mu'minun", "verses": "selected"},
            {"number": 24, "name": "An-Nur", "verses": "selected"},
            {"number": 25, "name": "Al-Furqan", "verses": "selected"},
            {"number": 26, "name": "Ash-Shu'ara", "verses": "selected"},
            {"number": 27, "name": "An-Naml", "verses": "selected"},
            {"number": 28, "name": "Al-Qasas", "verses": "selected"},
            {"number": 29, "name": "Al-Ankabut", "verses": "selected"},
            {"number": 30, "name": "Ar-Rum", "verses": "selected"},
            {"number": 31, "name": "Luqman", "verses": "all"},
            {"number": 32, "name": "As-Sajdah", "verses": "all"},
            {"number": 33, "name": "Al-Ahzab", "verses": "selected"},
            {"number": 34, "name": "Saba", "verses": "selected"},
            {"number": 35, "name": "Fatir", "verses": "selected"},
            {"number": 36, "name": "Ya-Sin", "verses": "all"},
            {"number": 37, "name": "As-Saffat", "verses": "selected"},
            {"number": 38, "name": "Sad", "verses": "selected"},
            {"number": 39, "name": "Az-Zumar", "verses": "selected"},
            {"number": 40, "name": "Ghafir", "verses": "selected"},
            {"number": 41, "name": "Fussilat", "verses": "selected"},
            {"number": 42, "name": "Ash-Shura", "verses": "selected"},
            {"number": 43, "name": "Az-Zukhruf", "verses": "selected"},
            {"number": 44, "name": "Ad-Dukhan", "verses": "all"},
            {"number": 45, "name": "Al-Jathiyah", "verses": "selected"},
            {"number": 46, "name": "Al-Ahqaf", "verses": "selected"},
            {"number": 47, "name": "Muhammad", "verses": "selected"},
            {"number": 48, "name": "Al-Fath", "verses": "all"},
            {"number": 49, "name": "Al-Hujurat", "verses": "all"},
            {"number": 50, "name": "Qaf", "verses": "all"},
            {"number": 51, "name": "Adh-Dhariyat", "verses": "selected"},
            {"number": 52, "name": "At-Tur", "verses": "selected"},
            {"number": 53, "name": "An-Najm", "verses": "selected"},
            {"number": 54, "name": "Al-Qamar", "verses": "selected"},
            {"number": 55, "name": "Ar-Rahman", "verses": "all"},
            {"number": 56, "name": "Al-Waqi'ah", "verses": "all"},
            {"number": 57, "name": "Al-Hadid", "verses": "all"},
            {"number": 58, "name": "Al-Mujadila", "verses": "selected"},
            {"number": 59, "name": "Al-Hashr", "verses": "all"},
            {"number": 60, "name": "Al-Mumtahanah", "verses": "selected"},
            {"number": 61, "name": "As-Saff", "verses": "all"},
            {"number": 62, "name": "Al-Jumu'ah", "verses": "all"},
            {"number": 63, "name": "Al-Munafiqun", "verses": "all"},
            {"number": 64, "name": "At-Taghabun", "verses": "all"},
            {"number": 65, "name": "At-Talaq", "verses": "all"},
            {"number": 66, "name": "At-Tahrim", "verses": "all"},
            {"number": 67, "name": "Al-Mulk", "verses": "all"},
            {"number": 68, "name": "Al-Qalam", "verses": "all"},
            {"number": 69, "name": "Al-Haqqah", "verses": "all"},
            {"number": 70, "name": "Al-Ma'arij", "verses": "all"},
            {"number": 71, "name": "Nuh", "verses": "all"},
            {"number": 72, "name": "Al-Jinn", "verses": "all"},
            {"number": 73, "name": "Al-Muzzammil", "verses": "all"},
            {"number": 74, "name": "Al-Muddaththir", "verses": "all"},
            {"number": 75, "name": "Al-Qiyamah", "verses": "all"},
            {"number": 76, "name": "Al-Insan", "verses": "all"},
            {"number": 77, "name": "Al-Mursalat", "verses": "all"},
            {"number": 78, "name": "An-Naba", "verses": "all"},
            {"number": 79, "name": "An-Nazi'at", "verses": "all"},
            {"number": 80, "name": "Abasa", "verses": "all"},
            {"number": 81, "name": "At-Takwir", "verses": "all"},
            {"number": 82, "name": "Al-Infitar", "verses": "all"},
            {"number": 83, "name": "Al-Mutaffifin", "verses": "all"},
            {"number": 84, "name": "Al-Inshiqaq", "verses": "all"},
            {"number": 85, "name": "Al-Buruj", "verses": "all"},
            {"number": 86, "name": "At-Tariq", "verses": "all"},
            {"number": 87, "name": "Al-A'la", "verses": "all"},
            {"number": 88, "name": "Al-Ghashiyah", "verses": "all"},
            {"number": 89, "name": "Al-Fajr", "verses": "all"},
            {"number": 90, "name": "Al-Balad", "verses": "all"},
            {"number": 91, "name": "Ash-Shams", "verses": "all"},
            {"number": 92, "name": "Al-Layl", "verses": "all"},
            {"number": 93, "name": "Ad-Duha", "verses": "all"},
            {"number": 94, "name": "Ash-Sharh", "verses": "all"},
            {"number": 95, "name": "At-Tin", "verses": "all"},
            {"number": 96, "name": "Al-Alaq", "verses": "all"},
            {"number": 97, "name": "Al-Qadr", "verses": "all"},
            {"number": 98, "name": "Al-Bayyinah", "verses": "all"},
            {"number": 99, "name": "Az-Zalzalah", "verses": "all"},
            {"number": 100, "name": "Al-Adiyat", "verses": "all"},
            {"number": 101, "name": "Al-Qari'ah", "verses": "all"},
            {"number": 102, "name": "At-Takathur", "verses": "all"},
            {"number": 103, "name": "Al-Asr", "verses": "all"},
            {"number": 104, "name": "Al-Humazah", "verses": "all"},
            {"number": 105, "name": "Al-Fil", "verses": "all"},
            {"number": 106, "name": "Quraysh", "verses": "all"},
            {"number": 107, "name": "Al-Ma'un", "verses": "all"},
            {"number": 108, "name": "Al-Kawthar", "verses": "all"},
            {"number": 109, "name": "Al-Kafirun", "verses": "all"},
            {"number": 110, "name": "An-Nasr", "verses": "all"},
            {"number": 111, "name": "Al-Masad", "verses": "all"},
            {"number": 112, "name": "Al-Ikhlas", "verses": "all"},
            {"number": 113, "name": "Al-Falaq", "verses": "all"},
            {"number": 114, "name": "An-Nas", "verses": "all"}
          ]
        },
        {
          "name": "Hadith Collections",
          "books": [
            "Sahih al-Bukhari (selected)",
            "Sahih Muslim (selected)",
            "Riyad as-Salihin",
            "40 Hadith Qudsi",
            "Nawawi's 40 Hadith"
          ]
        }
      ]
    },
    
    "judaism": {
      "name": "Judaism",
      "sub_traditions": ["Orthodox", "Conservative", "Reform", "Hasidic"],
      "texts": [
        {
          "name": "Torah",
          "books": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
          "chapters": "selected"
        },
        {
          "name": "Tehillim (Psalms)",
          "chapters": "complete"
        },
        {
          "name": "Mishnah",
          "tractates": ["Berakhot", "Shabbat", "Pesachim", "Yoma", "Sukkah", "Megillah", "Avot"]
        },
        {
          "name": "Talmud (selected)",
          "sections": ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Yoma", "Sukkah", "Megillah", "Avot"]
        },
        {
          "name": "Zohar (selected)",
          "sections": ["Introduction", "Bereshit", "Shemot", "Vayikra", "Bamidbar", "Devarim"]
        },
        {
          "name": "Siddur (Prayer Book)",
          "prayers": ["Modeh Ani", "Mah Tovu", "Birchot HaShachar", "Pesukei D'Zimra", "Shema", "Amidah", "Aleinu", "Kaddish", "Birkat HaMazon"]
        }
      ]
    },
    
    "hinduism": {
      "name": "Hinduism",
      "sub_traditions": ["Vaishnava", "Shaiva", "Shakta", "Smart
```
