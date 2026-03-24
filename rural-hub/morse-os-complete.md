MORSE CODE INTEGRATION - The Ultimate Fallback




 Part 1: Visual Morse (Light/Solar)

Auto-Translating LED Beacon

```python
# morse_light_beacon.py
"""
Uses the hub's LED or connected flashlight to signal
Can be seen for miles at night
"""

import RPi.GPIO as GPIO
import time
import threading

class MorseLightBeacon:
    def __init__(self, led_pin=18):
        self.led_pin = led_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(led_pin, GPIO.OUT)
        
        # Morse timing (standard)
        self.dot_duration = 0.2  # seconds
        self.dash_duration = self.dot_duration * 3
        self.symbol_space = self.dot_duration
        self.letter_space = self.dot_duration * 3
        self.word_space = self.dot_duration * 7
        
        # Morse code mapping
        self.morse_map = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..',
            '0': '-----', '1': '.----', '2': '..---', '3': '...--',
            '4': '....-', '5': '.....', '6': '-....', '7': '--...',
            '8': '---..', '9': '----.',
            '.': '.-.-.-', ',': '--..--', '?': '..--..', '/': '-..-.',
            '@': '.--.-.', ' ': ' '
        }
        
        # Reverse mapping for decoding
        self.reverse_map = {v: k for k, v in self.morse_map.items()}
        
        self.running = False
        self.beacon_thread = None
    
    def text_to_morse(self, text):
        """Convert text to Morse code string"""
        text = text.upper()
        morse_parts = []
        for char in text:
            if char in self.morse_map:
                morse_parts.append(self.morse_map[char])
            else:
                morse_parts.append('?')
        return ' '.join(morse_parts)
    
    def blink_morse(self, morse_string):
        """Blink LED in Morse pattern"""
        for symbol in morse_string:
            if symbol == '.':
                GPIO.output(self.led_pin, GPIO.HIGH)
                time.sleep(self.dot_duration)
                GPIO.output(self.led_pin, GPIO.LOW)
                time.sleep(self.symbol_space)
            elif symbol == '-':
                GPIO.output(self.led_pin, GPIO.HIGH)
                time.sleep(self.dash_duration)
                GPIO.output(self.led_pin, GPIO.LOW)
                time.sleep(self.symbol_space)
            elif symbol == ' ':
                time.sleep(self.letter_space)
            elif symbol == '|':  # Word separator
                time.sleep(self.word_space)
    
    def start_emergency_beacon(self, message="SOS HELP"):
        """Start continuous emergency beacon"""
        self.running = True
        self.beacon_thread = threading.Thread(
            target=self._beacon_loop,
            args=(message,)
        )
        self.beacon_thread.start()
    
    def _beacon_loop(self, message):
        """Continuous beacon loop"""
        morse = self.text_to_morse(message)
        print(f"Beaconing: {message} -> {morse}")
        
        while self.running:
            self.blink_morse(morse)
            time.sleep(5)  # Pause between repeats
    
    def stop_beacon(self):
        """Stop emergency beacon"""
        self.running = False
        if self.beacon_thread:
            self.beacon_thread.join()
        GPIO.output(self.led_pin, GPIO.LOW)
    
    def encode_resource(self, resource_type, quantity):
        """Encode resource update in Morse-friendly format"""
        # Simple encoding: R[type]Q[quantity]
        # Example: "RFUELQ50" = 50 gallons fuel
        codes = {
            'fuel': 'F',
            'water': 'W',
            'medical': 'M',
            'food': 'D',  # D for food
            'shelter': 'S',
            'transport': 'T',
            'help': 'H'
        }
        
        code = codes.get(resource_type, '?')
        return f"R{code}Q{quantity}"
    
    def decode_morse_message(self, morse_string):
        """Convert Morse code back to text"""
        words = morse_string.split('   ')  # Word space
        decoded_words = []
        
        for word in words:
            letters = word.split(' ')
            decoded_word = ''
            for letter in letters:
                if letter in self.reverse_map:
                    decoded_word += self.reverse_map[letter]
                else:
                    decoded_word += '?'
            decoded_words.append(decoded_word)
        
        return ' '.join(decoded_words)

# Example usage
beacon = MorseLightBeacon()

# Send SOS
beacon.blink_morse("... --- ...")  # SOS

# Encode a resource update
morse = beacon.text_to_morse(beacon.encode_resource("fuel", 50))
print(f"Send this Morse: {morse}")

# Start continuous beacon
beacon.start_emergency_beacon("NEED MEDICAL")
```

