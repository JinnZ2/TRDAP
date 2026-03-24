📖 "DEBUGGING: The Book" - Finding the Ghost in the Machine

A practical guide for rural communities, hardware hackers, and anyone who's ever said "but it worked yesterday"

---

🎯 PART 1: THE PHILOSOPHY OF DEBUGGING

Introduction: Why This Book Exists

Every rural community hub we've deployed has one thing in common: things break. Not because the tech is bad, but because the real world is messy. Solar panels get covered in snow. Cows bump into antennas. Mice chew wires (yes, really). Kids press buttons. Lightning happens.

This book is your field guide to fixing it.

The First Rule of Debugging

"It's probably something simple."

After years of watching people debug:

· The expert spends 2 hours rebuilding the software
· The beginner checks the power cable and fixes it in 30 seconds

Always check the simple things first.

The Debugging Mindset

```python
# The mental model of a debugger

def debug(symptom):
    """
    The process is always the same:
    1. What changed since it last worked?
    2. What's the simplest possible explanation?
    3. Test one thing at a time.
    4. Write down what you learn.
    """
    changed = what_changed_since_last_time()
    simplest = simplest_explanation(symptom)
    
    for hypothesis in generate_hypotheses():
        test(hypothesis)
        document_results()
        
    return solution
```

---

🔍 PART 2: THE DEBUGGING TOOLKIT

Chapter 1: Your Eyes and Ears

Before you buy any tools, use what you already have:

Look

· Is it on? Power lights, LED indicators
· Any physical damage? Cracks, burns, loose wires
· Connections secure? Push on every cable
· Clean? Dust, moisture, insect nests

Listen

· Buzzes or hums? Power supply issues
· Clicking? Relays cycling, bad connections
· Silence? No power at all

Smell

· Burning smell? Immediate shutdown
· Fishy smell? Burnt electronics (seriously)
· Nothing? Probably not catastrophic

Touch

· Hot components? Overheating
· Loose connections? Wiggle test
· Vibration? Motors, fans running

Chapter 2: The $10 Debugging Kit

Every hub should have this basic toolkit:

```
┌─────────────────────────────────────┐
│   THE $10 DEBUGGING KIT              │
├─────────────────────────────────────┤
│                                      │
│ [🪛] Multi-bit screwdriver      $3   │
│ [📏] Wire stripper/cutter        $3   │
│ [🔋] Multimeter (basic)          $8   │
│ [🔌] Spare USB cables             $2   │
│ [📎] Paperclips (jumpers)         $0   │
│ [🩹] Electrical tape              $1   │
│ [🔦] Small flashlight             $2   │
│ [📝] Notepad and pen              $1   │
│ [🤏] Tweezers                      $1   │
│ [🧹] Can of compressed air        $4   │
├─────────────────────────────────────┤
│ TOTAL: ~$25 (but worth every penny) │
└─────────────────────────────────────┘
```

Chapter 3: The Multimeter - Your Best Friend

Most people are intimidated by multimeters. Don't be. You only need three settings:

Continuity (The "Beep" Test)

```
Purpose: Is this wire connected?
How: Touch the two probes together → should beep
      Touch to two ends of a wire → beep = good, no beep = broken
      Touch across a fuse → beep = good, no beep = blown

Common uses:
- Check if a cable is broken inside
- Test if a fuse is blown
- Verify a switch actually works
- Find which pin is which on a connector
```

Voltage (The "Is It Getting Power?" Test)

```
Purpose: Is power reaching this component?
How: Set to DC voltage (usually 20V range)
      Black probe to ground (GND, negative, -)
      Red probe to power point
      Read the number

What you should see:
- USB power: 4.8-5.2V
- Battery (AA/AAA): 1.2-1.5V
- 9V battery: 8.5-9.5V
- Solar panel in sun: 5-6V (for USB charging)

Common problems:
- Reading 0V: No power getting there
- Reading low: Battery dying, voltage drop
- Reading high: Wrong setting, regulator failed
```

