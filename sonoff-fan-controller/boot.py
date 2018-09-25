# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)

# import webrepl
# webrepl.start()

import gc
gc.collect()

# Disable Access point
import network
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