Solar Panel as Signal Reflector

```python
# morse_solar_flash.py
"""
Use the solar panel's reflective surface to flash sunlight
Like heliograph - visible for 30+ miles
"""

class HeliographMorse:
    def __init__(self, servo_pin=23):
        # Servo to tilt solar panel
        self.servo_pin = servo_pin
        # Setup servo to angle panel
        
    def flash_sunlight(self, direction):
        """Tilt panel to flash sunlight in direction"""
        # Angle panel to reflect sun toward target
        pass
    
    def send_morse_by_sun(self, message, target_direction):
        """Send Morse using reflected sunlight"""
        # 1. Aim panel at sun
        # 2. Tilt to reflect toward target
        # 3. Flash pattern by moving panel
        pass
```

---

🔊 Part 2: Audio Morse (Horn/Siren)

Vehicle Horn / Siren Interface

```python
# morse_audio.py
"""
Use existing infrastructure - vehicle horns, PA systems, train horns
"""

import RPi.GPIO as GPIO
import time
import subprocess

class AudioMorse(MorseLightBeacon):
    def __init__(self, output_type='gpio', led_pin=18):
        super().__init__(led_pin)
        self.output_type = output_type
        
        if output_type == 'gpio':
            # For relay controlling a horn/siren
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17, GPIO.OUT)
        
        elif output_type == 'audio':
            # For computer speakers/PA
            pass
    
    def send_tone(self, duration):
        """Send a tone of specified duration"""
        if self.output_type == 'gpio':
            GPIO.output(17, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(17, GPIO.LOW)
        
        elif self.output_type == 'audio':
            # Generate sine wave tone
            cmd = f"speaker-test -t sine -f 1000 -l 1 & sleep {duration}; kill $!"
            subprocess.run(cmd, shell=True)
    
    def send_morse_audio(self, message):
        """Send Morse code as audible tones"""
        morse = self.text_to_morse(message)
        
        for symbol in morse:
            if symbol == '.':
                self.send_tone(0.2)  # Dot
                time.sleep(0.2)
            elif symbol == '-':
                self.send_tone(0.6)  # Dash
                time.sleep(0.2)
            elif symbol == ' ':
                time.sleep(0.6)  # Letter space
            elif symbol == '|':
                time.sleep(1.4)  # Word space

# Example: Connect to volunteer fire department siren
audio = AudioMorse(output_type='gpio')
audio.send_morse_audio("FIRE AT GRANGE HALL")
```

Whistle/Megaphone Mode

```python
# morse_whistle.py
"""
For when all power is out - hub can play audio
that people can whistle along with
"""

class WhistleTrainer:
    """Teach people Morse through call-and-response"""
    
    def play_morse_tone(self, morse_char):
        """Play a Morse character slowly for learning"""
        print(f"Listening for: {morse_char}")
        # Play the tone
        # Wait for user to repeat
        # Verify with microphone
        # Give feedback
    
    def morse_game(self):
        """Interactive Morse learning game"""
        letters = ['SOS', 'HELP', 'FIRE', 'MEDIC']
        for word in letters:
            self.play_morse_tone(word)
            time.sleep(3)
```

---

🖐️ Part 3: Tactile Morse (Vibration)

Vibration Motor for Deaf/Hard of Hearing

