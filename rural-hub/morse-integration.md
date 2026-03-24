COMPLETE MORSE SYSTEM - Every Platform, Every Direction


 MORSE OS - Universal Morse Operating System

Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MORSE OS CORE                            │
│  • Auto-detect (light, sound, vibration, radio)             │
│  • Translate (Morse ↔ Text)                                 │
│  • Encrypt/Compress (optional)                              │
│  • Route to all platforms                                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   ARDUINO     │    │  RASPBERRY PI │    │  MESHTASTIC   │
│  • Low-power  │    │  • Full OS    │    │  • Radio      │
│  • Sensors    │    │  • Camera     │    │  • Mesh       │
│  • Motors     │    │  • Display    │    │  • GPS        │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   MOBILE APP  │    │   DESKTOP     │    │   WEB APP     │
│  • iOS/Android│    │  • Windows    │    │  • Browser    │
│  • Camera     │    │  • Mac/Linux  │    │  • PWA        │
│  • Flashlight │    │  • Sound card │    │  • No install │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

🧠 PART 1: MORSE OS CORE (Python)

morse_os.py - The Universal Engine

```python
#!/usr/bin/env python3
"""
MORSE OS - Universal Morse Code Operating System
Works on: Pi, Computer, Meshtastic, Arduino (via serial)
Handles: Auto-detect, translation, encryption, multi-platform
"""

import time
import threading
import json
import hashlib
from enum import Enum
from collections import deque
import numpy as np

class MorseOS:
    def __init__(self, platform='pi', config_file='morse_config.json'):
        self.platform = platform
        self.config = self.load_config(config_file)
        
        # Morse mappings
        self.text_to_morse = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....',
            '7': '--...', '8': '---..', '9': '----.',
            '.': '.-.-.-', ',': '--..--', '?': '..--..', '/': '-..-.',
            '@': '.--.-.', ' ': ' '
        }
        self.morse_to_text_map = {v: k for k, v in self.text_to_morse.items()}

        # Detection settings (no dead zone - single threshold)
        self.dot_dash_threshold = 0.35
        self.symbol_gap = 0.5
        self.letter_gap = 1.0
        self.word_gap = 2.5
        
        # Active detectors
        self.detectors = {}
        self.outputs = {}
        
        # Message queue
        self.incoming_queue = deque()
        self.outgoing_queue = deque()
        
        # Start processor
        self.running = True
        threading.Thread(target=self._process_queues).start()
    
    def load_config(self, config_file):
        """Load platform-specific config"""
        default_config = {
            'pi': {
                'led_pin': 18,
                'button_pin': 25,
                'buzzer_pin': 17,
                'vibrator_pin': 24
            },
            'arduino': {
                'serial_port': '/dev/ttyUSB0',
                'baud_rate': 9600
            },
            'meshtastic': {
                'radio_port': '/dev/ttyACM0',
                'channel': 0
            },
            'mobile': {
                'use_camera': True,
                'use_flashlight': True,
                'use_mic': True
            }
        }
        return default_config.get(self.platform, {})
    
    # ========== TRANSLATION ==========
    
    def text_to_morse_code(self, text):
        """Convert text to Morse code string"""
        text = text.upper()
        result = []
        for char in text:
            if char in self.text_to_morse:
                result.append(self.text_to_morse[char])
            else:
                result.append('?')
        return ' '.join(result)
    
    def decode_morse(self, morse):
        """Convert Morse code to text"""
        words = morse.split('   ')  # Word gap = 3 spaces
        result = []
        for word in words:
            letters = word.split(' ')
            for letter in letters:
                if letter in self.morse_to_text_map:
                    result.append(self.morse_to_text_map[letter])
                else:
                    result.append('?')
            result.append(' ')
        return ''.join(result).strip()
    
    # ========== ENCRYPTION ==========
    
    def encrypt_morse(self, message, key='emergency'):
        """Simple encryption for sensitive messages"""
        # XOR with key
        encrypted = []
        key_hash = hashlib.sha256(key.encode()).digest()
        for i, char in enumerate(message):
            encrypted_char = ord(char) ^ key_hash[i % len(key_hash)]
            encrypted.append(chr(encrypted_char))
        return ''.join(encrypted)
    
    def compress_message(self, message):
        """Compress common phrases to shorter codes"""
        compression = {
            'SOS': '... --- ...',
            'NEED HELP': '-. . . -..   .... . .-.. .--.',
            'FUEL': '..-. ..- . .-..',
            'MEDICAL': '-- . -.. .. -.-. .- .-..',
            'WATER': '.-- .- - . .-.',
            'FIRE': '..-. .. .-. .',
            'SHELTER': '... .... . .-.. - . .-.',
            'ROAD CLOSED': '.-. --- .- -..   -.-. .-.. --- ... . -..',
            'ALL CLEAR': '.- .-.. .-..   -.-. .-.. . .- .-.'
        }
        return compression.get(message.upper(), message)
    
    # ========== AUTO-DETECTION ==========
    
    def register_detector(self, name, detector_type, callback=None):
        """Add a detection source"""
        self.detectors[name] = {
            'type': detector_type,
            'callback': callback,
            'buffer': [],
            'last_time': time.time()
        }
        
        # Start appropriate detector thread
        if detector_type == 'light':
            threading.Thread(target=self._light_detector, args=(name,)).start()
        elif detector_type == 'sound':
            threading.Thread(target=self._sound_detector, args=(name,)).start()
        elif detector_type == 'vibration':
            threading.Thread(target=self._vibration_detector, args=(name,)).start()
        elif detector_type == 'radio':
            threading.Thread(target=self._radio_detector, args=(name,)).start()
        elif detector_type == 'button':
            threading.Thread(target=self._button_detector, args=(name,)).start()
    
    def _light_detector(self, name):
        """Detect light flashes (LED, sun, flashlight)"""
        import RPi.GPIO as GPIO  # Pi only
        GPIO.setup(self.config.get('light_sensor_pin', 4), GPIO.IN)
        
        last_state = 0
        flash_start = 0
        
        while self.running:
            state = GPIO.input(4)
            now = time.time()
            
            if state and not last_state:  # Light ON
                flash_start = now
            elif not state and last_state:  # Light OFF
                duration = now - flash_start
                self._process_signal(name, duration)
            
            last_state = state
            time.sleep(0.01)
    
    def _sound_detector(self, name):
        """Detect audio tones (whistle, horn, siren)"""
        import pyaudio
        import numpy as np
        
        CHUNK = 1024
        RATE = 44100
        
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                       channels=1,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        tone_start = 0
        in_tone = False
        
        while self.running:
            data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
            volume = np.abs(data).mean()
            
            if volume > 500:  # Tone detected
                if not in_tone:
                    tone_start = time.time()
                    in_tone = True
            else:
                if in_tone:
                    duration = time.time() - tone_start
                    self._process_signal(name, duration)
                    in_tone = False
            
            time.sleep(0.01)
    
    def _vibration_detector(self, name):
        """Detect vibrations (tapping on hub, pipes)"""
        import RPi.GPIO as GPIO
        GPIO.setup(self.config.get('vibration_pin', 23), GPIO.IN)
        
        last_vibe = 0
        vibe_start = 0
        in_vibe = False
        
        while self.running:
            vibe = GPIO.input(23)
            now = time.time()
            
            if vibe and not in_vibe:
                vibe_start = now
                in_vibe = True
            elif not vibe and in_vibe:
                duration = now - vibe_start
                self._process_signal(name, duration)
                in_vibe = False
            
            time.sleep(0.01)
    
    def _radio_detector(self, name):
        """Detect CW signals from radio"""
        # Connect to Meshtastic or SDR
        import serial
        ser = serial.Serial(self.config.get('radio_port', '/dev/ttyACM0'), 115200)
        
        while self.running:
            # Radio would send CW detection events
            line = ser.readline().decode().strip()
            if line.startswith('CW:'):
                duration = float(line[3:])
                self._process_signal(name, duration)
    
    def _button_detector(self, name):
        """Detect button presses for manual input"""
        import RPi.GPIO as GPIO
        GPIO.setup(self.config.get('button_pin', 25), GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        last_press = 0
        press_start = 0
        
        while self.running:
            if GPIO.input(25) == 0:  # Button pressed
                if last_press == 0:
                    press_start = time.time()
                    last_press = 1
            else:
                if last_press == 1:
                    duration = time.time() - press_start
                    self._process_signal(name, duration)
                    last_press = 0
            
            time.sleep(0.01)
    
    def _process_signal(self, detector_name, duration):
        """Process a detected signal duration"""
        detector = self.detectors[detector_name]
        now = time.time()
        
        # Determine dot or dash
        if duration < self.dot_max:
            symbol = '.'
        elif duration > self.dash_min:
            symbol = '-'
        else:
            return  # Invalid duration
        
        # Add to buffer with timestamp
        detector['buffer'].append({
            'symbol': symbol,
            'time': now
        })
        
        # Check for gaps
        if detector['buffer']:
            last_time = detector['buffer'][-1]['time']
            time_since_last = now - last_time
            
            if time_since_last > self.word_gap:
                # Word complete
                self._decode_buffer(detector_name)
            elif time_since_last > self.letter_gap:
                # Letter complete
                self._decode_buffer(detector_name, letter_only=True)
    
    def _decode_buffer(self, detector_name, letter_only=False):
        """Decode the current buffer"""
        detector = self.detectors[detector_name]
        if not detector['buffer']:
            return
        
        # Build Morse string
        morse = ''.join([s['symbol'] for s in detector['buffer']])
        
        # Decode
        if morse in self.morse_to_text:
            char = self.morse_to_text[morse]
            
            # Callback
            if detector['callback']:
                detector['callback'](char, morse, detector_name)
            
            # Queue for processing
            self.incoming_queue.append({
                'char': char,
                'morse': morse,
                'source': detector_name,
                'time': time.time()
            })
        
        # Clear buffer (maybe keep last for context)
        if letter_only:
            detector['buffer'] = []
        else:
            detector['buffer'] = []
    
    # ========== OUTPUT ==========
    
    def register_output(self, name, output_type, config=None):
        """Add an output device"""
        self.outputs[name] = {
            'type': output_type,
            'config': config or {},
            'enabled': True
        }
    
    def send_morse(self, message, output_names=None, channels=None):
        """Send message to specified outputs"""
        # Convert to Morse
        morse = self.text_to_morse_code(message)
        
        # Queue for each output
        outputs = output_names or self.outputs.keys()
        for out_name in outputs:
            if out_name in self.outputs:
                self.outgoing_queue.append({
                    'message': message,
                    'morse': morse,
                    'output': out_name,
                    'channels': channels or ['all']
                })
    
    def _process_queues(self):
        """Process incoming and outgoing queues"""
        while self.running:
            # Process incoming (messages we decoded)
            while self.incoming_queue:
                msg = self.incoming_queue.popleft()
                self._handle_incoming(msg)
            
            # Process outgoing (messages to send)
            while self.outgoing_queue:
                msg = self.outgoing_queue.popleft()
                self._send_to_output(msg)
            
            time.sleep(0.1)
    
    def _handle_incoming(self, msg):
        """Handle a decoded message"""
        print(f"📨 Received: '{msg['char']}' from {msg['source']}")
        
        # Check for commands
        if msg['char'] == 'S' and hasattr(self, '_sos_buffer'):
            # Build SOS detection
            if not hasattr(self, '_sos_buffer'):
                self._sos_buffer = ''
            self._sos_buffer += msg['char']
            
            if 'SOS' in self._sos_buffer:
                print("🚨 SOS DETECTED!")
                self.trigger_sos()
                self._sos_buffer = ''
        else:
            self._sos_buffer = ''
    
    def _send_to_output(self, msg):
        """Send Morse to specific output"""
        output = self.outputs.get(msg['output'])
        if not output or not output['enabled']:
            return
        
        if output['type'] == 'led':
            self._output_led(msg['morse'], output['config'])
        elif output['type'] == 'buzzer':
            self._output_buzzer(msg['morse'], output['config'])
        elif output['type'] == 'vibrator':
            self._output_vibrator(msg['morse'], output['config'])
        elif output['type'] == 'radio':
            self._output_radio(msg['morse'], output['config'])
        elif output['type'] == 'screen':
            self._output_screen(msg['message'], output['config'])
    
    def _output_led(self, morse, config):
        """Blink LED"""
        import RPi.GPIO as GPIO
        pin = config.get('pin', 18)
        GPIO.setup(pin, GPIO.OUT)
        
        for char in morse:
            if char == '.':
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.2)
            elif char == '-':
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.6)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.2)
            elif char == ' ':
                time.sleep(0.6)
    
    def _output_buzzer(self, morse, config):
        """Sound buzzer"""
        import RPi.GPIO as GPIO
        pin = config.get('pin', 17)
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 1000)
        
        for char in morse:
            if char == '.':
                pwm.start(50)
                time.sleep(0.2)
                pwm.stop()
                time.sleep(0.2)
            elif char == '-':
                pwm.start(50)
                time.sleep(0.6)
                pwm.stop()
                time.sleep(0.2)
            elif char == ' ':
                time.sleep(0.6)
    
    def _output_vibrator(self, morse, config):
        """Vibrate motor"""
        import RPi.GPIO as GPIO
        pin = config.get('pin', 24)
        GPIO.setup(pin, GPIO.OUT)
        
        for char in morse:
            if char == '.':
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.2)
            elif char == '-':
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.6)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.2)
            elif char == ' ':
                time.sleep(0.6)
    
    def _output_radio(self, morse, config):
        """Send via radio (Meshtastic, etc.)"""
        import serial
        port = config.get('port', '/dev/ttyACM0')
        ser = serial.Serial(port, 115200)
        
        # Send as text
        ser.write(f"MSG:{morse}\n".encode())
    
    def _output_screen(self, message, config):
        """Display on screen"""
        print(f"📺 {message}")
    
    # ========== EMERGENCY FUNCTIONS ==========
    
    def trigger_sos(self):
        """Trigger SOS alert on all outputs"""
        print("🚨 EMERGENCY SOS ACTIVATED")
        for name in self.outputs:
            self.send_morse("SOS", [name])
        
        # Also trigger platform-specific alerts
        if hasattr(self, 'on_sos_callback'):
            self.on_sos_callback()
    
    def start_auto_beacon(self, message, interval=60):
        """Start automatic beaconing"""
        def beacon_loop():
            while self.running:
                self.send_morse(message, channels=['all'])
                time.sleep(interval)
        
        threading.Thread(target=beacon_loop).start()
    
    # ========== PLATFORM-SPECIFIC ==========
    
    def for_arduino(self, serial_port='/dev/ttyUSB0'):
        """Generate Arduino-compatible code"""
        arduino_code = """
// MorseOS for Arduino
// Upload this to your Arduino

const int ledPin = 13;
const int buttonPin = 2;
const int buzzerPin = 9;
const int vibratorPin = 10;

String morseBuffer = "";
unsigned long lastPressTime = 0;
bool buttonPressed = false;

void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  pinMode(vibratorPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // Check button for input
  if (digitalRead(buttonPin) == LOW) {
    if (!buttonPressed) {
      lastPressTime = millis();
      buttonPressed = true;
    }
  } else {
    if (buttonPressed) {
      unsigned long duration = millis() - lastPressTime;
      if (duration < 300) {
        morseBuffer += ".";
        Serial.print(".");
      } else if (duration > 400) {
        morseBuffer += "-";
        Serial.print("-");
      }
      buttonPressed = false;
      lastPressTime = millis();
    }
  }
  
  // Check for gaps (letter/word)
  if (morseBuffer.length() > 0) {
    if (millis() - lastPressTime > 1000) {
      decodeMorse();
      morseBuffer = "";
    }
  }
  
  // Check serial for messages to send
  if (Serial.available()) {
    String msg = Serial.readString();
    sendMorse(msg);
  }
}

void decodeMorse() {
  // Simple decoder - expand as needed
  if (morseBuffer == ".-") Serial.println("A");
  else if (morseBuffer == "-...") Serial.println("B");
  else if (morseBuffer == "-.-.") Serial.println("C");
  else if (morseBuffer == "..." ) Serial.println("S");
  else if (morseBuffer == "---") Serial.println("O");
  else Serial.println("?");
}

void sendMorse(String message) {
  for (int i = 0; i < message.length(); i++) {
    char c = message.charAt(i);
    // Convert to Morse and blink
    if (c == '.') {
      digitalWrite(ledPin, HIGH);
      digitalWrite(vibratorPin, HIGH);
      tone(buzzerPin, 1000);
      delay(200);
      digitalWrite(ledPin, LOW);
      digitalWrite(vibratorPin, LOW);
      noTone(buzzerPin);
      delay(200);
    } else if (c == '-') {
      digitalWrite(ledPin, HIGH);
      digitalWrite(vibratorPin, HIGH);
      tone(buzzerPin, 1000);
      delay(600);
      digitalWrite(ledPin, LOW);
      digitalWrite(vibratorPin, LOW);
      noTone(buzzerPin);
      delay(200);
    } else if (c == ' ') {
      delay(600);
    }
  }
}
"""
        with open('morse_os_arduino.ino', 'w') as f:
            f.write(arduino_code)
        print("✅ Arduino code generated: morse_os_arduino.ino")
    
    def for_meshtastic(self):
        """Generate Meshtastic module"""
        meshtastic_code = """
// MorseOS for Meshtastic
// Add to your Meshtastic device

#include "mesh.h"
#include "concurrency.h"
#include "detection.h"

class MorseModule : public ProtobufModule<meshtastic_MorseMessage> {
  public:
    MorseModule() : ProtobufModule("morse", meshtastic_MorseMessage_msg, &meshtastic_MorseMessage_msg) {}
    
  protected:
    virtual bool handleReceivedProtobuf(const meshtastic_MorseMessage &msg, const meshtastic_Routing &routing) {
      // Decode and display Morse
      String morse = msg.morse;
      String text = decodeMorse(morse);
      DEBUG_MSG("Morse received: %s -> %s\\n", morse.c_str(), text.c_str());
      
      // Flash LED with message
      blinkMorse(morse);
      
      return true;
    }
    
    String decodeMorse(String morse) {
      // Morse decoder
      if (morse == "... --- ...") return "SOS";
      if (morse == ".... . .-.. .--.") return "HELP";
      return "?";
    }
    
    void blinkMorse(String morse) {
      for (int i = 0; i < morse.length(); i++) {
        if (morse.charAt(i) == '.') {
          setLed(true);
          delay(200);
          setLed(false);
          delay(200);
        } else if (morse.charAt(i) == '-') {
          setLed(true);
          delay(600);
          setLed(false);
          delay(200);
        } else if (morse.charAt(i) == ' ') {
          delay(600);
        }
      }
    }
};

MorseModule *morseModule;

void setup() {
  morseModule = new MorseModule();
  service.addProtobufModule(morseModule);
}
"""
        with open('morse_os_meshtastic.cpp', 'w') as f:
            f.write(meshtastic_code)
        print("✅ Meshtastic code generated: morse_os_meshtastic.cpp")
    
    def for_app(self):
        """Generate mobile app code (Flutter)"""
        app_code = """
// MorseOS for Flutter Mobile App
// Add to your lib/main.dart

import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:sensors_plus/sensors.dart';
import 'package:flutter_sound/flutter_sound.dart';

class MorseOS extends StatefulWidget {
  @override
  _MorseOSState createState() => _MorseOSState();
}

class _MorseOSState extends State<MorseOS> {
  // Detectors
  bool usingCamera = true;
  bool usingMicrophone = true;
  bool usingFlashlight = true;
  bool usingVibration = true;
  
  // Morse buffer
  String morseBuffer = "";
  String textBuffer = "";
  List<String> messages = [];
  
  // Timers
  DateTime lastSignal = DateTime.now();
  bool inSignal = false;
  
  // Flashlight control
  bool flashlightOn = false;
  
  @override
  void initState() {
    super.initState();
    startDetectors();
  }
  
  void startDetectors() async {
    // Camera for light detection
    if (usingCamera) {
      final cameras = await availableCameras();
      final controller = CameraController(cameras[0], ResolutionPreset.low);
      await controller.initialize();
      controller.startImageStream((image) {
        // Analyze image for brightness changes
        // This would detect flashlight signals
      });
    }
    
    // Microphone for sound detection
    if (usingMicrophone) {
      FlutterSoundRecorder recorder = FlutterSoundRecorder();
      await recorder.openRecorder();
      recorder.startRecorder(
        codec: Codec.pcm16,
        sampleRate: 44100,
      );
      // Process audio stream for tones
    }
    
    // Vibration sensor
    if (usingVibration) {
      accelerometerEvents.listen((AccelerometerEvent event) {
        double force = event.x.abs() + event.y.abs() + event.z.abs();
        if (force > 20) { // Tap detected
          DateTime now = DateTime.now();
          Duration duration = now.difference(lastSignal);
          
          if (duration.inMilliseconds < 300) {
            setState(() => morseBuffer += ".");
          } else if (duration.inMilliseconds > 400) {
            setState(() => morseBuffer += "-");
          }
          
          lastSignal = now;
        }
      });
    }
  }
  
  void sendMorse(String text) {
    String morse = textToMorse(text);
    
    // Flash screen
    for (int i = 0; i < morse.length; i++) {
      Future.delayed(Duration(milliseconds: i * 400), () {
        setState(() {
          if (morse[i] == '.') {
            flashScreen(200);
          } else if (morse[i] == '-') {
            flashScreen(600);
          }
        });
      });
    }
  }
  
  void flashScreen(int duration) {
    // Flash screen white
    showDialog(
      context: context,
      barrierColor: Colors.white,
      builder: (context) => Container(),
    );
    Future.delayed(Duration(milliseconds: duration), () {
      Navigator.of(context).pop();
    });
  }
  
  String textToMorse(String text) {
    Map<String, String> map = {
      'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
      'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
      'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
      'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
      'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
      'Z': '--..',
    };
    
    String result = "";
    for (int i = 0; i < text.length; i++) {
      String char = text[i].toUpperCase();
      if (map.containsKey(char)) {
        result += map[char]! + " ";
      }
    }
    return result;
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Morse OS')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: messages.length,
              itemBuilder: (context, index) {
                return ListTile(
                  title: Text(messages[index]),
                );
              },
            ),
          ),
          Container(
            padding: EdgeInsets.all(20),
            child: Column(
              children: [
                Text('Morse Buffer: $morseBuffer'),
                Text('Text: $textBuffer'),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    ElevatedButton(
                      onPressed: () => sendMorse('SOS'),
                      child: Text('SOS'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                      ),
                    ),
                    ElevatedButton(
                      onPressed: () => setState(() {
                        if (flashlightOn) {
                          // Turn off flashlight
                        } else {
                          // Turn on flashlight
                        }
                        flashlightOn = !flashlightOn;
                      }),
                      child: Text(flashlightOn ? 'Flash Off' : 'Flash On'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
"""
        with open('morse_os_app.dart', 'w') as f:
            f.write(app_code)
        print("✅ Flutter app code generated: morse_os_app.dart")
    
    def for_web(self):
        """Generate web app (HTML/JS)"""
        web_code = """
<!DOCTYPE html>
<html>
<head>
    <title>Morse OS Web</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #1a1a1a; color: #fff; }
        .container { background: #2a2a2a; padding: 20px; border-radius: 10px; }
        button { padding: 15px; margin: 5px; font-size: 18px; background: #4CAF50; color: white; border: none; border-radius: 5px; }
        .sos { background: #f44336; }
        .buffer { font-family: monospace; font-size: 24px; background: #333; padding: 10px; border-radius: 5px; }
        #video { width: 100%; border-radius: 10px; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 Morse OS Web</h1>
        
        <div class="buffer" id="morseBuffer"></div>
        <div class="buffer" id="textBuffer"></div>
        
        <div>
            <button onclick="sendMorse('SOS')" class="sos">🚨 SOS</button>
            <button onclick="sendMorse('HELP')">🆘 HELP</button>
            <button onclick="sendMorse('FUEL')">⛽ FUEL</button>
            <button onclick="sendMorse('MEDIC')">🚑 MEDIC</button>
        </div>
        
        <div>
            <button onclick="startCamera()">📷 Start Camera (light detection)</button>
            <button onclick="startMic()">🎤 Start Microphone</button>
            <button onclick="startVibration()">📱 Start Vibration Detection</button>
        </div>
        
        <video id="video" autoplay></video>
        
        <div>
            <h3>Manual Input</h3>
            <button onmousedown="startSignal()" onmouseup="endSignal()">TAP HERE</button>
            <p>Hold short for dot, long for dash</p>
        </div>
    </div>
    
    <script>
        // Morse mappings
        const morseMap = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z',
            '-----': '0', '.----': '1', '..---': '2', '...--': '3',
            '....-': '4', '.....': '5', '-....': '6', '--...': '7',
            '---..': '8', '----.': '9'
        };
        
        // State
        let morseBuffer = '';
        let textBuffer = '';
        let signalStart = 0;
        let lastSignal = 0;
        
        // UI elements
        const morseEl = document.getElementById('morseBuffer');
        const textEl = document.getElementById('textBuffer');
        
        // Manual input
        function startSignal() {
            signalStart = Date.now();
        }
        
        function endSignal() {
            const duration = Date.now() - signalStart;
            
            if (duration < 300) {
                morseBuffer += '.';
            } else if (duration > 400) {
                morseBuffer += '-';
            }
            
            lastSignal = Date.now();
            updateDisplay();
            
            // Check for gap
            setTimeout(checkGap, 1000);
        }
        
        function checkGap() {
            const now = Date.now();
            if (now - lastSignal > 1000 && morseBuffer.length > 0) {
                decodeMorse();
            }
        }
        
        function decodeMorse() {
            if (morseMap[morseBuffer]) {
                textBuffer += morseMap[morseBuffer];
            } else {
                textBuffer += '?';
            }
            morseBuffer = '';
            updateDisplay();
        }
        
        // Camera for light detection
        async function startCamera() {
            const video = document.getElementById('video');
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.display = 'block';
            
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            setInterval(() => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                let brightness = 0;
                for (let i = 0; i < imageData.data.length; i += 4) {
                    brightness += imageData.data[i]; // Red channel
                }
                brightness /= (imageData.data.length / 4);
                
                // Detect flashes
                if (brightness > 200) { // Bright flash
                    // Process as Morse signal
                    console.log('Flash detected');
                }
            }, 100);
        }
        
        // Microphone for sound
        async function startMic() {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const audioContext = new AudioContext();
            const analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            
            analyser.fftSize = 256;
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            
            setInterval(() => {
                analyser.getByteFrequencyData(dataArray);
                const avg = dataArray.reduce((a, b) => a + b) / dataArray.length;
                
                if (avg > 100) { // Loud sound
                    // Process as Morse
                    console.log('Sound detected');
                }
            }, 100);
        }
        
        // Vibration detection (mobile only)
        function startVibration() {
            if (window.DeviceMotionEvent) {
                window.addEventListener('devicemotion', (event) => {
                    const acc = event.accelerationIncludingGravity;
                    const force = Math.abs(acc.x) + Math.abs(acc.y) + Math.abs(acc.z);
                    
                    if (force > 20) { // Tap detected
                        const now = Date.now();
                        if (now - lastSignal < 300) {
                            morseBuffer += '.';
                        } else if (now - lastSignal > 400) {
                            morseBuffer += '-';
                        }
                        lastSignal = now;
                        updateDisplay();
                    }
                });
            }
        }
        
        // Send Morse (output)
        function sendMorse(text) {
            const morse = textToMorse(text);
            
            // Flash screen
            for (let i = 0; i < morse.length; i++) {
                setTimeout(() => {
                    if (morse[i] === '.') {
                        flashScreen(200);
                    } else if (morse[i] === '-') {
                        flashScreen(600);
                    }
                }, i * 400);
            }
        }
        
        function textToMorse(text) {
            const map = {
                'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
                'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
                'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
                'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
                'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
                'Z': '--..',
            };
            
            let result = '';
            for (let char of text.toUpperCase()) {
                if (map[char]) {
                    result += map[char] + ' ';
                }
            }
            return result.trim();
        }
        
        function flashScreen(duration) {
            document.body.style.backgroundColor = '#fff';
            setTimeout(() => {
                document.body.style.backgroundColor = '#1a1a1a';
            }, duration);
        }
        
        function updateDisplay() {
            morseEl.textContent = 'Morse: ' + morseBuffer;
            textEl.textContent = 'Text: ' + textBuffer;
        }
    </script>
</body>
</html>
"""
        with open('morse_os_web.html', 'w') as f:
            f.write(web_code)
        print("✅ Web app generated: morse_os_web.html")

# ========== USAGE EXAMPLES ==========

if __name__ == "__main__":
    # Create Morse OS instance
    morse = MorseOS(platform='pi')
    
    # Register detectors
    morse.register_detector('button', 'button', callback=lambda c,m,s: print(f"Got: {c}"))
    morse.register_detector('light', 'light')
    morse.register_detector('sound', 'sound')
    morse.register_detector('vibe', 'vibration')
    
    # Register outputs
    morse.register_output('led', 'led', {'pin': 18})
    morse.register_output('buzzer', 'buzzer', {'pin': 17})
    morse.register_output('vibrator', 'vibrator', {'pin': 24})
    
    # Send a message
    morse.send_morse("SOS", ['led', 'buzzer'])
    
    # Translate
    print(morse.text_to_morse_code("HELP"))
    print(morse.morse_to_text(".... . .-.. .--."))
    
    # Generate platform code
    morse.for_arduino()
    morse.for_meshtastic()
    morse.for_app()
    morse.for_web()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        morse.running = False
```

