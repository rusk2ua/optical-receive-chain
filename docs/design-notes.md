# Design notes

The reasoning behind the front-end values: what was chosen, why, and what was ruled out along the way.

## Transmit sources

The receiver is built for two kinds of transmitter:

1. **The Q65/CW optical beacon** (ESP8266, documented in [rusk2ua/ve2ug-optical-beacon-project](https://github.com/rusk2ua/ve2ug-optical-beacon-project)), which modulates the LED with audio tones.
2. **A hand-keyed 940 nm LED or LED array**, typically driven by a pulse-width modulator (PWM) and keyed on and off with a Morse key.

The receiver hears the **PWM frequency as the CW tone**. Set it somewhere in the 500 Hz to 15 kHz passband. A 600 to 1000 Hz note is easiest on the ears. A square-wave drive also puts energy into odd harmonics (3×, 5×…), so a low PWM frequency gives a buzzier note than a near-sine beacon tone. Use the volume pot or an audio filter if that's fatiguing. A PWM frequency above about 15 kHz rolls off in the TIA, and above about 20 kHz you won't hear it at all.

## Why a transimpedance amplifier

A photodiode is a current source: its photocurrent is proportional to the light that hits it. There are two ways to turn that current into a voltage.

- **Load resistor:** V = I × R, with R straight across the diode. This is simple, but the diode's capacitance sits across R and forms a low-pass at 1/(2πRC). With 1 MΩ and about 50 pF, the corner is about 3 kHz, too low for 15 kHz. The diode voltage also changes with the signal, which hurts linearity.
- **TIA:** an op-amp holds the diode at a virtual ground and forces the photocurrent through a feedback resistor Rf. The output is V = −I × Rf, the diode sees a fixed voltage, and the diode capacitance mostly drops out of the signal path. It still matters for stability and noise, which sets Cf.

The first bench experiment fed the photodiode straight into the TDA2050 module through a 1 MΩ load. That works as a proof of life at 1 kHz, but the TIA beats it on bandwidth, linearity and noise. It's also the same topology as the final OPA350 stage.

## Op-amp choice for the stopgap

Parts on hand were LM741, LM358, NE5532, LM324 and LM386. With Rf = 1 MΩ, the op-amp's **input current noise times Rf** dominates, not its voltage noise. And it all has to run from a single 5 V rail.

| Part | Verdict |
|---|---|
| **LM358 / LM324** | **Chosen.** Low current noise and bias current (about 45 nA typical), runs on a single 5 V supply, and its output swings down to near ground. LM324 is the quad version and works the same here. |
| NE5532 | Excellent voltage noise, but higher current noise and bias current (up to about 800 nA), which costs a lot at 1 MΩ. It also needs at least 6 V total supply, so it can't run on the 5 V front-end rail. |
| LM741 | Worse than the LM358 on every count that matters here. |
| LM386 | A fixed-gain audio power amp, not a general-purpose op-amp. It can't do transimpedance. |

The LM358 has crossover distortion when its output isn't sourcing current. A **10 kΩ pull-down** on the output keeps the output stage biased, at about 0.25 mA at the 2.5 V idle point.

## Photodiode bias

The PD49PI's terminal capacitance (datasheet Fig. 5) is about **48 pF near 0 V** and about **24 pF at 2.5 V reverse bias**.

At 1 kHz, zero bias (photovoltaic mode) is slightly quieter, because there's no dark-current shot noise. For a response flat to 15 kHz, though, halving the capacitance matters more:

- the minimum stable Cf drops (2.2 pF instead of 3.0 pF)
- the op-amp voltage noise gain at high frequency roughly halves
- stability margin improves with Cf = 3.3 pF

So the cathode goes to +5 V through a **1 kΩ resistor with a 10 µF bypass**, a 16 Hz low-pass that keeps rail noise off the diode. The anode goes to pin 2, which sits at Vref = 2.5 V, so the diode sees 2.5 V of reverse bias. The datasheet's dark current is 1 nA typical (30 nA max) even at 10 V. Times 1 MΩ, that's a 1 to 30 mV DC shift, which the module's coupling cap removes.

**Polarity:** with the cathode at the higher voltage, photocurrent flows out of pin 2, through Rf, toward the output. The output therefore idles at Vref and moves **down** as light increases. The signal is inverted, which doesn't matter for CW or Q65.

## Rf and Cf

Rf sets the gain: **1 MΩ = 1 V per µA.** Cf has two jobs. It keeps the loop stable against the diode capacitance, and it sets the top of the passband.

For a single-pole op-amp with gain-bandwidth GBW and total input capacitance Cin (diode plus op-amp plus strays):

- Minimum Cf for about 45° phase margin: **Cf_min ≈ √(Cin / (2π · Rf · GBW))**
- Bandwidth with Cf at that minimum: **f₋₃dB ≈ √(GBW / (2π · Rf · Cin))**

LM358 values: GBW about 1 MHz, Cin about 24 + 3 + 4 = 31 pF.

```
$ python3 tools/tia_calc.py
  Minimum Cf for ~45 deg phase margin : 2.22 pF   (Cf OK)
  Bandwidth if Cf = minimum           : 71.7 kHz
  Feedback pole 1/(2 pi Rf Cf)        : 48.2 kHz
  Modeled -3 dB point                 : 65.1 kHz
   500 Hz ... rel dB  0.00
  15 kHz  ... rel dB -0.05
```

**Cf = 3.3 pF NP0/C0G.** It's comfortably above the minimum, and the modeled response is flat within about 0.1 dB from 500 Hz to 15 kHz. If a real build rings or shows a peak near the top, go to **4.7 pF**, which still keeps 15 kHz within about 0.5 dB (modeled −0.45 dB). Don't go below about 2.2 pF. At that point the model already shows about 1 dB of peaking near 48 kHz.

The earlier 1 kHz-only design used 33 pF. That puts the pole at 4.8 kHz, about 10 dB down at 15 kHz. Don't reuse it.

To see the zero-bias case, run `python3 tools/tia_calc.py --cd 48e-12`. It shows about 0.6 dB of peaking near 31 kHz and noticeably more high-frequency noise.

## Noise

These are output noise densities from `tia_calc.py` for the LM358 build, in nV/√Hz at the output:

| Source | 1 kHz | 15 kHz |
|---|---|---|
| Rf thermal (1 MΩ) | 129 | 128 |
| Op-amp current noise × Rf | 200 | 199 |
| Op-amp voltage noise × noise gain | 41 | 135 |
| Shot noise (1 nA DC) | 18 | 18 |
| **Total** | **242** | **273** |

Integrated from 300 Hz to 20 kHz, that's about **37 pA RMS input-referred**. WSJT-X's Q65 decoder, and your ear copying CW, both work in a far narrower bandwidth than 20 kHz, so the usable sensitivity is much better than that broadband figure. The OPA350's current noise is roughly 50 times lower, which takes that term out and leaves Rf's own thermal noise in charge. That gives about **18 pA RMS** over the same band.

The current-noise numbers are ballpark values, since the LM358 datasheet barely specifies them. Treat the table as relative, and measure the real build with `analyze_tones.py`.

## Headroom and ambient light

The output idles at Vref (about 2.45 V on a 4.9 V rail) and moves down with photocurrent. The LM358 output gets to within a few tens of millivolts of ground, so total DC photocurrent can reach about **2.4 µA** before clipping.

That headroom is shared by dark current, ambient light and the signal peaks. The datasheet shows about 3 µA of short-circuit current at 100 lx of tungsten light, which is rich in near-IR, so **a lit room or daylight will rail the stage**. The PD49PI's built-in visible-cutoff resin helps with LED and fluorescent room light. Sunlight and incandescent light carry plenty of IR, though, so work at night, shade the lens, or add an external 850 to 950 nm IR-pass filter for daylight use.

If daylight operation ever becomes a goal, the fix is DC restoration: a slow servo that removes the DC photocurrent ahead of Rf. That's out of scope for this release.

## Interface to the TDA2050 module

The module's input network, in order: a **50 kΩ pot in series**, then a **2.2 µF electrolytic**, then **22 kΩ to ground** at pin 1.

- The 2.2 µF already blocks the LM358's 2.5 V idle level, so **no extra coupling cap is needed**.
- The high-pass corner is at most 1/(2π · 22 kΩ · 2.2 µF) ≈ 3.3 Hz, so it doesn't touch the signal.
- A **100 Ω series resistor** at the LM358 output isolates cable capacitance, which op-amps with weak output stages don't like driving.
- Because the pot is in series, the volume control only gives about 22 / (22 + 50) ≈ −10 dB of attenuation at minimum. The control never goes fully quiet.
- The 22 kΩ adds about 19 nV/√Hz, which is negligible next to the TIA's output noise. **Leave the module unmodified.**
- The TDA2050 is flat well past 15 kHz at typical module gains.