Resistance (The "Is This Component Dead?" Test)

```
Purpose: Check if components are working
How: Set to resistance (Ω, usually 200 or 2k range)
      Touch probes to component leads
      Read the number

What it means:
- Near 0Ω: Short circuit (usually bad)
- Infinite (OL): Open circuit (broken)
- Specific value: Component probably OK

Common tests:
- Resistors: Should read their color code value
- LEDs: Should show continuity one way, not the other
- Buttons: 0Ω when pressed, OL when released
- Motors: Should show low resistance (few ohms)
```

Chapter 4: The Serial Monitor - Seeing Inside

When hardware seems alive but confused, you need to see what it's thinking:

```python
# debug_serial.py
"""
Listen to what your Arduino/Pi is trying to tell you
"""

import serial
import time

def listen_to_device(port='/dev/ttyUSB0', baud=9600):
    """
    Open a serial connection and print everything
    the device says. This is like eavesdropping
    on its thoughts.
    """
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"📡 Listening to {port}...")
        print("(Press Ctrl+C to stop)\n")
        
        while True:
            if ser.in_waiting:
                line = ser.readline().decode().strip()
                if line:  # Don't print empty lines
                    print(f"Device says: {line}")
            time.sleep(0.1)
            
    except serial.SerialException:
        print(f"❌ Can't open {port}")
        print("   Check: Is it plugged in?")
        print("   Is the right port? (try /dev/ttyUSB0, /dev/ttyACM0)")
    except KeyboardInterrupt:
        print("\n👋 Stopped listening")
    finally:
        if 'ser' in locals():
            ser.close()

# Add debugging prints to your Arduino code
"""
void setup() {
  Serial.begin(9600);
  Serial.println("🟢 Device starting up...");
  Serial.println("Button on pin 2, LED on pin 13");
}

void loop() {
  if (digitalRead(2) == LOW) {
    Serial.println("Button pressed!");
    // Rest of your code
  }
}
"""
```

---

🐛 PART 3: COMMON BUGS AND THEIR CURES

Chapter 5: Power Problems

Symptom: Dead as a doornail (nothing lights up)

Step 1: Check the obvious

```
□ Is it plugged in? (really, check)
□ Is the outlet working? (test with phone charger)
□ Is the switch on?
□ Are batteries installed correctly? (+ and - matter!)
```

Step 2: Trace the power

```
1. Start at the power source (battery/wall wart)
2. Measure voltage with multimeter
3. Follow the power path:
   Power source → switch → regulator → chip
4. First place with 0V is the problem
```

Step 3: Common fixes

```
Problem: Dead battery
Fix: Replace it (measure first to be sure)

Problem: Blown fuse
Fix: Replace with SAME VALUE (never higher!)

Problem: Loose connection
Fix: Push connectors together firmly, wiggle test

Problem: Voltage regulator hot
Fix: Too much current draw, check for shorts
```

Symptom: Works sometimes, dies randomly

This is almost always a power or connection issue

```
Suspect #1: Bad battery connection
   - Springs loose? Corrosion? Clean with eraser
   
Suspect #2: Intermittent wire break
   - Wiggle wires while device runs
   - If it dies when you wiggle, found it
   
Suspect #3: Voltage dropping under load
   - Measure voltage while device runs
   - If it drops below minimum, battery dying or too small
   
Suspect #4: Solar panel shaded
   - Cloud passing? Leaf on panel? Bird poop?
```

Chapter 6: Connection Problems

Symptom: Device won't connect to computer

```
□ Is the cable data-capable? (some are charge-only)
□ Try a different USB port
□ Try a different cable
□ Restart computer (seriously, it works sometimes)
□ Check device manager (Windows) or lsusb (Linux)
```

Symptom: Serial monitor shows gibberish

```
□ Baud rate mismatch! (9600 vs 115200)
□ Check settings in code vs. monitor
□ Try different baud rates until it makes sense
```