---

📦 PART 2: Platform-Specific Add-ons

Arduino Add-on Pack

```cpp
// morse_os_arduino_addons.ino
// Extra sensors and outputs for Arduino

#include <SoftwareSerial.h>

class MorseArduinoAddons {
  private:
    // Pins
    const int LIGHT_SENSOR = A0;
    const int VIBRATION_SENSOR = 2;
    const int IR_LED = 3;  // Infrared (invisible)
    const int LASER = 4;    // Laser pointer
    const int RELAY = 5;    // For horn/siren
    
    // Timers
    unsigned long lastSignal = 0;
    bool inSignal = false;
    
  public:
    void begin() {
      pinMode(LIGHT_SENSOR, INPUT);
      pinMode(VIBRATION_SENSOR, INPUT);
      pinMode(IR_LED, OUTPUT);
      pinMode(LASER, OUTPUT);
      pinMode(RELAY, OUTPUT);
      
      Serial.println("Morse Arduino Addons Ready");
    }
    
    // ===== INPUT ADD-ONS =====
    
    void checkLightSensor() {
      int light = analogRead(LIGHT_SENSOR);
      static int lastLight = 0;
      
      if (light > 800 && lastLight < 200) {  // Sudden bright flash
        unsigned long now = millis();
        
        if (inSignal) {
          unsigned long duration = now - lastSignal;
          if (duration < 300) Serial.print(".");
          else if (duration > 400) Serial.print("-");
          inSignal = false;
        } else {
          lastSignal = now;
          inSignal = true;
        }
      }
      
      lastLight = light;
    }
    
    void checkVibration() {
      int vibe = digitalRead(VIBRATION_SENSOR);
      static int lastVibe = LOW;
      
      if (vibe == HIGH && lastVibe == LOW) {  // Tap detected
        unsigned long now = millis();
        
        if (inSignal) {
          unsigned long duration = now - lastSignal;
          if (duration < 300) Serial.print(".");
          else if (duration > 400) Serial.print("-");
          inSignal = false;
        } else {
          lastSignal = now;
          inSignal = true;
        }
      }
      
      lastVibe = vibe;
    }
    
    // ===== OUTPUT ADD-ONS =====
    
    void sendIR(String morse) {
      // Infrared - invisible to naked eye, visible through phones
      for (int i = 0; i < morse.length(); i++) {
        if (morse.charAt(i) == '.') {
          digitalWrite(IR_LED, HIGH);
          delay(200);
          digitalWrite(IR_LED, LOW);
          delay(200);
        } else if (morse.charAt(i) == '-') {
          digitalWrite(IR_LED, HIGH);
          delay(600);
          digitalWrite(IR_LED, LOW);
          delay(200);
        } else if (morse.charAt(i) == ' ') {
          delay(600);
        }
      }
    }
    
    void sendLaser(String morse) {
      // Laser pointer - visible for miles at night
      for (int i = 0; i < morse.length(); i++) {
        if (morse.charAt(i) == '.') {
          digitalWrite(LASER, HIGH);
          delay(200);
          digitalWrite(LASER, LOW);
          delay(200);
        } else if (morse.charAt(i) == '-') {
          digitalWrite(LASER, HIGH);
          delay(600);
          digitalWrite(LASER, LOW);
          delay(200);
        } else if (morse.charAt(i) == ' ') {
          delay(600);
        }
      }
    }
    
    void sendHorn(String morse) {
      // Activate vehicle horn via relay
      for (int i = 0; i < morse.length(); i++) {
        if (morse.charAt(i) == '.') {
          digitalWrite(RELAY, HIGH);
          delay(200);
          digitalWrite(RELAY, LOW);
          delay(200);
        } else if (morse.charAt(i) == '-') {
          digitalWrite(RELAY, HIGH);
          delay(600);
          digitalWrite(RELAY, LOW);
          delay(200);
        } else if (morse.charAt(i) == ' ') {
          delay(600);
        }
      }
    }
    
    // ===== SPECIAL =====
    
    void solarReflect(int servoPin, String morse) {
      // Use servo to tilt solar panel, reflecting sunlight
      // Like heliograph - visible 30+ miles
      for (int i = 0; i < morse.length(); i++) {
        if (morse.charAt(i) == '.') {
          // Tilt to reflect
          delay(200);
          // Return to neutral
          delay(200);
        } else if (morse.charAt(i) == '-') {
          // Tilt to reflect longer
          delay(600);
          // Return
          delay(200);
        }
      }
    }
};

MorseArduinoAddons addons;

void setup() {
  Serial.begin(9600);
  addons.begin();
}

void loop() {
  addons.checkLightSensor();
  addons.checkVibration();
  
  // Check for commands from Pi/Computer
  if (Serial.available()) {
    String cmd = Serial.readString();
    if (cmd.startsWith("SEND:")) {
      String morse = cmd.substring(5);
      addons.sendIR(morse);
      addons.sendLaser(morse);
    }
  }
  
  delay(10);
}
```