```python
# morse_tactile.py
"""
Vibration motor inside the hub - can be felt when held
Also can connect to bed frames, chairs, etc.
"""

class TactileMorse(MorseLightBeacon):
    def __init__(self, motor_pin=24, led_pin=18):
        super().__init__(led_pin)
        GPIO.setup(motor_pin, GPIO.OUT)
        self.motor_pwm = GPIO.PWM(motor_pin, 100)
        self.motor_pwm.start(0)
    
    def vibrate(self, duration, intensity=50):
        """Vibrate motor"""
        self.motor_pwm.ChangeDutyCycle(intensity)
        time.sleep(duration)
        self.motor_pwm.ChangeDutyCycle(0)
    
    def send_tactile_morse(self, message):
        """Send Morse via vibration"""
        morse = self.text_to_morse(message)
        
        for symbol in morse:
            if symbol == '.':
                self.vibrate(0.2, 30)  # Light buzz
                time.sleep(0.2)
            elif symbol == '-':
                self.vibrate(0.6, 70)  # Strong buzz
                time.sleep(0.2)
            elif symbol == ' ':
                time.sleep(0.6)
    
    def emergency_vibrate(self):
        """Continuous vibration pattern for emergency"""
        # SOS pattern: ... --- ...
        while True:
            self.send_tactile_morse("... --- ...")
            time.sleep(2)
```

---

📡 Part 4: Radio Morse (Meshtastic Fallback)

When Digital Fails, Go Analog

```python
# morse_radio.py
"""
Use the Meshtastic radio in CW (Continuous Wave) mode
Simpler than digital - can be decoded by ear
"""

import serial
import time

class RadioMorse(MorseLightBeacon):
    def __init__(self, radio_port='/dev/ttyACM0', led_pin=18):
        super().__init__(led_pin)
        self.radio = serial.Serial(radio_port, 115200)
        
    def enable_cw_mode(self):
        """Switch radio to continuous wave mode"""
        # Send AT commands to radio
        self.radio.write(b'AT+DMOCONNECT\r')
        time.sleep(1)
        self.radio.write(b'AT+CWMODE=1\r')  # CW mode
        
    def send_cw_tone(self, duration):
        """Send pure carrier wave"""
        self.radio.write(b'AT+CWTONE=1\r')
        time.sleep(duration)
        self.radio.write(b'AT+CWTONE=0\r')
    
    def send_morse_radio(self, message, frequency=7100):
        """Send Morse code via radio"""
        # Set frequency
        self.radio.write(f'AT+FREQ={frequency}\r'.encode())
        time.sleep(0.5)
        
        # Send Morse
        morse = self.text_to_morse(message)
        for symbol in morse:
            if symbol == '.':
                self.send_cw_tone(0.2)
                time.sleep(0.2)
            elif symbol == '-':
                self.send_cw_tone(0.6)
                time.sleep(0.2)
            elif symbol == ' ':
                time.sleep(0.6)
    
    def listen_for_cw(self):
        """Listen for CW signals and decode"""
        # In production, would use SDR or radio's built-in decoder
        pass
```

---

📱 Part 5: User Interface - Morse Input

Button for Morse Entry