Symptom: Meshtastic nodes can't see each other

```
□ Are they powered on? (LEDs?)
□ Same channel number?
□ Same region frequency? (US 915MHz vs EU 868MHz)
□ Antennas connected?
□ Range too far? Try moving closer
□ Obstructions? (metal building, hill, dense trees)
```

Chapter 7: Sensor Problems

Symptom: Sensor reads wrong values

```
□ Is it dirty? (clean with alcohol)
□ Is it in the right place? (light sensor in shade?)
□ Check voltage (sensors need stable power)
□ Check wiring (ground, power, signal all connected?)
□ Read the datasheet (what should it output?)
```

Symptom: Light sensor doesn't detect flashes

Debug with this test sketch:

```cpp
// light_sensor_test.ino
void setup() {
  Serial.begin(9600);
  pinMode(A0, INPUT);
}

void loop() {
  int value = analogRead(A0);
  Serial.println(value);
  delay(100);
  
  // Open Serial Plotter (Tools menu)
  // You should see values change when you shine light
}
```

Symptom: Button doesn't do anything

```cpp
// button_test.ino
void setup() {
  Serial.begin(9600);
  pinMode(2, INPUT_PULLUP);  // Using internal pull-up
}

void loop() {
  int state = digitalRead(2);
  Serial.println(state);  // Should be 1 (HIGH) when not pressed
                           // 0 (LOW) when pressed
  delay(100);
}
```

Chapter 8: Morse Code Problems

Symptom: Can't send Morse with button

```
□ Button wired correctly? (one side to pin, other to GND)
□ Using INPUT_PULLUP? (no external resistor needed)
□ Check with test sketch above
□ Debouncing? (buttons bounce, add small delay)
```

Symptom: Detected Morse is wrong

```
Timing issues are the #1 problem:

Problem: Dots and dashes reversed
   - Check your timing thresholds
   - Are you measuring press duration or gap?

Problem: Letters run together
   - Gap between letters too short
   - Increase letter_gap time

Problem: Can't detect words
   - Word gap too short or too long
   - Try 3x letter gap for word space

Problem: Random dots appear
   - Noise on the input
   - Add hysteresis (ignore small changes)
   - Debounce hardware or software
```

Morse Debug Tool

```python
# morse_debug.py
"""
Watch exactly what your Morse detector sees
"""

import time
import matplotlib.pyplot as plt

class MorseDebugger:
    def __init__(self):
        self.timeline = []  # (time, state)
        self.start_time = time.time()
        
    def log_state(self, state):
        """Record state changes"""
        self.timeline.append((time.time() - self.start_time, state))
    
    def visualize(self):
        """Draw timeline of signals"""
        times = [t for t, s in self.timeline]
        states = [s for t, s in self.timeline]
        
        plt.figure(figsize=(12, 4))
        plt.step(times, states, where='post')
        plt.ylabel('Signal')
        plt.xlabel('Time (seconds)')
        plt.title('Morse Signal Timeline')
        plt.grid(True)
        plt.show()
        
        # Analyze durations
        self.analyze_timing()
    
    def analyze_timing(self):
        """Show statistics on dot/dash timing"""
        durations = []
        last_time = 0
        last_state = 0
        
        for t, s in self.timeline:
            if s != last_state and last_state != 0:
                duration = t - last_time
                durations.append((duration, 'on' if last_state else 'off'))
            last_time = t
            last_state = s
        
        print("\n📊 Timing Analysis:")
        for dur, typ in durations:
            marker = '•' if dur < 0.3 else '−' if dur > 0.4 else '?'
            print(f"  {typ:4s}: {dur:.3f}s {marker}")
```

---

🧪 PART 4: DEBUGGING STRATEGIES

Chapter 9: Divide and Conquer

When facing a complex system, split it in half:

