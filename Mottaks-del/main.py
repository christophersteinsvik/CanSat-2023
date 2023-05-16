# Koden starter her. Importerer nødvendige biblioteker
from machine import UART, Pin
import utime

# Initialiserer UART (E22-900T22D)
uart_e22 = UART(1,baudrate = 9600,tx = Pin(8),rx = Pin(9))

# Initialiser Pin 6 og Pin 7 som utganger (disse brukes til å bestemme driftsmodus til E22-900T22D)
m0 = Pin(6, Pin.OUT)
m1 = Pin(7, Pin.OUT)

# Setter driftsmodus til E22-900T22D til "Normal" (M0 = 0, M1 = 0)
m0.value(0)
m1.value(0)

# Starter en løkke som vil kjøre for alltid
while True:
    # Registrer starttiden til løkken
    start_time = utime.ticks_ms()

    # Leser data fra E22-900T22D
    dataRead = uart_e22.readline() 

    # Sjekker om det ble mottatt noe data (sjekker bufferet til E22-900T22D)
    if dataRead is not None:
        # Dekoder dataRead fra bytes til en streng (ASCII) og skriver ut til konsoll
        dataRead_string = dataRead.decode("ASCII")
        print(dataRead_string)

        # Splitter strengen inn i en liste basert på komma
        dataRead_list = dataRead_string.split(",")

        # Sjekker om listen har 5 elementer (viktig i tilfelle man mottar kun en del av en datastreng)
        if len(dataRead_list) == 5:
            # Denne linjen fjerner "\n" fra mottatt datastreng (hver telemetristreng avsluttes med "\n")
            dataRead_list[4] = dataRead_list[4].rstrip()
            
            # Skriver ut mottatt streng på en strukturert måte til konsoll
            print(f"Callsign: {dataRead_list[0]}")
            print(f"Frame: {dataRead_list[1]}")
            print(f"Mills: {dataRead_list[2]}")
            print(f"Pressure (hPa): {dataRead_list[3]}")
            print(f"Temperature (Celcius): {dataRead_list[4]}")
            print("-----")

    # Passer på at løkken tar nøyaktig 1 sekund, som samsvarer med telemetri-del
    loop_time = utime.ticks_diff(utime.ticks_ms(), start_time)
    if loop_time < 1000:
        utime.sleep_ms(1000 - loop_time)

# Koden avsluttes her

