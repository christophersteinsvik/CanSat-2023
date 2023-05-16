# Koden starter her. Importerer nødvendige biblioteker
import utime
from machine import Pin, UART

# Funksjon for å presentere mottatt byte-streng med registerdata fra radioen på en mer leselig måte
def print_hex(data):
    print(["0x{:02X}".format(b) for b in data])
    
# Funksjon for å presentere radioens innstillinger (via registerverdier) som en tabell
def print_hex_list(data):
    descriptions = ['Command                                                 ',
                    'Starting address                                        ',
                    'Length                                                  ',
                    '\nModule address (higher bits)               00H      0x00',
                    'Module address (lower bits)                01H      0x00',
                    'Network address                            02H      0x00',
                    'Serial port rate and air data rate         03H      0x62',
                    'Sub packet setting and Transmitting power  04H      0x00', 
                    'Channel control                            05H      0x12',
                    'RSSI, FPT, Repeater, LBT and WOR           06H      0x03', 
                    'Key high byte (write only)                 07H      0x00',
                    'Key low byte (write only)                  08H      0x00']
    hex_data = ["0x{:02X}".format(b) for b in data]
    for desc, val in zip(descriptions, hex_data):
        print(f'{desc}      {val}')

# Funksjon for å ta inn brukerens valg når man konfigurerer radioen
def get_user_choice(prompt, choices):
    while True:
        print(prompt)
        for i, choice in enumerate(choices, 1):
            print(f"   {i}:   {choice}")
        try:
            choice = int(input(f"\nSkriv inn ditt valg (tall mellom 1 og {len(choices)}): ")) - 1
            if 0 <= choice < len(choices):
                return choice
            else:
                print("Ugyldig valg. Vennligst prøv igjen.")
        except ValueError:
            print("Ugyldig valg. Vennligst skriv et tall.")