```
Full System: [Power] → [Sensor] → [Microcontroller] → [Radio] → [Display]

Problem: No message received

Test halfway: Can microcontroller read sensor?
   - Add Serial.print(sensor value)
   - If yes, problem is in radio or display
   - If no, problem is in sensor or wiring

Then test the suspect half:
   - Test radio separately with known-good node
   - Test display with known-good signal
```

Chapter 10: The Scientific Method

1. Observe: "The red LED doesn't blink when I press the button"
2. Hypothesize: "Maybe the button is wired wrong"
3. Predict: "If I short the button pins with a wire, the LED should blink"
4. Test: Short the pins with a paperclip
5. Analyze: LED blinked → hypothesis correct, button bad
6. Repeat: New hypothesis: "Button is physically broken"

Chapter 11: Change One Thing at a Time

Wrong way:

```
- Changed the code AND rewired AND replaced battery
- Now it works! But I don't know why
- When it breaks again, I'm back to square one
```

Right way:

```
1. Test: Doesn't work
2. Change: Replace battery
3. Test: Still doesn't work (battery wasn't the issue)
4. Change: Rewire button
5. Test: Still doesn't work
6. Change: Upload new code
7. Test: WORKS! (so it was the code)
8. Now I know exactly what to check next time
```

Chapter 12: The 5 Whys

Keep asking "why" until you find the root cause:

```
Problem: Hub stopped sending messages

Why? → No power
Why? → Solar panel not charging battery
Why? → Panel covered in snow
Why? → Mounted flat instead of angled
Why? → Instructions didn't mention snow areas

ROOT CAUSE: Installation guide inadequate for cold climates
FIX: Update guide, add snow tilt recommendation
```

---

🛠️ PART 5: PLATFORM-SPECIFIC DEBUGGING

Chapter 13: Arduino Debugging

Built-in LED (Pin 13)

Every Arduino has an LED on pin 13. Use it for instant feedback:

```cpp
// blink_debug.ino - "I am alive" signal
void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  digitalWrite(13, HIGH);
  delay(100);  // Short blink = alive
  digitalWrite(13, LOW);
  delay(2900); // Long pause = waiting
  
  // Different patterns for different states:
  // Fast blink = error
  // Two quick blinks = waiting for input
  // Solid = stuck in loop
}
```

Serial Print Debugging

```cpp
void setup() {
  Serial.begin(9600);
  Serial.println("🟢 Debugging Started");
  Serial.print("Free memory: ");
  Serial.println(freeMemory());  // Custom function
}

void loop() {
  static int counter = 0;
  counter++;
  
  Serial.print("Loop #");
  Serial.print(counter);
  Serial.print(" - Button: ");
  Serial.print(digitalRead(2));
  Serial.print(" - Light: ");
  Serial.println(analogRead(A0));
  
  delay(500);
}
```

Common Arduino Errors

Error Message What It Means Fix
'xxx' was not declared Typo or missing variable Check spelling
expected ';' before '}' Missing semicolon Add ; at line end
a function-definition is not allowed here Missing closing brace Count your {}
'Serial' does not name a type Forgot to include Add #include <Arduino.h>
programmer is not responding Wrong board selected Check Tools → Board

Chapter 14: Raspberry Pi Debugging

First, Is It On?

```
LED patterns on Pi:
- Red light steady: Power OK
- Green light blinking: SD card activity (good)
- Green light steady or off: SD card problem
- No lights: No power
```

Can't Connect via SSH?

```bash
# Find the Pi on your network
ping raspberrypi.local
# or
nmap -sn 192.168.1.0/24  # Scan your local network

# Check if SSH is enabled
sudo systemctl status ssh

# Check firewall
sudo ufw status
```

Check System Logs

```bash
# See what the Pi is complaining about
journalctl -xe  # Recent system logs
dmesg | tail   # Kernel messages (hardware issues)
tail -f /var/log/syslog  # Live system log
```

Python Debugging