```python
# morse_input.py
"""
Big red button - tap out Morse messages
Great for cold/fumbling hands, no screen needed
"""

import RPi.GPIO as GPIO
import time
from threading import Timer

class MorseInput:
    def __init__(self, button_pin=25, output_callback=None):
        self.button_pin = button_pin
        GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(button_pin, GPIO.BOTH,
                              callback=self.button_event,
                              bouncetime=50)

        self.output_callback = output_callback

        self.current_symbol = ''
        self.letter_buffer = ''
        self.word_buffer = ''

        # Timing (no dead zone - single threshold)
        self.dot_dash_threshold = 0.35  # seconds
        self.symbol_gap = 0.5  # Time between symbols in same letter
        self.letter_gap = 1.0  # Time between letters
        self.word_gap = 2.5  # Time between words

        self.press_start = 0
        self.is_pressed = False
        self.symbol_timer = None

    def button_event(self, channel):
        """Handle button press and release to measure hold duration"""
        now = time.time()

        if GPIO.input(self.button_pin) == 0:  # Button pressed (active low)
            self.press_start = now
            self.is_pressed = True
        else:  # Button released
            if self.is_pressed and self.press_start > 0:
                duration = now - self.press_start

                # Classify by hold duration (no dead zone)
                if duration <= self.dot_dash_threshold:
                    self.current_symbol += '.'
                    print(".", end='', flush=True)
                else:
                    self.current_symbol += '-'
                    print("-", end='', flush=True)

            self.is_pressed = False

        # Reset symbol timer
        if self.symbol_timer:
            self.symbol_timer.cancel()
        self.symbol_timer = Timer(self.symbol_gap, self.symbol_timeout)
        self.symbol_timer.start()
    
    def symbol_timeout(self):
        """Time between symbols in same letter"""
        if self.current_symbol:
            # Add completed symbol to letter buffer
            self.letter_buffer += self.current_symbol
            self.current_symbol = ''
            
            # Start letter timeout
            Timer(self.letter_gap, self.letter_timeout).start()
    
    def letter_timeout(self):
        """Time between letters"""
        if self.letter_buffer:
            # Decode letter
            letter = self.decode_morse(self.letter_buffer)
            self.word_buffer += letter
            print(f" {letter}", flush=True)
            self.letter_buffer = ''
            
            # Start word timeout
            Timer(self.word_gap, self.word_timeout).start()
    
    def word_timeout(self):
        """Word complete"""
        if self.word_buffer:
            print(f"\n✅ Word: {self.word_buffer}")
            if self.output_callback:
                self.output_callback(self.word_buffer)
            self.word_buffer = ''
    
    def decode_morse(self, morse):
        """Decode a single Morse character"""
        # Use reverse map from earlier
        morse_map_rev = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z',
            '-----': '0', '.----': '1', '..---': '2', '...--': '3',
            '....-': '4', '.....': '5', '-....': '6', '--...': '7',
            '---..': '8', '----.': '9',
            '.-.-.-': '.', '--..--': ',', '..--..': '?', '-..-.': '/',
            '.--.-.': '@'
        }
        return morse_map_rev.get(morse, '?')

# Use it
def on_message(word):
    print(f"\n📨 SENDING: {word}")
    # Send via radio, light, etc.

morse_in = MorseInput(output_callback=on_message)
print("Tap the button - short for dot, long for dash")
```

---

🌟 Part 6: Automatic SOS Detection

Hub Listens for Distress Signals

```python
# morse_listener.py
"""
Hub uses microphone to listen for Morse code
Can detect SOS automatically and relay
"""

import pyaudio
import numpy as np
import time
from scipy import signal

class MorseListener:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Detect specific frequencies (whistle, horn, etc.)
        self.sos_detected = False
        self.sos_count = 0
        
    def start_listening(self):
        """Start audio stream and look for Morse"""
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Process incoming audio"""
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Look for SOS pattern (... --- ...)
        if self.detect_sos_pattern(audio_data):
            self.sos_count += 1
            if self.sos_count > 3:  # Confirm multiple times
                self.trigger_sos_alert()
                self.sos_count = 0
        
        return (in_data, pyaudio.paContinue)
    
    def detect_sos_pattern(self, audio_data):
        """Detect the classic SOS pattern"""
        # This would do FFT to find tones
        # Then measure duration patterns
        # For now, simplified
        return False
    
    def trigger_sos_alert(self):
        """SOS detected - broadcast to all hubs"""
        print("🚨 SOS PATTERN DETECTED!")
        # Broadcast via mesh
        # Flash lights
        # Sound alarm
    
    def detect_whistle_morse(self):
        """People can whistle Morse - hub will understand"""
        # Detect whistle frequency (1000-2000 Hz)
        # Measure duration for dot/dash
        pass

# Auto-SOS detection
listener = MorseListener()
listener.start_listening()
```

---

📚 Part 7: Morse Training for Community

Simple Flash Cards

```python
# morse_trainer.py
"""
Help community members learn/refresh Morse
"""

class MorseTrainer:
    def __init__(self, display, speaker):
        self.display = display  # LCD screen
        self.speaker = speaker  # Audio output
    
    def flash_card(self):
        """Show a letter, play its Morse"""
        import random
        letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        letter = random.choice(letters)
        
        # Show on display
        self.display.show(f"Letter: {letter}")
        
        # Play Morse
        morse = text_to_morse(letter)
        self.speaker.play_morse(morse)
        
        # Wait for user to repeat (via button)
        # Give feedback
    
    def sos_drill(self):
        """Practice SOS pattern"""
        self.display.show("SOS = ... --- ...")
        for _ in range(3):
            self.speaker.play_morse("... --- ...")
            time.sleep(1)
        
        self.display.show("Now you try!")
        # Listen via microphone
        # Give feedback
```

