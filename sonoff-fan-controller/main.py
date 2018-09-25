"""
sonoff-fan-controller

Control a fan using a SonOff Basic WiFi Smart Switch. Provides
temperature-based automatic control and manual override. LED
indicates status. Should be adaptable to other ESP8266-based
devices and boards.

www.swvincent.com

https://github.com/swvincent/sonoff-fan-controller

Copyright (c) 2018 Scott W. Vincent

Shared under an MIT License
"""
import utime, math
from machine import Pin, PWM
from dstemp import DSTempSensor


# RunMode "Enum"
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
temps = [0, 0]
time_temp_last_read = 0
time_last_button_press = 0
time_last_pwm = 0
pwm_counter = 0
run_mode = RunMode.AUTO

# GPIO Setup
button = Pin(0, Pin.IN, Pin.PULL_UP)
led = Pin(13, Pin.OUT)
pwm = PWM(led)
relay = Pin(12, Pin.OUT)
temp_sensor = DSTempSensor(14, 10)

# Relay/LED off at start. led lights w/ output low
led.on()
relay.off()


def breathe_led():
    """
    Pulse LED for 'breathing' effect
    Based on Micropython docs PWM tutorial
    """
    global time_last_pwm, pwm_counter

    now = utime.ticks_ms()

    # Update LED every 50ms
    time_span = utime.ticks_diff(now, time_last_pwm)

    if time_span > 50:
        pwm_counter += 1
        if pwm_counter > 100:
            pwm_counter = 1
        pwm.duty(int(math.sin(pwm_counter / 50 * math.pi) * 500 + 500))
        time_last_pwm = now


def button_pressed(p):
    """Determine button press type and action to take"""
    global time_last_button_press, run_mode

    time_pressed = utime.ticks_ms()

    if button.value() and time_last_button_press > 0:
        # Button released, determine length since press
        hold_length = utime.ticks_diff(time_pressed, time_last_button_press)

        if hold_length > LONG_PRESS_TIME:
            # Long press
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


def update_temps():
    """Get temperature every second"""
    global temps, time_temp_last_read

    now = utime.ticks_ms()

    # Get temp every second
    time_span = utime.ticks_diff(now, time_temp_last_read)
    if time_span > 1000:
        temps = temp_sensor.read_temp()
        print(run_mode, temps)
        time_temp_last_read = now


def toggle_relay():
    """Open/close relay based on mode and temperature"""
    global run_mode, temps
    if run_mode == RunMode.AUTO:
        if temps[1] > FAN_ON_TEMP and not relay.value():
            print('Temp too high, closing relay')
            relay.value(1)
        elif temps[1] < FAN_OFF_TEMP and relay.value():
            print('Temp under control, opening relay')
            relay.value(0)
    elif run_mode == RunMode.ON and not relay.value():
        print ('On mode, closing relay')
        relay.value(1)
    elif run_mode == RunMode.OFF and relay.value():
        print ('Off mode; opening relay')
        relay.value(0)


def toggle_led():
    """Toggle LED to indicate mode and status"""
    global run_mode

    if run_mode == RunMode.AUTO:
        if relay.value():
            # Fan running in auto; breathing effect
            breathe_led()
        else:
            # Fan off in auto; pulse every 4 sec.
            pwm.deinit()
            led_time = utime.ticks_ms() % 4000
            led.value(led_time > 10)
    elif run_mode == RunMode.ON and led.value():
        # Fan forced on, LED is on
        pwm.deinit()
        led.value(0)
    elif run_mode == RunMode.OFF and not led.value():
        # Fan forced off, LED is off
        pwm.deinit()
        led.value(1)


def main():
    """Main program loop"""
    while True:
        update_temps()
        toggle_relay()
        toggle_led()


# Setup button interrupt. Input goes low on press, high on release
button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=button_pressed)


if __name__ == '__main__':
    main()
