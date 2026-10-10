# OPA350 upgrade

The LM358 is a stopgap. The OPA350, a CMOS rail-to-rail op-amp, is the intended final TIA. The power section is already built for it.

## What the OPA350 brings

These are TI's typical figures; check the datasheet for your parts.

| Spec | LM358 (approx.) | OPA350 |
|---|---|---|
| Supply | 3 to 32 V | **2.7 to 5.5 V** |
| Gain-bandwidth | about 1 MHz | about 38 MHz |
| Slew rate | about 0.3 V/µs | about 22 V/µs |
| Input bias current | about 45 nA | 10 pA max |
| Voltage noise | about 40 nV/√Hz | about 5 to 7 nV/√Hz |
| Output swing | about GND to Vcc − 1.5 V | rail to rail |

At Rf = 1 MΩ, the important change is **current noise**. The OPA350's CMOS input noise current is in the femtoamp range, so the 1 MΩ resistor's own thermal noise becomes the floor. `tia_calc.py` puts input-referred noise from 300 Hz to 20 kHz at **about 18 pA RMS, versus about 37 pA for the LM358**, roughly 6 dB better.

## ⚠️ Supply limit

**Never connect the OPA350 to 13 V.** Its absolute maximum is about 5.5 V (check the datasheet), and the 13 V battery will destroy it instantly. It goes on the **+5 V FE** rail from the 78L05, exactly where the LM358 sits now.

## Pinout

- **OPA350 (single):** uses the standard single op-amp pinout: pin 2 −IN, pin 3 +IN, pin 4 V−, pin 6 OUT, pin 7 V+. Confirm it against the datasheet. That's **not** the same as the dual LM358 (pin 1 OUT, pin 8 V+), so either rewire the socket or use a small adapter.
- **OPA2350 (dual):** shares the **LM358 / NE5532 dual pinout**. It drops into the same socket. Treat its unused half the same way (pin 7 to pin 6, pin 5 to Vref).

The OPA350 and OPA2350 come in SOIC-8 and VSSOP-8 packages, so plan on an SOIC-to-DIP adapter board if you're building on perfboard.

## Component changes

| Part | LM358 build | OPA350 build | Why |
|---|---|---|---|
| U (op-amp) | LM358 | OPA350 or OPA2350 | |
| Cf | 3.3 pF | **2.2 pF** NP0 | Minimum stable Cf is about 0.4 pF with 38 MHz GBW, but keep a real capacitor to cap the noise bandwidth |
| Rf | 1 MΩ | 1 MΩ | Same gain; the lower noise is the win |
| 10 k pull-down | fitted | optional | The OPA350 has no crossover issue. Leaving it in is harmless. |
| Everything else | — | unchanged | |

Modeled response with the OPA350 and 2.2 pF: −0.17 dB at 15 kHz, −3 dB near 75 kHz, no peaking. With 3.3 pF: −0.4 dB at 15 kHz and a −3 dB point near 49 kHz. Either works. Smaller Cf just lets more high-frequency noise reach the TDA2050 and sound card.

```bash
python3 tools/tia_calc.py --opamp opa350 --cf 2.2e-12
```

## Headroom

The output idles at Vref and swings down toward 0 V, and the OPA350 gets within a few millivolts of the rail. DC headroom stays about **2.4 µA**, because it's set by Vref / Rf, not by the op-amp.

## After the swap

Re-run test steps 2, 4, 5 and 7 from the [test procedure](test-procedure.md). Compare the step 7 noise floor against the LM358 baseline.
