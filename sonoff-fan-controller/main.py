import utime
from machine import Pin
from dstemp import DSTempSensor


class RunMode:
    OFF = 0
    ON = 1
    AUTO = 2


# Global CONSTANTS
DEBOUNCE_TIME = 20
LONG_PRESS_TIME = 600
FAN_ON_TEMP = 84
FAN_OFF_TEMP = 80

# Global variables
time_temp_last_read = 0
time_last_button_press = 0
run_mode = RunMode.AUTO

# GPIO Setup
button = Pin(0, Pin.IN, Pin.PULL_UP)
led = Pin(13, Pin.OUT)
relay = Pin(12, Pin.OUT)
temp_sensor = DSTempSensor(14, 10)

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
    global time_last_button_press, run_mode

    time_pressed = utime.ticks_ms()

    if button.value() and time_last_button_press > 0:
        # Button released, determine length since press
        hold_length = utime.ticks_diff(time_pressed, time_last_button_press)

        if hold_length > LONG_PRESS_TIME:
            # Long press
            # Short press
            print('Long press ({}ms)'.format(hold_length))
            if run_mode == RunMode.AUTO:
                run_mode = relay.value()
            else:
                run_mode = RunMode.AUTO
        elif hold_length > DEBOUNCE_TIME:
            # Short press
            print('Short press ({}ms)'.format(hold_length))
            if run_mode == RunMode.AUTO:
                run_mode = not relay.value()
            elif run_mode == RunMode.ON:
                run_mode = RunMode.OFF
            elif run_mode == RunMode.OFF:
                run_mode = RunMode.ON

        # Reset last pressed time
        time_last_button_press = 0
    elif not button.value() and time_last_button_press == 0:
        # First button press since last release; record time
        time_last_button_press = time_pressed


def process_mode(temp):
    if run_mode == RunMode.AUTO:
        if temp > FAN_ON_TEMP and not relay.value():
            print('Temp too high, closing relay')
            relay.value(1)
            led.value(0)
        elif temp < FAN_OFF_TEMP and relay.value():
            print('Temp under control, opening relay')
            relay.value(0)
            led.value(1)
    elif run_mode == RunMode.ON and not relay.value():
        print ('On mode, closing relay')
        relay.value(1)
        led.value(0)
    elif run_mode == RunMode.OFF and relay.value():
        print ('Off mode; opening relay')
        relay.value(0)
        led.value(1)


def main():
    global time_temp_last_read

    while True:
        now = utime.ticks_ms()

        # Get temp every second
        time_span = utime.ticks_diff(now, time_temp_last_read)
        if time_span > 1000:
            temps = temp_sensor.read_temp()
            print(run_mode, temps)
            time_temp_last_read = now

        process_mode(temps[1])

# Setup button interrupt. Input goes low on press, high on release
button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=button_pressed)

if __name__ == '__main__':
    main()