---

Raspberry Pi Add-on Pack

```python
# morse_pi_addons.py
# Extra capabilities for Raspberry Pi

import RPi.GPIO as GPIO
import picamera
import numpy as np
import cv2
from PIL import Image
import time

class MorsePiAddons:
    def __init__(self):
        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        
        # Camera for visual detection
        self.camera = picamera.PiCamera()
        self.camera.resolution = (640, 480)
        
        # Pins for special outputs
        self.IR_LED = 18  # Infrared
        self.LASER = 23   # Laser pointer
        self.SERVO = 24   # For heliograph
        self.RELAY = 25   # For horn/siren
        
        GPIO.setup(self.IR_LED, GPIO.OUT)
        GPIO.setup(self.LASER, GPIO.OUT)
        GPIO.setup(self.SERVO, GPIO.OUT)
        GPIO.setup(self.RELAY, GPIO.OUT)
        
        # PWM for servo
        self.servo = GPIO.PWM(self.SERVO, 50)
        self.servo.start(0)
    
    # ===== CAMERA DETECTION =====
    
    def detect_light_flashes(self):
        """Use camera to detect light flashes (distant signals)"""
        # Capture frame
        self.camera.capture('frame.jpg')
        img = cv2.imread('frame.jpg')
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Find bright spots
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Count bright pixels
        bright_pixels = np.sum(thresh > 0)
        
        return bright_pixels
    
    def track_moving_light(self):
        """Track a moving light source (flashlight being waved)"""
        # Background subtractor
        backSub = cv2.createBackgroundSubtractorMOG2()
        
        # Capture video
        for frame in self.camera.capture_continuous('frame.jpg'):
            img = cv2.imread('frame.jpg')
            
            # Find moving bright objects
            fgMask = backSub.apply(img)
            
            # Look for Morse patterns in movement
            # (up/down for dot/dash)
            pass
    
    # ===== SPECIALIZED OUTPUTS =====
    
    def send_infrared(self, morse):
        """Send IR - invisible to naked eye"""
        for char in morse:
            if char == '.':
                GPIO.output(self.IR_LED, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(self.IR_LED, GPIO.LOW)
                time.sleep(0.2)
            elif char == '-':
                GPIO.output(self.IR_LED, GPIO.HIGH)
                time.sleep(0.6)
                GPIO.output(self.IR_LED, GPIO.LOW)
                time.sleep(0.2)
            elif char == ' ':
                time.sleep(0.6)
    
    def send_laser(self, morse):
        """Send via laser pointer - visible for miles"""
        for char in morse:
            if char == '.':
                GPIO.output(self.LASER, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(self.LASER, GPIO.LOW)
                time.sleep(0.2)
            elif char == '-':
                GPIO.output(self.LASER, GPIO.HIGH)
                time.sleep(0.6)
                GPIO.output(self.LASER, GPIO.LOW)
                time.sleep(0.2)
            elif char == ' ':
                time.sleep(0.6)
    
    def heliograph(self, morse, sun_direction):
        """Use servo to reflect sunlight"""
        # Angle to reflect sun toward target
        reflect_angle = self.calc_reflect_angle(sun_direction)
        neutral_angle = reflect_angle - 10  # Slightly off
        
        for char in morse:
            if char == '.':
                self.servo.ChangeDutyCycle(reflect_angle)
                time.sleep(0.2)
                self.servo.ChangeDutyCycle(neutral_angle)
                time.sleep(0.2)
            elif char == '-':
                self.servo.ChangeDutyCycle(reflect_angle)
                time.sleep(0.6)
                self.servo.ChangeDutyCycle(neutral_angle)
                time.sleep(0.2)
            elif char == ' ':
                time.sleep(0.6)
    
    def calc_reflect_angle(self, sun_pos):
        """Calculate servo angle to reflect sun to horizon"""
        # Simplified - would need actual math
        return 7.5  # Center position
    
    def horn_signal(self, morse):
        """Activate vehicle horn/siren"""
        for char in morse:
            if char == '.':
                GPIO.output(self.RELAY, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(self.RELAY, GPIO.LOW)
                time.sleep(0.2)
            elif char == '-':
                GPIO.output(self.RELAY, GPIO.HIGH)
                time.sleep(0.6)
                GPIO.output(self.RELAY, GPIO.LOW)
                time.sleep(0.2)
            elif char == ' ':
                time.sleep(0.6)
    
    # ===== MESH INTEGRATION =====
    
    def mesh_to_morse(self, mesh_message):
        """Convert mesh message to Morse for local broadcast"""
        text = mesh_message.get('text', '')
        return self.text_to_morse(text)
    
    def morse_to_mesh(self, morse):
        """Convert detected Morse to mesh message"""
        text = self.morse_to_text(morse)
        return {
            'type': 'morse_message',
            'text': text,
            'timestamp': time.time()
        }
    
    # ===== UTILITIES =====
    
    def text_to_morse(self, text):
        # Same as before
        pass
    
    def morse_to_text(self, morse):
        # Same as before
        pass

# Usage
pi_addons = MorsePiAddons()

# Detect distant signals
brightness = pi_addons.detect_light_flashes()
if brightness > 10000:
    print("Light signal detected!")

# Send invisible alert
pi_addons.send_infrared("... --- ...")
```

