import utime
from dstemp import DSTempSensor

time_temp_last_read = 0


def main():
    global time_temp_last_read

    DSTemp = DSTempSensor(14, 10)

    while True:
        now = utime.ticks_ms()

        time_span = utime.ticks_diff(now, time_temp_last_read)
        if time_span > 1000:
            temps = DSTemp.read_temp()
            print(temps)
            time_temp_last_read = now


if __name__ == '__main__':
    main()
