import utime
from machine import Pin
from dstemp import DSTempSensor

# Global CONSTANTS/variables
DEBOUNCE_TIME = 20
LONG_PRESS_TIME = 600
time_temp_last_read = 0
time_last_button_press = 0

# GPIO Setup
button = Pin(0, Pin.IN, Pin.PULL_UP)
led = Pin(13, Pin.OUT)
relay = Pin(12, Pin.OUT)
DSTemp = DSTempSensor(14, 10)

# Everything off at start. led is "normally closed"
led.on()
relay.off()


def change_relay_state():
    """
    Toggle value of relay and LED. Note
    that led is NC so it's opposite.
    """
    relay.value(led.value())
    led.value(not led.value())


def button_pressed(p):
    global time_last_button_press

    time_pressed = utime.ticks_ms()

    if button.value() and time_last_button_press > 0:
        # Button released, determine length since press
        hold_length = utime.ticks_diff(time_pressed, time_last_button_press)

        if hold_length > LONG_PRESS_TIME:
            # Long press
            print(utime.ticks_ms(),
                  "Long press doesn't do anything yet! ({}ms)"
                  .format(hold_length))
        elif hold_length > DEBOUNCE_TIME:
            # Short press
            change_relay_state()

        # Reset last pressed time
        time_last_button_press = 0
    elif not button.value() and time_last_button_press == 0:
        # First button press since last release; record time
        time_last_button_press = time_pressed


def main():
    global time_temp_last_read

    while True:
        now = utime.ticks_ms()

        time_span = utime.ticks_diff(now, time_temp_last_read)
        if time_span > 1000:
            temps = DSTemp.read_temp()
            print(temps)
            time_temp_last_read = now


# Setup button interrupt. Input goes low on press, high on release
button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=button_pressed)

if __name__ == '__main__':
    main()