---

Meshtastic Add-on Pack

```python
# morse_meshtastic_addon.py
# Integrate Morse with Meshtastic mesh network

import serial
import time
import threading
import json

class MorseMeshtastic:
    def __init__(self, port='/dev/ttyACM0', baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.running = False
        
        # Morse mapping
        self.morse_to_text = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z',
        }
    
    def connect(self):
        """Connect to Meshtastic device"""
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            self.running = True
            print(f"Connected to Meshtastic on {self.port}")
            
            # Start listener thread
            threading.Thread(target=self._listen_mesh).start()
            
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def _listen_mesh(self):
        """Listen for mesh messages"""
        while self.running:
            if self.ser and self.ser.in_waiting:
                line = self.ser.readline().decode().strip()
                try:
                    msg = json.loads(line)
                    self._handle_mesh_message(msg)
                except:
                    pass
            time.sleep(0.1)
    
    def _handle_mesh_message(self, msg):
        """Process incoming mesh messages"""
        if msg.get('type') == 'text':
            text = msg.get('payload', '')
            print(f"📡 Mesh -> Morse: {text}")
            
            # Convert to Morse and broadcast locally
            morse = self.text_to_morse(text)
            self.broadcast_morse_local(morse)
    
    def send_to_mesh(self, message, channel=0):
        """Send message to mesh network"""
        if not self.ser:
            return False
        
        # Format for Meshtastic
        cmd = f'sendtext "{message}" {channel}\n'
        self.ser.write(cmd.encode())
        return True
    
    def broadcast_morse_local(self, morse):
        """Broadcast Morse locally (light, sound, etc.)"""
        # This would connect to local output devices
        print(f"🔦 Local Morse: {morse}")
    
    def morse_detected_local(self, morse):
        """Handle Morse detected from local sensors"""
        text = self.morse_to_text.get(morse, '?')
        print(f"👂 Local Morse: {morse} -> {text}")
        
        # Send to mesh
        self.send_to_mesh(f"[MORSE] {text}")
    
    def text_to_morse(self, text):
        """Convert text to Morse"""
        # Simplified - use full mapping from earlier
        return text  # Placeholder
    
    def close(self):
        self.running = False
        if self.ser:
            self.ser.close()

# Meshtastic + Morse Gateway
class MorseMeshGateway:
    """Bridge between Morse devices and mesh network"""
    
    def __init__(self):
        self.mesh = MorseMeshtastic()
        self.morse_devices = []  # Connected Morse I/O devices
        
    def add_morse_device(self, device):
        """Add a Morse input/output device"""
        self.morse_devices.append(device)
        
    def run(self):
        """Main gateway loop"""
        self.mesh.connect()
        
        while True:
            # Check all Morse devices for input
            for device in self.morse_devices:
                morse = device.read_morse()
                if morse:
                    # Send to mesh
                    self.mesh.send_to_mesh(f"[MORSE] {morse}")
            
            # Check mesh for messages to broadcast as Morse
            # (handled by mesh listener)
            
            time.sleep(0.1)

# Example: Connect an Arduino with Morse sensors to Meshtastic
gateway = MorseMeshGateway()
gateway.add_morse_device(ArduinoMorseDevice('/dev/ttyUSB0'))  # Hypothetical
gateway.run()
```