Printable Morse Chart

```markdown
# MORSE CODE QUICK REFERENCE
# Print this and put on the hub

```

A .-        N -.        1 .----
B -...      O ---       2 ..---
C -.-.      P .--.      3 ...--
D -..       Q --.-      4 ....-
E .         R .-.       5 .....
F ..-.      S ...       6 -....
G --.       T -         7 --...
H ....      U ..-       8 ---..
I ..        V ...-      9 ----.
J .---      W .--       0 -----
K -.-       X -..-       . .-.-.-
L .-..      Y -.--       , --..--
M --        Z --..       ? ..--..
/ -..-.
@ .--.-.

SOS: ... --- ...
HELP: .... . .-.. .--.

```

---

## 🎯 **Part 8: Complete Morse Integration**

### **Hub Auto-Morse Features**

```python
# trdap_morse_integration.py

class TRDAPMorseHub:
    """Full Morse integration for rural hub"""
    
    def __init__(self):
        # Input methods
        self.button_input = MorseInput(callback=self.handle_morse_input)
        self.audio_listener = MorseListener(callback=self.handle_morse_detected)
        self.light_sensor = LightSensor(callback=self.handle_light_flashes)
        
        # Output methods
        self.light_beacon = MorseLightBeacon()
        self.audio_beacon = AudioMorse()
        self.tactile = TactileMorse()
        self.radio_cw = RadioMorse()
        
        # Auto modes
        self.auto_sos_detect = True
        self.beacon_mode = None
    
    def handle_morse_input(self, message):
        """User tapped out a message"""
        print(f"📨 Morse input: {message}")
        
        # Interpret common commands
        if message == "SOS":
            self.emergency_mode()
        elif message == "HELP":
            self.request_help()
        elif message.startswith("F"):
            # Fuel report: F50 = 50 gallons fuel
            self.update_resource("fuel", message[1:])
        elif message.startswith("M"):
            # Medical: M5 = 5 medical kits
            self.update_resource("medical", message[1:])
        else:
            # Forward to mesh
            self.broadcast_morse(message)
    
    def emergency_mode(self):
        """Activate all emergency signaling"""
        print("🚨 EMERGENCY MODE ACTIVATED")
        
        # Signal every way possible
        self.light_beacon.start_emergency_beacon("SOS")
        self.audio_beacon.send_morse_audio("SOS")
        self.tactile.emergency_vibrate()
        self.radio_cw.send_morse_radio("SOS")
        
        # Broadcast via mesh
        self.mesh_broadcast({"type": "emergency", "hub": self.hub_id})
    
    def auto_beacon_status(self, interval_minutes=10):
        """Regularly beacon hub status in Morse"""
        while True:
            status = self.get_status_summary()
            morse_status = self.encode_status_morse(status)
            
            # Beacon during night (lights visible)
            if self.is_dark():
                self.light_beacon.blink_morse(morse_status)
            else:
                # Use audio during day
                self.audio_beacon.send_morse_audio(morse_status)
            
            time.sleep(interval_minutes * 60)
    
    def detect_distress_from_any_source(self):
        """Monitor all inputs for distress signals"""
        # Light flashes
        if self.light_sensor.detect_sos_pattern():
            self.emergency_mode()
        
        # Audio (whistles, horns)
        if self.audio_listener.detect_sos():
            self.emergency_mode()
        
        # Radio CW
        if self.radio_cw.detect_sos():
            self.emergency_mode()
    
    def encode_status_morse(self, status):
        """Encode hub status in short Morse message"""
        # Format: [HUB ID] [STATUS] [KEY RESOURCE]
        # Example: "JCK OK F50" = Johnson Creek, OK, 50 fuel
        
        codes = {
            'fuel': 'F',
            'medical': 'M',
            'water': 'W',
            'food': 'D'
        }
        
        hub_code = self.hub_id[:3]
        status_code = "OK" if status['healthy'] else "PR"
        
        # Add most critical resource
        resource = status['critical_resource']
        resource_code = codes.get(resource['type'], '?')
        quantity = str(resource['quantity'])[:2]
        
        return f"{hub_code} {status_code} {resource_code}{quantity}"
