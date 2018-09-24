"""
dstemp.py

Read temperature from a single DS18x20 sensor connected to to
an ESP8266 board using Micropython.

Scott W. Vincent
https://gist.github.com/swvincent/8bdf3da658350f68b1109611f2242ff4

Forked from Christopher Hiller "boneskull"
https://gist.github.com/boneskull/1f5ae354815c6db5b1cb05ad2cb6232b

My version is similar to Hiller's, except that I don't delay
in the temperature reading code, instead I rely on the delay of
the main program's loop. Also I added a main.py function so
I could easily test my code in a single file. Most significantly
I average over the last n values to keep it from fluctuating wildly.
Finally, I return both Celsius and Fahrenheit rather than just one.

I also did away with the additional files that provided MQTT, etc.
since I wasn't interested in that part of it.
"""
import utime
from ds18x20 import DS18X20
from machine import Pin
from onewire import OneWire


class DSTempSensor:
    """
    Represents a Temperature sensor
    """

    def __init__(self, pin, samples):
        """
        Finds address of single DS18B20 on bus specified by `pin`
        :param pin: 1-Wire bus pin
        :type pin: int
        """
        self.ds = DS18X20(OneWire(Pin(pin)))
        addrs = self.ds.scan()
        if not addrs:
            raise Exception('no DS18B20 found at bus on pin %d' % pin)
        # save what should be the only address found
        self.addr = addrs.pop()

        # create samples collection and related variables
        self.samples = samples
        self.temps = [0] * samples
        self.temps_pos = 0

        # Force initial convert_temp and delay to avoid bad values
        self.ds.convert_temp()
        utime.sleep_ms(750)

    def read_temp(self):
        """
        Reads temperature from a single DS18X20. It's assumed this will
        be called multiple times with a delay of at least 750ms between
        calls, so read and convert are done backwards here so delay can
        be done in main loop of program running on the ESP8266. This
        way the temp sensor reading isn't blocking the program. The
        first reading may be affected so this isn't recommended for
        taking a single reading or intermittent readings.
        :return: Temperature in C and F
        :rtype: [float, float]
        """

        self.temps[self.temps_pos] = self.ds.read_temp(self.addr)
        self.ds.convert_temp()

        # Set next position for averages. I'm not using deque because
        # the ucollections version isn't iterable in my testing with
        # uPython 1.9.4. So I can sum the values.
        self.temps_pos += 1
        if self.temps_pos >= self.samples:
            self.temps_pos = 0

        avg_temp = sum(self.temps) / len(self.temps)

        return [avg_temp, self.c_to_f(avg_temp)]

    @staticmethod
    def c_to_f(c):
        """
        Converts Celsius to Fahrenheit
        :param c: Temperature in Celsius
        :type c: float
        :return: Temperature in Fahrenheit
        :rtype: float
        """
        return (c * 1.8) + 32


def main():
    # Get temp once per second indefinitely as demo.
    pin_num = input('Enter the pin#:')
    t = DSTempSensor(int(pin_num), 10)
    while True:
        print(t.read_temp())
        utime.sleep_ms(1000)  # Must be >= 750


if __name__ == '__main__':
    main()