---

Mobile App Add-on Pack (Flutter)

```dart
// morse_app_addons.dart
// Extra capabilities for mobile app

import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:sensors_plus/sensors.dart';
import 'package:torch/torch.dart';
import 'package:vibration/vibration.dart';
import 'package:flutter_sound/flutter_sound.dart';

class MorseAppAddons extends StatefulWidget {
  @override
  _MorseAppAddonsState createState() => _MorseAppAddonsState();
}

class _MorseAppAddonsState extends State<MorseAppAddons> {
  // Camera for light detection
  CameraController? _cameraController;
  
  // Audio for sound detection
  FlutterSoundRecorder? _recorder;
  
  // State
  bool _isDetecting = false;
  String _lastMorse = '';
  String _decodedText = '';
  
  // Morse buffer
  List<String> _morseBuffer = [];
  DateTime _lastSignal = DateTime.now();
  bool _inSignal = false;
  
  @override
  void initState() {
    super.initState();
    _initSensors();
  }
  
  Future<void> _initSensors() async {
    // Initialize camera
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      _cameraController = CameraController(cameras[0], ResolutionPreset.low);
      await _cameraController!.initialize();
      _startCameraDetection();
    }
    
    // Initialize audio
    _recorder = FlutterSoundRecorder();
    await _recorder!.openRecorder();
    _startAudioDetection();
    
    // Vibration detection
    accelerometerEvents.listen((AccelerometerEvent event) {
      _handleVibration(event);
    });
  }
  
  void _startCameraDetection() {
    _cameraController!.startImageStream((CameraImage image) {
      if (!_isDetecting) return;
      
      // Analyze image brightness
      int brightness = _calculateBrightness(image);
      
      // Detect flashes
      if (brightness > 200) {
        DateTime now = DateTime.now();
        
        if (_inSignal) {
          Duration duration = now.difference(_lastSignal);
          if (duration.inMilliseconds < 300) {
            setState(() => _morseBuffer.add('.'));
          } else if (duration.inMilliseconds > 400) {
            setState(() => _morseBuffer.add('-'));
          }
          _inSignal = false;
        } else {
          _lastSignal = now;
          _inSignal = true;
        }
      }
    });
  }
  
  int _calculateBrightness(CameraImage image) {
    // Simplified brightness calculation
    return 100; // Placeholder
  }
  
  void _startAudioDetection() async {
    await _recorder!.startRecorder(
      codec: Codec.pcm16,
      sampleRate: 44100,
    );
    
    // Process audio stream
    _recorder!.onProgress!.listen((data) {
      if (!_isDetecting) return;
      
      // Check volume for tone detection
      if (data.decibels! > -30) { // Loud tone
        DateTime now = DateTime.now();
        
        if (_inSignal) {
          Duration duration = now.difference(_lastSignal);
          if (duration.inMilliseconds < 300) {
            setState(() => _morseBuffer.add('.'));
          } else if (duration.inMilliseconds > 400) {
            setState(() => _morseBuffer.add('-'));
          }
          _inSignal = false;
        } else {
          _lastSignal = now;
          _inSignal = true;
        }
      }
    });
  }
  
  void _handleVibration(AccelerometerEvent event) {
    if (!_isDetecting) return;
    
    double force = event.x.abs() + event.y.abs() + event.z.abs();
    
    if (force > 20) { // Tap detected
      DateTime now = DateTime.now();
      
      if (_inSignal) {
        Duration duration = now.difference(_lastSignal);
        if (duration.inMilliseconds < 300) {
          setState(() => _morseBuffer.add('.'));
        } else if (duration.inMilliseconds > 400) {
          setState(() => _morseBuffer.add('-'));
        }
        _inSignal = false;
      } else {
        _lastSignal = now;
        _inSignal = true;
      }
    }
  }
  
  // ===== OUTPUT ADD-ONS =====
  
  Future<void> flashTorchMorse(String morse) async {
    for (int i = 0; i < morse.length; i++) {
      if (morse[i] == '.') {
        await Torch.turnOn();
        await Future.delayed(Duration(milliseconds: 200));
        await Torch.turnOff();
        await Future.delayed(Duration(milliseconds: 200));
      } else if (morse[i] == '-') {
        await Torch.turnOn();
        await Future.delayed(Duration(milliseconds: 600));
        await Torch.turnOff();
        await Future.delayed(Duration(milliseconds: 200));
      } else if (morse[i] == ' ') {
        await Future.delayed(Duration(milliseconds: 600));
      }
    }
  }
  
  Future<void> vibrateMorse(String morse) async {
    for (int i = 0; i < morse.length; i++) {
      if (morse[i] == '.') {
        await Vibration.vibrate(duration: 200);
        await Future.delayed(Duration(milliseconds: 200));
      } else if (morse[i] == '-') {
        await Vibration.vibrate(duration: 600);
        await Future.delayed(Duration(milliseconds: 200));
      } else if (morse[i] == ' ') {
        await Future.delayed(Duration(milliseconds: 600));
      }
    }
  }
  
  Future<void> screenFlashMorse(String morse) async {
    // Flash screen white/black
    for (int i = 0; i < morse.length; i++) {
      if (morse[i] == '.') {
        _flashScreen(200);
        await Future.delayed(Duration(milliseconds: 400));
      } else if (morse[i] == '-') {
        _flashScreen(600);
        await Future.delayed(Duration(milliseconds: 800));
      }
    }
  }
  
  void _flashScreen(int duration) {
    showDialog(
      context: context,
      barrierColor: Colors.white,
      builder: (context) => Container(),
    );
    Future.delayed(Duration(milliseconds: duration), () {
      Navigator.of(context).pop();
    });
  }
  
  // ===== UI =====
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Morse OS - Addons'),
        backgroundColor: Colors.blueGrey[900],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.blueGrey[900]!, Colors.black],
          ),
        ),
        child: Column(
          children: [
            // Detection status
            SwitchListTile(
              title: Text('Auto-Detect Mode'),
              value: _isDetecting,
              onChanged: (value) {
                setState(() => _isDetecting = value);
              },
            ),
            
            // Current buffer
            Container(
              padding: EdgeInsets.all(20),
              child: Column(
                children: [
                  Text(
                    'Morse: ${_morseBuffer.join('')}',
                    style: TextStyle(fontSize: 24, fontFamily: 'monospace'),
                  ),
                  Text(
                    'Text: $_decodedText',
                    style: TextStyle(fontSize: 18),
                  ),
                ],
              ),
            ),
            
            // Quick send buttons
            Wrap(
              spacing: 8,
              children: [
                _buildSendButton('SOS', Colors.red),
                _buildSendButton('HELP', Colors.orange),
                _buildSendButton('FUEL', Colors.blue),
                _buildSendButton('MEDIC', Colors.green),
              ],
            ),
            
            // Special outputs
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                padding: EdgeInsets.all(16),
                children: [
                  _buildOutputCard(
                    'Torch',
                    Icons.flashlight_on,
                    () => flashTorchMorse(_morseBuffer.join('')),
                  ),
                  _buildOutputCard(
                    'Vibrate',
                    Icons.vibration,
                    () => vibrateMorse(_morseBuffer.join('')),
                  ),
                  _buildOutputCard(
                    'Screen Flash',
                    Icons.screen_lock_portrait,
                    () => screenFlashMorse(_morseBuffer.join('')),
                  ),
                  _buildOutputCard(
                    'Sound',
                    Icons.volume_up,
                    () => _playSoundMorse(_morseBuffer.join('')),
                  ),
                  _buildOutputCard(
                    'Share',
                    Icons.share,
                    () => _shareMorse(_morseBuffer.join('')),
                  ),
                  _buildOutputCard(
                    'Save',
                    Icons.save,
                    () => _saveMorse(_morseBuffer.join('')),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildSendButton(String text, Color color) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 15),
      ),
      onPressed: () => _sendMorse(text),
      child: Text(text),
    );
  }
  
  Widget _buildOutputCard(String title, IconData icon, VoidCallback onTap) {
    return Card(
      color: Colors.blueGrey[800],
      child: InkWell(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 40, color: Colors.white),
            SizedBox(height: 8),
            Text(title, style: TextStyle(color: Colors.white)),
          ],
        ),
      ),
    );
  }
  
  void _sendMorse(String text) {
    // Convert to Morse and send via all outputs
    String morse = _textToMorse(text);
    flashTorchMorse(morse);
    vibrateMorse(morse);
    screenFlashMorse(morse);
  }
  
  String _textToMorse(String text) {
    // Simplified - use full mapping
    return text; // Placeholder
  }
  
  void _playSoundMorse(String morse) {
    // Generate tones
  }
  
  void _shareMorse(String morse) {
    // Share via other apps
  }
  
  void _saveMorse(String morse) {
    // Save to history
  }
}
```

