# Koden starter her. Importerer nødvendige biblioteker
from machine import UART, Pin
import Lcd1_14driver
import utime

# Initialiserer UART (E22-900T22S)
uart_e22 = UART(0,baudrate = 9600,tx = Pin(0),rx = Pin(1))

# Initialiser Pin 3 og Pin 2 som utganger (disse brukes til å bestemme driftsmodus til E22-900T22S)
m0 = Pin(3, Pin.OUT)
m1 = Pin(2, Pin.OUT)

# Setter driftsmodus til E22-900T22S til "Normal" (M0 = 0, M1 = 0)
m0.value(0)
m1.value(0)

# Initialiserer LCD-skjermen via LCD-driveren
LCD = Lcd1_14driver.Lcd1_14()

# Viser en enkel oppstartsskjerm mens vi venter på signal
LCD.fill(LCD.white) 
LCD.lcd_show()
LCD.text("CanSat Kit 2023",60,45,LCD.blue)
LCD.text("Waiting for signal....",35,75,LCD.red)
LCD.lcd_show()
utime.sleep(1)

# Starter en løkke som vil kjøre for alltid
while True:
    # Registrer starttiden til løkken
    start_time = utime.ticks_ms()

    # Leser data fra E22-900T22S
    dataRead = uart_e22.readline() 

    # Sjekker om det ble mottatt noe data (sjekker bufferet til E22-900T22S)
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
            
            # Skriver mottatt streng til LCD-skjermen
            LCD.fill(LCD.white) 
            LCD.text("Received DATA: ",10,10,LCD.blue)
            LCD.text("Callsign:      ",10,25,LCD.blue)
            LCD.text("Framecounter:  ",10,40,LCD.blue)
            LCD.text("Mills:         ",10,55,LCD.blue)
            LCD.text("Pressure:      ",10,70,LCD.blue)
            LCD.text("Temperature:   ",10,85,LCD.blue)
            
            LCD.text(dataRead_list[0],120,25,LCD.red)
            LCD.text(dataRead_list[1],120,40,LCD.red)
            LCD.text(dataRead_list[2],120,55,LCD.red)
            LCD.text(str("{0} hPa").format(dataRead_list[3]),120,70,LCD.red)
            LCD.text(str("{0} C").format(dataRead_list[4]),120,85,LCD.red)            
            LCD.lcd_show()

    # Passer på at løkken tar nøyaktig 1 sekund, som samsvarer med telemetri-del
    loop_time = utime.ticks_diff(utime.ticks_ms(), start_time)
    if loop_time < 1000:
        utime.sleep_ms(1000 - loop_time)

# Koden avsluttes her