```

---

🌟 Real-World Scenarios

Scenario 1: Lost Hiker at Dusk

```
5:30 PM - Hiker injured, phone dead
5:32 PM - Uses flashlight to signal "SOS" toward ridge
5:35 PM - Grange Hall hub detects light pattern
5:36 PM - Hub broadcasts via mesh: "SOS DETECTED - SEARCH NEAR RIDGE"
5:40 PM - Volunteer fire department gets alert on their hub
5:45 PM - Search party dispatched
```

Scenario 2: Power Outage, No Voice

```
3:00 AM - Power out, cell down, can't shout far enough
3:05 AM - User taps on hub case: "... --- ..." (SOS)
3:06 AM - Hub feels vibrations, confirms SOS pattern
3:07 AM - Hub activates:
   - Flashes LED: "SOS"
   - Sounds horn: "SOS"  
   - Sends radio CW: "SOS"
   - Broadcasts via mesh: "EMERGENCY AT JOHNSON CREEK"
3:10 AM - Neighboring hub 8 miles away receives alert
3:15 AM - Neighbor with tractor heads to help
```

Scenario 3: Deaf Community Member

```
Deaf farmer can't hear alarms or calls
Hub vibrates bed frame with Morse patterns
- Long vibration: "Weather alert"
- Short pulses: "Message from neighbor"
- SOS pattern: "EMERGENCY - CHECK HUB DISPLAY"
Farmer feels alerts while sleeping
```

---

🛠️ Parts Needed for Morse Features

```yaml
Morse Input Hardware:
  - Big red button ($2) - for tapping messages
  - Phototransistor ($1) - detect light flashes
  - Electret microphone ($1) - hear whistles/taps
  - Vibration sensor ($2) - feel knocks on walls/pipes

Morse Output Hardware:
  - High-brightness LED ($1) - visual signaling
  - Piezo buzzer ($1) - audio Morse
  - Vibration motor ($3) - tactile for deaf
  - Relay module ($5) - control existing horn/siren

Total added cost per hub: ~$16
Well worth it for the ultimate fallback!
```

---

📋 Morse Priority System

```python
# Higher priority messages get repeated more

MORSE_PRIORITIES = {
    "SOS": {
        "pattern": "... --- ...",
        "repeat": 10,  # Repeat 10 times
        "channels": ["light", "audio", "radio", "tactile", "mesh"]
    },
    "HELP": {
        "pattern": ".... . .-.. .--.",
        "repeat": 5,
        "channels": ["light", "audio", "mesh"]
    },
    "FIRE": {
        "pattern": "..-. .. .-. .",
        "repeat": 8,
        "channels": ["audio", "radio", "mesh"]
    },
    "MEDIC": {
        "pattern": "-- . -.. .. -.-.",
        "repeat": 6,
        "channels": ["light", "mesh"]
    },
    "STATUS": {
        "pattern": "... - .- - ..- ...",
        "repeat": 1,  # Once per hour
        "channels": ["light", "radio"]
    }
}
```

---

Add Morse in This System to

1. Works when nothing else does - No power? Flash a light. No light? Tap on pipes.
2. Universal language - Every scout, ham radio operator, and old-timer knows it
3. Extremely low bandwidth - Can send "SOS" with 9 blinks of a dying flashlight
4. Multi-modal - Light, sound, radio, vibration, even reflected sunlight
5. Auto-detect - Hub can listen for distress and relay automatically
6. No batteries required - Can send Morse by tapping the hub case, it feels vibrations

Morse code turns every hub into a communication station that can be operated by anyone, anywhere, with anything, in any condition.