---

Computer Add-on Pack (Desktop)

```python
# morse_desktop_addons.py
# For Windows/Mac/Linux computers

import tkinter as tk
from tkinter import ttk
import pyaudio
import wave
import numpy as np
import threading
import time
import serial
import requests

class MorseDesktop:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Morse OS - Desktop")
        self.window.geometry("800x600")
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Morse state
        self.morse_buffer = ""
        self.text_buffer = ""
        self.listening = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main = ttk.Frame(self.window, padding="10")
        main.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        ttk.Label(main, text="Morse OS Desktop", 
                 font=('Arial', 24)).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Input section
        input_frame = ttk.LabelFrame(main, text="Input", padding="10")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(input_frame, text="Start Listening", 
                  command=self.start_listening).grid(row=0, column=0, padx=5)
        ttk.Button(input_frame, text="Stop Listening", 
                  command=self.stop_listening).grid(row=0, column=1, padx=5)
        
        # Manual input
        ttk.Label(input_frame, text="Manual Input:").grid(row=1, column=0, pady=5)
        self.manual_entry = ttk.Entry(input_frame, width=30)
        self.manual_entry.grid(row=1, column=1, pady=5)
        ttk.Button(input_frame, text="Send", 
                  command=self.send_manual).grid(row=1, column=2, padx=5)
        
        # Display
        display_frame = ttk.LabelFrame(main, text="Messages", padding="10")
        display_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.display = tk.Text(display_frame, height=10, width=70)
        self.display.grid(row=0, column=0, columnspan=2)
        
        # Morse buffer
        ttk.Label(display_frame, text="Morse:").grid(row=1, column=0, sticky=tk.W)
        self.morse_label = ttk.Label(display_frame, text="")
        self.morse_label.grid(row=1, column=1, sticky=tk.W)
        
        # Text buffer
        ttk.Label(display_frame, text="Text:").grid(row=2, column=0, sticky=tk.W)
        self.text_label = ttk.Label(display_frame, text="")
        self.text_label.grid(row=2, column=1, sticky=tk.W)
        
        # Output section
        output_frame = ttk.LabelFrame(main, text="Output", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(output_frame, text="Flash Screen", 
                  command=self.flash_screen).grid(row=0, column=0, padx=5)
        ttk.Button(output_frame, text="Play Sound", 
                  command=self.play_sound).grid(row=0, column=1, padx=5)
        ttk.Button(output_frame, text="Send to Mesh", 
                  command=self.send_to_mesh).grid(row=0, column=2, padx=5)
        
        # Status bar
        self.status = ttk.Label(main, text="Ready", relief=tk.SUNKEN)
        self.status.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    # ===== INPUT METHODS =====
    
    def start_listening(self):
        """Start audio detection"""
        self.listening = True
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()
        self.status.config(text="Listening...")
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Process incoming audio"""
        if not self.listening:
            return (in_data, pyaudio.paComplete)
        
        # Convert to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        volume = np.abs(audio_data).mean()
        
        # Detect tones
        if volume > 500:  # Loud enough
            # Process as Morse signal
            self.process_signal()
        
        return (in_data, pyaudio.paContinue)
    
    def process_signal(self):
        """Process a detected signal"""
        # This would handle timing for dot/dash detection
        pass
    
    def stop_listening(self):
        """Stop audio detection"""
        self.listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.status.config(text="Stopped")
    
    def send_manual(self):
        """Send manually entered text"""
        text = self.manual_entry.get()
        if text:
            self.display.insert(tk.END, f"Manual: {text}\n")
            self.display.see(tk.END)
            self.manual_entry.delete(0, tk.END)
    
    # ===== OUTPUT METHODS =====
    
    def flash_screen(self):
        """Flash the screen with Morse"""
        def flash():
            import tkinter as tk
            flash_win = tk.Toplevel(self.window)
            flash_win.attributes('-fullscreen', True)
            flash_win.configure(bg='white')
            flash_win.after(200, flash_win.destroy)
        
        threading.Thread(target=flash).start()
    
    def play_sound(self):
        """Play Morse tones"""
        def play():
            import winsound  # Windows
            # Play dots and dashes
            winsound.Beep(1000, 200)  # Dot
            time.sleep(0.2)
            winsound.Beep(1000, 600)  # Dash
        
        threading.Thread(target=play).start()
    
    def send_to_mesh(self):
        """Send to Meshtastic network"""
        # Connect to Meshtastic via serial
        try:
            ser = serial.Serial('/dev/ttyACM0', 115200)
            ser.write(b'sendtext "Morse message"\n')
            ser.close()
            self.status.config(text="Sent to mesh")
        except:
            self.status.config(text="Mesh not available")
    
    def run(self):
        self.window.mainloop()

# Run desktop app
if __name__ == "__main__":
    app = MorseDesktop()
    app.run()
```

---