# Funksjon for å konfigurere radio etter eget ønske
def configure_radio():
    # Starter med fabrikkinnstillinger
    configure_command = [0xC0, 0x00, 0x09, 0x00, 0x00, 0x00, 0x62, 0x00, 0x12, 0x03, 0x00, 0x00]

    # Sett radioens Adresse
    while True:
        try:
            address = int(input("\n\nVelg radioens adresse ved å skrive inn et tall mellom 0-65535. \nHusk at både telemetri-del og mottaks-del må ha samme adresse. \n\nDitt valg (fabrikkinnstilling er 0): "))
            if 0 <= address <= 65535:
                configure_command[3] = (address >> 8) & 0xFF  # Higher bits
                configure_command[4] = address & 0xFF  # Lower bits
                break
            else:
                print("Inngangen er utenfor gyldig område (0-65535). Prøv igjen.")
        except ValueError:
            print("Ugyldig inngang. Skriv inn et tall.")

    # Sett radioens Nettverksadresse
    while True:
        try:
            network_address = int(input("\n\nVelg radeioens Nettverksadresse. \nHusk at både telemetri-del og mottaks-del må være på samme nettverk. \n\nDitt valg (tall mellom 0-255, fabrikkinnstilling er 0): "))
            if 0 <= network_address <= 255:
                configure_command[5] = network_address & 0xFF
                break
            else:
                print("\nInngangen er utenfor gyldig område (0-255). Prøv igjen.")
        except ValueError:
            print("\nUgyldig inngang. Skriv inn et tall.")

    # Sett UART serial port rate (baud rate)
    uart_rate_choices = ["1200 baud", "2400 baud", "4800 baud", "9600 baud (fabrikkinnstilling)", "19200 baud", "38400 baud", "57600 baud", "115200 baud"]
    uart_rate_choice = get_user_choice("\n\nVelg UART serial port rate (baud rate til UART-protokollen).", uart_rate_choices)
    configure_command[6] &= 0x1F  # Clear bit 7, 6 and 5
    configure_command[6] |= (uart_rate_choice << 5)  # Sett bit 7, 6 and 5

    # Sett Serial Parity Bit
    serial_parity_choices = ["8N1 (fabrikkinnstilling)", "8O1", "8E1"]
    serial_parity_choice = get_user_choice("\n\nVelg Serial Parity. Bestemmer hvilken type feilsjekking som blir gjennomført på dataen", serial_parity_choices)
    configure_command[6] &= 0xE7  # Clear bit 4 and 3
    configure_command[6] |= (serial_parity_choice << 3)  # Sett bit 4 and 3

    # Velg Air Data Rate
    air_data_rate_choices = ["0.3k", "1.2k", "2.4k (fabrikkinnstilling)", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"]
    air_data_rate_choice = get_user_choice("\n\nVelg Air Data Rate (i antall bit per sekund). Bestemmer hvor fort radioen sender data. Høyere verdi gir lavere rekkevidde.\n", air_data_rate_choices)
    configure_command[6] &= 0xF8  # Clear lower 3 bits
    configure_command[6] |= air_data_rate_choice  # Sett lower 3 bits

    # Sett Sub Packet størrelse
    sub_packet_choices = ["240 bytes (fabrikkinnstilling)", "128 bytes", "64 bytes", "32 bytes"]
    sub_packet_choice = get_user_choice("\n\nVelg Sub Packet-størrelse. Bestemmer hvor mange bytes som sendes i hver pakke.", sub_packet_choices)
    configure_command[7] &= 0x3F  # Clear bit 7 and 6
    configure_command[7] |= (sub_packet_choice << 6)  # Sett bit 7 and 6

    # Sett RSSI Ambient Noise
    rssi_choices = ["Disable (fabrikkinnstilling)", "Enable"]
    rssi_choice = get_user_choice("\n\nSkru av/på RSSI Ambient Noise. RSSI = Received Signal Strength Indicator). \nDette er et tall som sier noe om støy på valgt kanal. \nFor å kunne se denne verdien, kreves det ytterligere oppsett. \nSe i databladet til E22 for mer informasjon. \n", rssi_choices)
    configure_command[7] &= 0xDF  # Clear bit 5
    configure_command[7] |= (rssi_choice << 5)  # Sett bit 5

    # Sett radioens sendestyrke
    power_choices = ["22dBm (fabrikkinnstilling)", "17dBm", "13dBm (Høyeste lovlige sendestyrke i Norge)", "10dBm"]
    power_choice = get_user_choice("\n\nVelg sendestyrke. Høyere verdi gir bedre rekkevidde. \n", power_choices)
    configure_command[7] &= 0xFC  # Clear lower 2 bits
    configure_command[7] |= power_choice  # Sett lower 2 bits

    # Sett kanal (0-80)
    while True:
        try:
            channel = int(input("\n\nSett radioens kanal. Det er totalt 81 kanaler tilgjengelig (0-80) \n\nFrekvens = 850,125 + Kanal [MHz]. \n\nI Norge/EU skal kun Kanal 15-18 brukes (tilsvarer 865,125-868,125MHz). \nFabrikkinnstilling = Kanal 18 (tilsvarer 868,125MHz). \n\nVelg radioens kanal: (tall mellom 0-80): "))
            if 0 <= channel <= 80:
                configure_command[8] = channel
                break
            else:
                print("Inngangen er utenfor gyldig område (0-80). Prøv igjen.")
        except ValueError:
            print("Ugyldig inngang. Skriv inn et tall.")

    # Set Enable RSSI
    rssi_choices = ["Disable (fabrikkinnstilling)", "Enable"]
    enable_rssi = get_user_choice("\n\nSkru av eller på RSSI (Received Signal Strength Indicator). \n\nVed å skru på denne innstillingen, vil det følge en RSSI-verdi etter hver mottatte melding. \nSe i databladet til E22-900T22 for mer informasjon om RSSI.\n", rssi_choices)
    configure_command[9] &= 0x7F  # Clear bit 7
    configure_command[9] |= (enable_rssi << 7)  # Sett bit 7

    # Set Fixed point transmission
    fixed_transmission_choices = ["Transparent Transmission Mode (fabrikkinnstilling)", "Fixed Point Transmission Mode"]
    fixed_point_transmission = get_user_choice("\n\nSett Fixed point transmission. \nSe i databladet til E22-900T22 for mer informasjon om Fixed Point Transmission.\n", fixed_transmission_choices)
    configure_command[9] &= 0xBF  # Clear bit 6
    configure_command[9] |= (fixed_point_transmission << 6)  # Sett bit 6

    # Set Enable Reply
    reply_choices = ["Disable Repeater function (fabrikkinnstilling)", "Enable Repeater Function"]
    enable_reply = get_user_choice("\n\nSett Skru av eller på Repeater-mode. \nDette er en innstilling som brukes i sammenheng med Fixed Point Transmission. \nSe i databladet til E22-900T22 for mer informasjon om Repeater-funksjonalitet. \n", reply_choices)
    configure_command[9] &= 0xDF  # Clear bit 5
    configure_command[9] |= (enable_reply << 5)  # Sett bit 5

    monitor_choices = ["AV (fabrikkinnstilling)", "PÅ (Skal være påskrudd i Norge/EU)"]
    monitor_choice = get_user_choice("\n\nVelg om Monitor Before Transmission skal være på eller av. \nDette er en funksjon som gjør at radioen lytter etter andre som sender på \nsamme kanal før den sender selv. Skal være påslått i Norge/EU. \n", monitor_choices)
    configure_command[9] &= 0xEF  # Clear bit 4
    configure_command[9] |= (monitor_choice << 4)  # Sett bit 4

    # Set Wake on Radio
    wor_choices = ["WOR Receiver (fabrikkinnstilling)", "WOR Transmitter"]
    wake_on_radio = get_user_choice("\n\nSett Wake on Radio-innstilling. Brukes i sammenheng med Wake on Radio, \nhvor radioen kan går i dvalemodus frem til den mottar en melding over radio. \nVed å velge WOR Transmitter vil radoen sende en 'wake up code' før den sender data. \nDenne innstillingen er kun relevant for 'WOR'-modus.\nI 'Normal'-modus kan den stå på fabrikkinnstilling. \n", wor_choices)
    configure_command[9] &= 0xF7  # Clear bit 3
    configure_command[9] |= (wake_on_radio << 3)  # Sett bit 3

    wor_cycle_choices = ["500ms", "1000ms", "1500ms", "2000ms (fabrikkinnstilling)", "2500ms", "3000ms", "3500ms", "4000ms"]
    wor_cycle_choice = get_user_choice("\n\nVelg WOR Cycle. Bestemmer WOR monitoring-intervall. \nViktig at både sender og mottakker har samme innstilling \nhvis WOR-modus brukes.\nDenne innstillingen er kun relevant for 'WOR'-modus.\nI 'Normal'-modus kan den stå på fabrikkinnstilling. \n", wor_cycle_choices)
    configure_command[9] &= 0xF8  # Clear bit 2, 1 and 0
    configure_command[9] |= wor_cycle_choice  # Sett bit 2, 1 and 0
    
    # Set Key high byte and key low byte (krypteringsnøkkel)
    while True:
        try:
            key = int(input("\n\nSett krypteringsnøkkel. \nDette tallet vil bli brukt internt i modulen til å kryptere meldingen som sendes. \nDette registeret er 'write-only', og vil alltid returnere 0x00 når det leses. \nFabrikkinnstilling er '0', som vil si at kryptering av avslått. \nSender-del og mottaker-del må ha samme krypteringsnøkkel. \n\nSkriv inn ønsket krypteringsnøkkel (tall mellom 0-65535): "))
            if 0 <= key <= 65535:
                configure_command[10] = (key >> 8) & 0xFF  # Higher bits
                configure_command[11] = key & 0xFF  # Lower bits
                break
            else:
                print("Inngangen er utenfor gyldig område (0-65535). Prøv igjen.")
        except ValueError:
            print("Ugyldig inngang. Skriv inn et tall.")


    return configure_command

# Hovedløkke
while True:
    print("\n\nVelkommen til konfigurasjons-verktøyet til CanSat-kit 2023!")
    print("Dette verktøyet vil hjelpe deg å konfigurere radioen til CanSat-settet.")
    print("Dette verktøyet kan brukes på Telemetri-del, Mottaks-del, og Pico LoRa Expansion.")
    print("\nRadioens innstillinger lagres i ni 8-bit registere. Dette verktøyet vil hjelpe deg å endre disse.")
    print("Se i databladet til E22-900T22 for en full gjennomgang av alle innstillinger.")
    print("\nFabrikkinnstillingene vil i de aller fleste tilfeller være gode nok, men sendestyrken er over lovlig grense i Norge.")
    print("Derfor anbefales det å bruke 'Fabrikkinnstillinger med 13dB sendestyrke', som er innenfor lovlig grense i Norge.") 
    print("\nFor å konfigurere radioen, følger du bare stegene under:")
    print("\n\nVelg hvilken del av CanSat-settet du vil konfigurere:")
    print("\n   1:   Mottaks-del")
    print("   2:   Telemetri-del")
    print("   3:   Pico LoRa Expansion")
    print("   4:   Avslutt")

    choice = input("\nSkriv inn ditt valg (1, 2, 3 eller 4): ")

    if choice == '1':
        # Sett pinne og UART-bus for Mottaks-del
        uart_e22 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
        m0 = Pin(6, Pin.OUT)
        m1 = Pin(7, Pin.OUT)
    elif choice == '2':
        # Sett pinne og UART-bus for Telemetri-del
        uart_e22 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
        m0 = Pin(2, Pin.OUT)
        m1 = Pin(3, Pin.OUT)
    elif choice == '3':
        # Sett pinne og UART-bus for Pico LoRa Expansion
        uart_e22 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1)) # Erstatt med riktig verdi
        m0 = Pin(3, Pin.OUT) # Erstatt med riktig verdi
        m1 = Pin(2, Pin.OUT) # Erstatt med riktig verdi
    elif choice == '4':
        print("Avslutter programmet.")
        break
    else:
        print("\nUgyldig valg. Vennligst skriv 1, 2, 3 eller 4.")
        continue

    # Setter driftsmodus til E22-900T22 til "Configuration Mode" (M0 = 0, M1 = 1)
    m0.value(0)
    m1.value(1)

    while True:  # Løkke for å velge handling

        print("\n\nVelg handling: ")
        print("\n   1:   Les radioens innstillinger")
        print("   2:   Konfigurer radio for bruk i Norge/EU (ANBEFALT)")
        print("\n   3:   Sett radio tilbake til Fabrikkinnstillinger")
        print("   4:   Velg egne innstillinger (velg denne om du vil endre blant annet kanal)")

        action_choice = input("\nSkriv inn ditt valg (1, 2, 3 eller 4): ")

        if action_choice == '1':
            # Bytestreng for å lese hele registeret. 0xC1 = Read Register, 0x00 = Startadresse, 0x09 = Lengde
            print("\n\nDu har valgt å lese hele registeret.")
            send_command = [0xC1, 0x00, 0x09]
            break
        elif action_choice == '2':
            # Bytestreng for å endre register for bruk i Norge/EU (ANBEFALT)
            print("\n\nDu har valgt å konfigurere radioen for bruk i Norge/EU.")
            send_command = [0xC0, 0x00, 0x09, 0x00, 0x00, 0x00, 0x62, 0x02, 0x12, 0x13, 0x00, 0x00]            
            break
        elif action_choice == '3':
            # Bytestreng for å endre register tilbake til Factory Default
            print("\n\nDu har valgt å sette radioen tilbake til Fabrikkinnstillinger.")
            send_command = [0xC0, 0x00, 0x09, 0x00, 0x00, 0x00, 0x62, 0x00, 0x12, 0x03, 0x00, 0x00]

            break
        elif action_choice == '4':
            # Bytestreng for egne innstillinger. Starter med Factory Default som utgangspunkt
            send_command = configure_radio()
            break
        else:
            print("\nUgyldig valg. Vennligst skriv 1, 2, 3 eller 4.")
            continue

    # Konverterer vektoren vi lager til en bytestreng som kan forstås av E22-900T22D
    send_command_bytestring = bytes(send_command)

    # Sender bytestreng til E22-900T22D, og venter i 100 ms på svar
    uart_e22.write(send_command_bytestring)
    utime.sleep(0.400)

    # Les respons fra E22-900T22D
    response = uart_e22.read()

    # Sjekker om vi mottar data fra E22-900T22D
    if response is not None:
        if response == b'\x00':
            print("\n\nRåstreng mottatt fra E22-900T22D:")
            print(response)
            # Denne feilen kan oppstå hvis man velger feil enhet å konfigurere (f.eks. velger Pico LoRa Expansion når man har koblet til telemetri-delen)
            print("\n\nFeilmelding: Du har kanskje valgt feil enhet i hovedmenyen. Prøv å koble til Picoen på nytt og kjøre koden igjen")
            
        elif response == b'\xff\xff\xff':
            print("\n\nRåstreng mottatt fra E22-900T22D:")
            print(response)
            print("\n\nFeilmelding: Du har sendt en ugyldig kommando til radioen. Prøv et annet konfigurasjonsvalg")
            # Denne feilen oppstår hvis radioen mottar en ugyldig kommando
        else:
            # Skriver mottatt råstreng fra E22-900T22D. Fjern pund-tegnet for å vise råstrengen. Brukes i debug-sammenheng.
            # print("\n\nRåstreng mottatt fra E22-900T22D:")
            # print(response)

            # Skriver råstreng på en mer lettlest måte. Fjern pund-tegnet for å vise råstrengen. Brukes i debug-sammenheng.
            # print("\nLettlest-råstreng fra E22-900T22D:")
            # print_hex(response)

            # Lister opp registeroversikt med beskrivelser
            print("\nOperasjonen var vellykket. Tabellen under viser en oversikt over radioens innstillinger:")
            print("------------------------------------------------------------------------")
            print("                                           Adresse  Standard  Satt verdi")
            print_hex_list(response)
            print("------------------------------------------------------------------------")
            
    else:
        print("\n\nFeilmelding: Ingen respons mottatt fra E22-900T22. Prøv å koble til Picoen på nytt og kjøre koden igjen")
        # Feilmelding hvis radio returnerer "None"

    # Spør brukeren om de vil kjøre programmet på nytt eller avslutte
    print("\nVil du kjøre programmet på nytt?")
    print("\n   1:   Kjør programmet på nytt")
    print("   2:   Avslutt programmet")
    repeat_choice = input("\nSkriv inn ditt valg (1 eller 2): ")
    if repeat_choice == '1':
        continue
    elif repeat_choice == '2':
        print("Avslutter programmet.")
        break
    else:
        print("Ugyldig valg. Avslutter programmet.")
        break