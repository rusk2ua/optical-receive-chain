# Test procedure

Work through these in order. Each step proves out the one after it.

## 1. Power, no op-amp installed

Socket the LM358 if you can. With the chip out and the battery connected, check:

| Point | Expected |
|---|---|
| Battery, after F1 and S1 | 10 to 14.6 V, about 13.2 V typical |
| 78L05 input (after D1 and R1) | about 0.9 V below the battery |
| 78L05 output | 5.0 V ±0.2 V |
| +5 V FE (after R2) | about 4.95 V with no load |
| Vref (pin 3 pad) | about half of +5 V FE |
| Photodiode cathode | about +5 V FE |

## 2. DC operating point, op-amp installed, in the dark

Cap the lens or cover the photodiode.

| Point | Expected |
|---|---|
| +5 V FE | about 4.9 V |
| Pin 3 (Vref) | about 2.45 V |
| Pin 2 | equal to pin 3 within a few millivolts |
| Pin 1 (output) | Vref minus I_dark × 1 MΩ, typically within 30 mV of Vref |
| Pin 7 (unused half) | equal to Vref |

If pin 1 is pinned near ground, the stage is saturated. Check for light leaks, then check the photodiode polarity (cathode toward +5 V).

## 3. Ambient check

Uncover the photodiode in the room where you'll operate. The DC drop at pin 1 is I_ambient × 1 MΩ. A drop of 1 V means 1 µA of ambient photocurrent, which is already about 40% of your 2.4 µA headroom. If pin 1 heads toward 0 V, shade the lens, add a hood or an IR-pass filter, or test after dark.

## 4. Oscillation check

With a scope on pin 1 in the dark, the output should be quiet DC plus noise. A clean sine wave of tens to hundreds of kHz means the stage is oscillating. If it does:

- shorten the pin-2 connections
- increase Cf to 4.7 pF
- confirm the 100 nF supply decoupling is at the chip

## 5. Frequency response by current injection (no light needed)

This tests the TIA, the cable and the module electrically.

**Jig:** sound-card output → **100 nF** film cap → **10 MΩ** resistor → pin 2. The cap blocks the 2.45 V DC at pin 2, and the 10 MΩ turns the sound-card voltage into a test current. At −6 dBFS, about 0.5 V peak, that's about 50 nA peak, or 50 mV peak at pin 1. Keep the 10 MΩ's pin-2 end short. It adds roughly 0.2 pF to the node, which is small.

1. `python3 tools/gen_test_tones.py -o tones.wav`
2. Play `tones.wav` into the jig while recording the module output, through the line-out divider, into a sound card at 48 kHz.
3. `python3 tools/analyze_tones.py recording.wav --ref 1500`
4. **Pass:** the "Rel 1500 Hz" column stays within about ±1 dB from 500 Hz to 15 kHz.
   - If 15 kHz is low by more than 1 dB, there's too much capacitance at pin 2 (strays), or Cf is too large.
   - If 15 kHz is high, or a peak shows up, Cf is too small. Go up one value.

Most sound cards roll off a little near 20 kHz. Run the playback and recording loop once with the jig bypassed and subtract that baseline.

## 6. Optical test, short range

1. Set the beacon running tones, or its normal Q65 or CW, at a few meters, indoors, in the dark. For a PWM keyed-LED transmitter, hold the key down for a steady carrier.
2. Focus the lens. Peak the signal by ear, or watch the spectrum in WSJT-X.
3. Record a test sweep if the beacon firmware can send tones at 1.5 kHz and 15 kHz. Compare them with `analyze_tones.py -f 1500,15000`. This checks the whole optical and electrical chain, including the LED driver's own frequency response.

## 7. Noise floor reference

Record about 30 seconds with the lens capped and the module at the gain you'll actually use. Then run:

```bash
python3 tools/analyze_tones.py capped.wav
```

The "Noise dBFS/Hz" column is your baseline. Re-run it after any layout change, and after the OPA350 upgrade, to compare.

## 8. Range testing

Q65 decodes far below the audible threshold. Don't judge range by ear. Let WSJT-X tell you, and log the reported SNR against distance.