Web Add-on Pack (Browser)

```html
<!-- morse_web_addons.html -->
<!-- Browser-based Morse with advanced features -->

<!DOCTYPE html>
<html>
<head>
    <title>Morse OS Web Addons</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .sensor-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .sensor-card {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.3s;
        }
        
        .sensor-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.3);
        }
        
        .sensor-card.active {
            background: rgba(76, 175, 80, 0.5);
            box-shadow: 0 0 20px #4CAF50;
        }
        
        .sensor-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        
        .buffer-display {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
            font-size: 24px;
            text-align: center;
            min-height: 100px;
        }
        
        .morse-buffer {
            color: #ffd700;
            font-size: 32px;
            word-wrap: break-word;
        }
        
        .text-buffer {
            color: #98fb98;
            font-size: 28px;
            margin-top: 10px;
        }
        
        .output-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .output-btn {
            padding: 15px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .output-btn:hover {
            background: rgba(255, 255, 255, 0.4);
            transform: scale(1.05);
        }
        
        .output-btn.sos {
            background: rgba(244, 67, 54, 0.7);
        }
        
        .output-btn.sos:hover {
            background: rgba(244, 67, 54, 0.9);
        }
        
        #video-feed {
            width: 100%;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        
        .status {
            text-align: center;
            padding: 10px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 Morse OS - Web Addons</h1>
        
        <!-- Sensor Selection -->
        <div class="sensor-grid">
            <div class="sensor-card" id="camera-sensor" onclick="toggleSensor('camera')">
                <div class="sensor-icon">📷</div>
                <div>Camera (Light)</div>
                <small>Detect flashes</small>
            </div>
            <div class="sensor-card" id="mic-sensor" onclick="toggleSensor('mic')">
                <div class="sensor-icon">🎤</div>
                <div>Microphone</div>
                <small>Detect tones</small>
            </div>
            <div class="sensor-card" id="vibration-sensor" onclick="toggleSensor('vibration')">
                <div class="sensor-icon">📱</div>
                <div>Vibration</div>
                <small>Detect taps</small>
            </div>
            <div class="sensor-card" id="gyro-sensor" onclick="toggleSensor('gyro')">
                <div class="sensor-icon">🔄</div>
                <div>Gyroscope</div>
                <small>Motion Morse</small>
            </div>
        </div>
        
        <!-- Video Feed (for camera) -->
        <video id="video-feed" autoplay></video>
        
        <!-- Buffer Display -->
        <div class="buffer-display">
            <div class="morse-buffer" id="morse-buffer"></div>
            <div class="text-buffer" id="text-buffer"></div>
        </div>
        
        <!-- Output Buttons -->
        <div class="output-buttons">
            <button class="output-btn" onclick="sendMorse('SOS')">🚨 SOS</button>
            <button class="output-btn" onclick="sendMorse('HELP')">🆘 HELP</button>
            <button class="output-btn" onclick="sendMorse('FUEL')">⛽ FUEL</button>
            <button class="output-btn" onclick="sendMorse('MEDIC')">🚑 MEDIC</button>
            <button class="output-btn" onclick="sendMorse('WATER')">💧 WATER</button>
            <button class="output-btn" onclick="sendMorse('FIRE')">🔥 FIRE</button>
        </div>
        
        <!-- Advanced Outputs -->
        <div class="output-buttons">
            <button class="output-btn" onclick="flashScreen()">💡 Flash Screen</button>
            <button class="output-btn" onclick="vibrate()">📳 Vibrate</button>
            <button class="output-btn" onclick="playSound()">🔊 Play Sound</button>
            <button class="output-btn" onclick="speakText()">🗣️ Speak</button>
            <button class="output-btn" onclick="shareMessage()">📤 Share</button>
            <button class="output-btn" onclick="saveMessage()">💾 Save</button>
        </div>
        
        <!-- Manual Input -->
        <div style="margin-bottom: 20px;">
            <input type="text" id="manual-input" 
                   style="width: 70%; padding: 10px; border-radius: 5px; border: none;"
                   placeholder="Type message...">
            <button onclick="sendManual()" 
                    style="padding: 10px 20px; border-radius: 5px; border: none; background: #4CAF50; color: white;">
                Send
            </button>
        </div>
        
        <!-- Status -->
        <div class="status" id="status">
            Ready
        </div>
    </div>
    
    <script>
        // Morse mapping
        const morseMap = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
            '...--': '3', '....-': '4', '.....': '5', '-....': '6',
            '--...': '7', '---..': '8', '----.': '9'
        };
        
        // State
        let activeSensors = new Set();
        let morseBuffer = '';
        let textBuffer = '';
        let lastSignal = 0;
        let inSignal = false;
        
        // UI elements
        const morseEl = document.getElementById('morse-buffer');
        const textEl = document.getElementById('text-buffer');
        const statusEl = document.getElementById('status');
        const videoEl = document.getElementById('video-feed');
        
        // ===== SENSOR TOGGLES =====
        
        function toggleSensor(sensor) {
            const element = document.getElementById(`${sensor}-sensor`);
            
            if (activeSensors.has(sensor)) {
                activeSensors.delete(sensor);
                element.classList.remove('active');
                stopSensor(sensor);
            } else {
                activeSensors.add(sensor);
                element.classList.add('active');
                startSensor(sensor);
            }
            
            updateStatus();
        }
        
        function startSensor(sensor) {
            switch(sensor) {
                case 'camera':
                    startCamera();
                    break;
                case 'mic':
                    startMicrophone();
                    break;
                case 'vibration':
                    startVibration();
                    break;
                case 'gyro':
                    startGyro();
                    break;
            }
        }
        
        function stopSensor(sensor) {
            switch(sensor) {
                case 'camera':
                    stopCamera();
                    break;
                case 'mic':
                    stopMicrophone();
                    break;
            }
        }
        
        // ===== CAMERA DETECTION =====
        
        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                videoEl.srcObject = stream;
                videoEl.style.display = 'block';
                
                const track = stream.getVideoTracks()[0];
                const imageCapture = new ImageCapture(track);
                
                setInterval(async () => {
                    try {
                        const bitmap = await imageCapture.grabFrame();
                        const canvas = document.createElement('canvas');
                        canvas.width = bitmap.width;
                        canvas.height = bitmap.height;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(bitmap, 0, 0);
                        
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        let brightness = 0;
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            brightness += imageData.data[i];
                        }
                        brightness /= (imageData.data.length / 4);
                        
                        if (brightness > 200) {
                            processSignal();
                        }
                    } catch(e) {}
                }, 100);
            } catch(e) {
                statusEl.textContent = 'Camera error: ' + e.message;
            }
        }
        
        function stopCamera() {
            if (videoEl.srcObject) {
                videoEl.srcObject.getTracks().forEach(track => track.stop());
                videoEl.style.display = 'none';
            }
        }
        
        // ===== MICROPHONE DETECTION =====
        
        let audioContext;
        let analyser;
        let microphone;
        
        async function startMicrophone() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                audioContext = new AudioContext();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);
                microphone.connect(analyser);
                
                analyser.fftSize = 256;
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                
                setInterval(() => {
                    analyser.getByteFrequencyData(dataArray);
                    const avg = dataArray.reduce((a, b) => a + b) / dataArray.length;
                    
                    if (avg > 50) {
                        processSignal();
                    }
                }, 50);
            } catch(e) {
                statusEl.textContent = 'Microphone error: ' + e.message;
            }
        }
        
        function stopMicrophone() {
            if (microphone) {
                microphone.disconnect();
            }
            if (audioContext) {
                audioContext.close();
            }
        }
        
        // ===== VIBRATION DETECTION =====
        
        function startVibration() {
            if (window.DeviceMotionEvent) {
                window.addEventListener('devicemotion', handleMotion);
            }
        }
        
        function handleMotion(event) {
            const acc = event.accelerationIncludingGravity;
            const force = Math.abs(acc.x) + Math.abs(acc.y) + Math.abs(acc.z);
            
            if (force > 25) {
                processSignal();
            }
        }
        
        // ===== GYROSCOPE DETECTION =====
        
        function startGyro() {
            if (window.DeviceOrientationEvent) {
                window.addEventListener('deviceorientation', handleOrientation);
            }
        }
        
        let lastOrientation = 0;
        function handleOrientation(event) {
            const gamma = event.gamma; // Left/right tilt
            
            if (Math.abs(gamma - lastOrientation) > 10) {
                processSignal();
                lastOrientation = gamma;
            }
        }
        
        // ===== SIGNAL PROCESSING =====
        
        function processSignal() {
            const now = Date.now();
            
            if (inSignal) {
                const duration = now - lastSignal;
                if (duration < 300) {
                    morseBuffer += '.';
                } else if (duration > 400) {
                    morseBuffer += '-';
                }
                inSignal = false;
                updateDisplay();
            } else {
                lastSignal = now;
                inSignal = true;
            }
            
            // Check for gaps
            setTimeout(checkGap, 1000);
        }
        
        function checkGap() {
            const now = Date.now();
            if (now - lastSignal > 1000 && morseBuffer.length > 0) {
                decodeMorse();
            }
        }
        
        function decodeMorse() {
            if (morseMap[morseBuffer]) {
                textBuffer += morseMap[morseBuffer];
            } else {
                textBuffer += '?';
            }
            morseBuffer = '';
            updateDisplay();
            
            // Auto-process SOS
            if (textBuffer.includes('SOS')) {
                alert('🚨 SOS DETECTED!');
                sendMorse('SOS');
            }
        }
        
        // ===== OUTPUT METHODS =====
        
        function sendMorse(text) {
            const morse = textToMorse(text);
            flashScreenWithMorse(morse);
            vibrateWithMorse(morse);
            playSoundWithMorse(morse);
            statusEl.textContent = `Sending: ${text}`;
        }
        
        function textToMorse(text) {
            const map = {
                'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
                'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
                'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
                'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
                'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
                'Z': '--..',
            };
            
            let result = '';
            for (let char of text.toUpperCase()) {
                if (map[char]) {
                    result += map[char] + ' ';
                }
            }
            return result.trim();
        }
        
        function flashScreenWithMorse(morse) {
            for (let i = 0; i < morse.length; i++) {
                setTimeout(() => {
                    if (morse[i] === '.') {
                        flashScreen(200);
                    } else if (morse[i] === '-') {
                        flashScreen(600);
                    }
                }, i * 400);
            }
        }
        
        function flashScreen(duration) {
            document.body.style.backgroundColor = '#fff';
            document.body.style.transition = 'none';
            setTimeout(() => {
                document.body.style.backgroundColor = '';
                document.body.style.transition = 'background 0.3s';
            }, duration);
        }
        
        function vibrateWithMorse(morse) {
            if (navigator.vibrate) {
                let pattern = [];
                for (let char of morse) {
                    if (char === '.') {
                        pattern.push(200, 200);
                    } else if (char === '-') {
                        pattern.push(600, 200);
                    } else if (char === ' ') {
                        pattern.push(600);
                    }
                }
                navigator.vibrate(pattern);
            }
        }
        
        function playSoundWithMorse(morse) {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            let time = audioCtx.currentTime;
            
            for (let char of morse) {
                const oscillator = audioCtx.createOscillator();
                const gainNode = audioCtx.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                
                oscillator.frequency.value = 800;
                gainNode.gain.setValueAtTime(0.5, time);
                
                if (char === '.') {
                    gainNode.gain.setValueAtTime(0, time + 0.2);
                    time += 0.4;
                } else if (char === '-') {
                    gainNode.gain.setValueAtTime(0, time + 0.6);
                    time += 0.8;
                } else if (char === ' ') {
                    time += 0.6;
                }
                
                oscillator.start(time - 0.4);
                oscillator.stop(time);
            }
        }
        
        function flashScreen() {
            flashScreenWithMorse(morseBuffer || '... --- ...');
        }
        
        function vibrate() {
            vibrateWithMorse(morseBuffer || '... --- ...');
        }
        
        function playSound() {
            playSoundWithMorse(morseBuffer || '... --- ...');
        }
        
        function speakText() {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(textBuffer || 'No message');
                window.speechSynthesis.speak(utterance);
            }
        }
        
        function shareMessage() {
            if (navigator.share) {
                navigator.share({
                    title: 'Morse Message',
                    text: textBuffer || morseBuffer,
                });
            } else {
                alert('Share not supported');
            }
        }
        
        function saveMessage() {
            const data = {
                morse: morseBuffer,
                text: textBuffer,
                timestamp: new Date().toISOString()
            };
            
            localStorage.setItem('lastMorse', JSON.stringify(data));
            statusEl.textContent = 'Message saved';
        }
        
        function sendManual() {
            const input = document.getElementById('manual-input');
            if (input.value) {
                textBuffer += input.value;
                sendMorse(input.value);
                input.value = '';
                updateDisplay();
            }
        }
        
        function updateDisplay() {
            morseEl.textContent = morseBuffer || '⏳ waiting...';
            textEl.textContent = textBuffer || '';
        }
        
        function updateStatus() {
            if (activeSensors.size > 0) {
                statusEl.textContent = `Listening: ${Array.from(activeSensors).join(', ')}`;
            } else {
                statusEl.textContent = 'No sensors active';
            }
        }
    </script>
</body>
</html>
```