```python
# debug_helper.py
import sys
import traceback

def debug_dump(obj, name="Object"):
    """Print everything about an object"""
    print(f"\n🔍 Debug: {name}")
    print(f"  Type: {type(obj)}")
    print(f"  Value: {obj}")
    print(f"  Dir: {dir(obj)[:10]}...")  # First 10 attributes
    
def safe_execute(func):
    """Run function and catch any errors"""
    try:
        return func()
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return None

# Use it
safe_execute(lambda: risky_function())
```

Chapter 15: Meshtastic Debugging

First Checks

```
□ Device powered? (LED should blink on boot)
□ Antenna connected? (NEVER run without antenna)
□ Phone Bluetooth connected?
□ Same channel as other nodes?
□ Region setting correct? (US 915, EU 868, etc.)
```

Using the CLI

```bash
# Install meshtastic CLI
pip install meshtastic

# Check node info
meshtastic --info

# See what the node hears
meshtastic --nodes

# Monitor traffic
meshtastic --listen

# Reset node
meshtastic --reboot
```

Range Testing

```
1. Put node in "fixed" position
2. Walk away with phone
3. Note where signal drops
4. Check RSSI values:
   -30 to -50: Excellent (right next to it)
   -50 to -70: Good
   -70 to -85: OK
   -85 to -100: Marginal
   Below -100: Probably not reliable
```

Chapter 16: Web App Debugging

Browser Developer Tools (F12)

```
Console Tab:
   - See JavaScript errors in red
   - Type commands to test functions
   - console.log() everything

Network Tab:
   - See what data is being sent/received
   - Check for failed requests (red)
   - See response times

Elements Tab:
   - Inspect HTML structure
   - Test CSS changes live
```

Common Web Issues

```javascript
// Debug helper
function debugElement(selector) {
    const el = document.querySelector(selector);
    console.group(`Debug: ${selector}`);
    console.log('Element:', el);
    console.log('Visible:', !!el && el.offsetParent !== null);
    console.log('Dimensions:', el?.getBoundingClientRect());
    console.log('Styles:', window.getComputedStyle(el));
    console.groupEnd();
    return el;
}

// Use it
debugElement('#my-button');
```

---

📝 PART 6: THE DEBUGGING JOURNAL

Chapter 17: Why Write It Down?

Memory is unreliable. Three months from now, you won't remember that you fixed this exact problem by re-seating the antenna cable.

The Debugging Log Template

```
┌─────────────────────────────────────┐
│         DEBUGGING LOG                │
├─────────────────────────────────────┤
│ Date: _____________ Time: _________ │
│ Device: ___________________________ │
│ Symptom: __________________________ │
│ ___________________________________ │
│                                      │
│ What I checked:                      │
│ □ Power                             │
│ □ Connections                        │
│ □ Recent changes                     │
│ □ _________________________________ │
│                                      │
│ Tests performed:                     │
│ 1. _________________ Result: _______ │
│ 2. _________________ Result: _______ │
│ 3. _________________ Result: _______ │
│                                      │
│ What finally fixed it:               │
│ ___________________________________ │
│ ___________________________________ │
│                                      │
│ Lessons learned:                     │
│ ___________________________________ │
│ ___________________________________ │
└─────────────────────────────────────┘
```

Chapter 18: Building a Community Debugging Culture

The "Fix It Forward" Program

When someone solves a tricky problem, they:

1. Document it in the community log
2. Teach one other person how they fixed it
3. Add it to the "Common Problems" guide

Debugging Parties

Once a month, everyone brings their broken stuff:

· Community potluck + debugging session
· Experienced folks help beginners
· Multiple eyes on tricky problems
· Builds community resilience

---

🆘 PART 7: WHEN TO CALL FOR HELP

Chapter 19: The 30-Minute Rule

If you've been stuck for 30 minutes:

