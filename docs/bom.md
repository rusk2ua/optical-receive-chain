# Bill of materials

Release 2026.10.10, LM358 stopgap build. Resistors are 1/4 W, 1% metal film unless noted.

## Front-end board (in the metal box at the lens)

| Qty | Ref / function | Value / part | Notes |
|---|---|---|---|
| 1 | Photodiode | Sharp PD49PI | Built-in visible-cutoff resin |
| 1 | TIA op-amp | LM358 (DIP-8) | Socket it. Swaps for OPA2350 later; see [opa350-upgrade.md](opa350-upgrade.md) |
| 1 | Rf | 1 MΩ | Metal film, low-noise |
| 1 | Cf | 3.3 pF NP0/C0G | 4.7 pF if the stage rings; 2.2 pF for the OPA350 |
| 2 | Vref divider | 10 kΩ | |
| 1 | Vref bypass | 10 µF 16 V electrolytic | + to Vref |
| 1 | PD bias resistor | 1 kΩ | Cathode to +5 V FE |
| 1 | PD bias bypass | 10 µF 16 V electrolytic | + to the 1 kΩ / cathode node |
| 1 | Output pull-down | 10 kΩ | Fixes LM358 crossover distortion |
| 1 | Output series | 100 Ω | Isolates the cable |
| 1 | Op-amp decoupling | 100 nF ceramic | Pin 8 to pin 4 |
| 1 | D1 | 1N5819 Schottky | Reverse-polarity protection |
| 1 | R1 | 100 Ω | Pre-regulator filter |
| 1 | C1 | 100 µF 25 V electrolytic | |
| 1 | C2 | 0.33 µF ceramic or film | 78L05 input |
| 1 | U1 | 78L05 (TO-92) | Or a 7805 |
| 1 | C3 | 0.1 µF ceramic | 78L05 output |
| 1 | R2 | 47 Ω | Post-regulator filter |
| 1 | C4 | 100 µF 16 V electrolytic | |
| 1 | C5 | 100 nF ceramic | |
| 1 | Enclosure | Die-cast aluminum or tinned steel | Hole for the photodiode |
| — | Optional | 850 to 950 nm IR-pass filter, lens hood | For IR-rich ambient light |

## Interconnect and main box

| Qty | Item | Notes |
|---|---|---|
| 1 | Shielded 2-conductor cable | Microphone cable; signal and +13 V, shield = ground |
| 1 | TDA2050 amplifier module | Store-bought, unmodified (50 kΩ series pot, 2.2 µF, 22 kΩ) |
| 1 | F1 | 3 A fast-blow, inline at the battery |
| 1 | S1 | Power switch rated for the module current |
| 1 | Battery | 13 V (4S) LFP, 10 Ah or larger |
| 1 | Speaker or headphone jack | 8 Ω dummy load for setup |
| 2 | Line-out divider | 4.7 kΩ series, 470 Ω shunt (about −21 dB) to the sound card |

## Test jig (optional)

| Qty | Item | Notes |
|---|---|---|
| 1 | 10 MΩ resistor | Current injection into pin 2 |
| 1 | 100 nF film capacitor | DC block in series with the 10 MΩ |
