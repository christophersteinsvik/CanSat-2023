# Koden starter her. Importerer nødvendige biblioteker
from machine import Pin, I2C, UART, SPI
from bmp280 import *
import utime
import os
import sdcard

# Initialiserer I2C (BMP280), UART (E22-900T22D), og SPI (microSD-kortleser)
uart_e22 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
i2c_bmp = I2C(1, scl=Pin(7), sda=Pin(6), freq=200000)
spi_sdcard = SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(8))

# Initialiserer Pin 6 og Pin 7 som utganger (disse brukes til å bestemme driftsmodus til E22-900T22D)
m0 = Pin(2, Pin.OUT)
m1 = Pin(3, Pin.OUT)

# Setter driftsmodus til E22-900T22D til "Normal" (M0 = 0, M1 = 0)
m0.value(0)
m1.value(0)

# Initialiserer BMP280 og setter "use_case" til "INDOOR". Dette er gir høyest oppløsning på sensordata
bmp = BMP280(i2c_bmp)
bmp.use_case(BMP280_CASE_INDOOR)

# Oppretter variabel for frame counter
frame_counter = 0

# Starter en løkke som vil kjøre for alltid
while True:
    # Registrer starttiden til løkken
    start_time = utime.ticks_ms()

    # Leser sensordata
    pressure = bmp.pressure / 100  # Konverter til hPa
    temperature = bmp.temperature
    frame_counter = frame_counter + 1
    mills = utime.ticks_ms()

    # Lager datastreng. Viktig å avslutte med "\n" da mottaks-delen bruker dette for å lese neste linje
    data = "CanSat01,{:05d},{:08d},{:00.02f},{:00.02f}\n".format(frame_counter, mills, pressure, temperature)

    # Skriver ut datastreng som skal sendes til konsoll
    print(data)
    
    # Skriver ut trykk- og temperaturdata på en stukturert måte til konsoll
    print(f"Pressure (hPa):  {pressure:00.02f}")
    print(f"Temperature (C): {temperature:00.02f}")
    print("- - - - - - - - - - - - - - - - - - -")

    # Skriver data til SD-kort. Gir feilmelding til konsoll hvis den ikke finner SD-kort
    try:
        sd = sdcard.SDCard(spi_sdcard, Pin(9))
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/fc")
        with open("/fc/Cansat01.txt", "a") as f:
            f.write(data)
        os.umount("/fc")
    except OSError:
        print('Kunne ikke skrive til SD-kortet. Vennligst sjekk kortet.')

    # Skriver data til E22-900T22D, som sender til mottaks-del
    uart_e22.write(data)

    # Passer på at løkken tar nøyaktig 1 sekund, som gir en oppdateringsfrekvens på 1 Hz
    loop_time = utime.ticks_diff(utime.ticks_ms(), start_time)
    if loop_time < 1000:
        utime.sleep_ms(1000 - loop_time)

# Koden avsluttes her