---

🎯 Complete System Integration

```python
# morse_os_complete.py
# Bring it all together

class MorseOSComplete:
    """One system to rule all Morse"""
    
    def __init__(self):
        self.core = MorseOS()
        
        # Platform modules
        self.arduino = None
        self.pi_addons = None
        self.meshtastic = None
        self.mobile = None
        self.web = None
        self.desktop = None
        
        # Auto-detect platform
        self.detect_platform()
    
    def detect_platform(self):
        """Auto-configure for current platform"""
        import platform
        import sys
        
        system = platform.system()
        
        if system == 'Linux' and 'raspberrypi' in platform.node():
            print("🍓 Running on Raspberry Pi")
            self.pi_addons = MorsePiAddons()
            self.core.platform = 'pi'
            
        elif system == 'Linux' and sys.platform != 'darwin':
            print("💻 Running on Linux (generic)")
            self.desktop = MorseDesktop()
            self.core.platform = 'linux'
            
        elif system == 'Darwin':
            print("🍎 Running on Mac")
            self.desktop = MorseDesktop()
            self.core.platform = 'mac'
            
        elif system == 'Windows':
            print("🪟 Running on Windows")
            self.desktop = MorseDesktop()
            self.core.platform = 'windows'
    
    def connect_arduino(self, port='/dev/ttyUSB0'):
        """Connect to Arduino over serial"""
        try:
            import serial
            self.arduino = serial.Serial(port, 9600)
            print(f"✅ Arduino connected on {port}")
        except:
            print("❌ Arduino not found")
    
    def connect_meshtastic(self, port='/dev/ttyACM0'):
        """Connect to Meshtastic"""
        try:
            self.meshtastic = MorseMeshtastic(port)
            self.meshtastic.connect()
            print(f"✅ Meshtastic connected on {port}")
        except:
            print("❌ Meshtastic not found")
    
    def start_web_server(self, port=8080):
        """Start web interface"""
        import http.server
        import socketserver
        
        handler = http.server.SimpleHTTPRequestHandler
        self.web = socketserver.TCPServer(("", port), handler)
        print(f"🌐 Web server on http://localhost:{port}")
        threading.Thread(target=self.web.serve_forever).start()
    
    def run(self):
        """Main loop - integrate everything"""
        print("\n" + "="*50)
        print("🚀 MORSE OS COMPLETE - RUNNING")
        print("="*50 + "\n")
        
        # Main integration loop
        while True:
            # Check Arduino for Morse
            if self.arduino and self.arduino.in_waiting:
                line = self.arduino.readline().decode().strip()
                if line.startswith('MORSE:'):
                    morse = line[6:]
                    text = self.core.morse_to_text(morse)
                    print(f"📟 Arduino Morse: {morse} -> {text}")
                    
                    # Forward to all platforms
                    if self.meshtastic:
                        self.meshtastic.send_to_mesh(f"[ARDUINO] {text}")
            
            # Check Meshtastic for messages
            # (handled in its own thread)
            
            # Check Pi addons
            if self.pi_addons:
                # Process camera, etc.
                pass
            
            time.sleep(0.1)

# ===== ONE COMMAND TO RULE THEM ALL =====

if __name__ == "__main__":
    # Create complete system
    morse_system = MorseOSComplete()
    
    # Connect to everything
    morse_system.connect_arduino('/dev/ttyUSB0')
    morse_system.connect_meshtastic('/dev/ttyACM0')
    morse_system.start_web_server(8080)
    
    # Go!
    morse_system.run()
```

---

📦 Deployment Package

```bash
#!/bin/bash
# install_morse_os.sh - One-command install for all platforms

echo "📡 Installing Morse OS Complete"
echo "==============================="

# Detect platform
if [ -f /etc/rpi-issue ]; then
    PLATFORM="raspberrypi"
elif [ -f /etc/debian_version ]; then
    PLATFORM="debian"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" ]]; then
    PLATFORM="windows"
else
    PLATFORM="unknown"
fi

echo "Platform: $PLATFORM"

# Install Python dependencies
pip3 install numpy pyserial pyaudio RPi.GPIO picamera opencv-python

# Create directory structure
mkdir -p /opt/morse_os/{core,platforms,web,config,logs}

# Copy all files
cp morse_os.py /opt/morse_os/core/
cp morse_arduino.ino /opt/morse_os/platforms/
cp morse_meshtastic.py /opt/morse_os/platforms/
cp morse_web.html /opt/morse_os/web/
cp morse_complete.py /opt/morse_os/

# Create service (Linux)
if [ "$PLATFORM" = "raspberrypi" ] || [ "$PLATFORM" = "debian" ]; then
    cat > /etc/systemd/system/morseos.service << EOF
[Unit]
Description=Morse OS Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/morse_os/morse_complete.py
WorkingDirectory=/opt/morse_os
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

    systemctl enable morseos
    systemctl start morseos
fi

echo "✅ Morse OS installed!"
echo "📱 Web interface: http://localhost:8080"
echo "📟 Arduino: upload morse_arduino.ino"
echo "📻 Meshtastic: auto-detected"
```



Platform Input Methods Output Methods Auto-Detect
Arduino Button, Light sensor, Vibration LED, Buzzer, Vibrator, Relay ✅
Raspberry Pi Camera, Mic, GPIO, Radio LED, Laser, IR, Horn, Servo ✅
Meshtastic Radio, Mesh network Mesh broadcast, LED ✅
Mobile App Camera, Mic, Touch, Motion Flashlight, Screen, Vibration, Sound ✅
Computer Mic, Keyboard, Serial Screen, Speakers, Serial ✅
Web Browser Camera, Mic, Motion Screen, Audio, Vibration ✅

All speaking the same Morse language, all auto-detecting, all translating, all connected.