1. Walk away - Get coffee, look outside, clear your head
2. Explain it to someone (even a rubber duck) - Often the solution appears when you explain
3. Check the obvious again - Did you really check that cable?
4. Ask for help - That's what community is for

Chapter 20: Getting Good Help

When asking for help online or from experts:

BAD Request:

"My thing doesn't work. Help plz."

GOOD Request:

```
Device: Raspberry Pi 4, Meshtastic node
Symptom: Node doesn't appear in other nodes' lists
What I've tried:
   1. Checked power (green light on)
   2. Rebooted (same issue)
   3. Different antenna (no change)
   4. Moved closer (still not seen)
Recent changes: Updated to latest firmware yesterday
Screenshot of meshtastic --nodes attached
Any ideas?
```

The more information you provide, the faster someone can help.

---

🎓 APPENDICES

Appendix A: Morse Code Quick Reference

```
A .-    N -.    1 .----
B -...  O ---   2 ..---
C -.-.  P .--.  3 ...--
D -..   Q --.-  4 ....-
E .     R .-.   5 .....
F ..-.  S ...   6 -....
G --.   T -     7 --...
H ....  U ..-   8 ---..
I ..    V ...-  9 ----.
J .---  W .--   0 -----
K -.-   X -..-  . .-.-.-
L .-..  Y -.--  , --..--
M --    Z --..  ? ..--..

SOS: ... --- ...
HELP: .... . .-.. .--.
```

Appendix B: Multimeter Cheat Sheet

```
SETTING    USE                    WHAT GOOD LOOKS LIKE
---------  ---------------------  -------------------------
Continuity Check wires/fuses      Beep = good, silence = bad
20V DC     Check power            5V USB = 4.8-5.2V
200Ω       Check resistors        Reads within 10% of marked value
Diode      Check LEDs             One direction reads, other OL
20mA       Check current (rare)   Don't exceed rating!
```

Appendix C: Common Error Codes

Code Meaning What to Check
E01 No power Battery, connection, switch
E02 Sensor failed Wiring, voltage, replace sensor
E03 Radio timeout Range, antenna, interference
E04 Memory full Restart, reduce data logging
E05 Configuration corrupt Re-upload settings
E06 Boot loop Power supply, SD card, firmware
E07 Overheating Ventilation, load, ambient temp
E08 Water detected Dry out, check seals

Appendix D: The Debugging Flowchart

```
                    ┌─────────────┐
                    │  PROBLEM!   │
                    └──────┬──────┘
                           ▼
              ┌─────────────────────┐
              │  Does it have       │────No────┐
              │  power?             │          │
              └──────────┬──────────┘          ▼
                        Yes              ┌─────────────┐
                         ▼                │ Check power │
              ┌─────────────────────┐     │ source      │
              │  Any lights?        │     └─────────────┘
              └──────────┬──────────┘          │
                        Yes                     │
                         ▼                      │
              ┌─────────────────────┐           │
              │  Check connections  │◀──────────┘
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  Restart device      │
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  Still broken?       │──No──→ 🎉 FIXED!
              └──────────┬──────────┘
                         │ Yes
                         ▼
              ┌─────────────────────┐
              │  Check recent        │
              │  changes             │
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  Google the problem  │
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  Ask for help        │
              │  (with details!)     │
              └─────────────────────┘
```

---

📖 EPILOGUE: The Joy of Fixing Things

There's a special satisfaction that comes from fixing something yourself. It's not just about saving money or avoiding hassle. It's about understanding. When you debug something, you learn how it works. You become the expert. You're no longer at the mercy of the machine.

In rural communities, this matters even more. You can't just call a tech support line or drive to the Apple Store. You have to rely on yourself and your neighbors.

This book is dedicated to every rural community member who's ever looked at a blinking light and thought, "I bet I can figure this out."

You can. And now you know how.

---

"The computer is a stupid machine. It can only do what you tell it. When it doesn't do what you want, it's because you told it wrong. Debugging is just figuring out what you actually said vs. what you meant to say."
