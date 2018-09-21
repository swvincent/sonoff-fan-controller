import utime
from dstemp import TemperatureSensor

time_temp_last_read = 0

def main():
    global time_temp_last_read

    t = TemperatureSensor(14, 10)

    while True:
        now = utime.ticks_ms()

        last_temp_time_span = utime.ticks_diff(now, time_temp_last_read)

        if last_temp_time_span > 1000:
            temp = t.read_temp()
            print(temp)
            time_temp_last_read = now


if __name__ == '__main__':
    main()
