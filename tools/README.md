# Tools

Small Python 3 helpers for designing and testing the receive chain.

| Script | Needs | What it does |
|---|---|---|
| `tia_calc.py` | standard library | TIA stability, bandwidth, response, noise breakdown, and DC headroom |
| `gen_test_tones.py` | standard library | Writes a WAV of stepped equal-level test tones |
| `analyze_tones.py` | numpy | Measures tone level, flatness, SNR and noise floor in a recording |

```bash
pip install -r tools/requirements.txt   # only analyze_tones.py needs it
```

## tia_calc.py

```bash
python3 tools/tia_calc.py                            # LM358, 1 MΩ, 3.3 pF, PD49PI at 2.5 V bias
python3 tools/tia_calc.py --cd 48e-12                # same, photodiode at zero bias
python3 tools/tia_calc.py --opamp opa350 --cf 2.2e-12
python3 tools/tia_calc.py --rf 470e3 --cf 6.8e-12    # try other values
python3 tools/tia_calc.py --csv sweep.csv            # 10 Hz–1 MHz sweep for Google Sheets
```

Key options:

- `--opamp lm358|opa350|ne5532` picks a preset. Override individual specs with `--gbw`, `--en` and `--in`.
- `--cd` sets the photodiode capacitance at your bias point. For the PD49PI that's about 48 pF at 0 V and about 24 pF at 2.5 V (datasheet Fig. 5).
- `--stray` sets extra capacitance at pin 2. The default is 4 pF.
- `--idc` sets the DC photocurrent (dark plus ambient) used for the shot-noise estimate.
- `--band lo,hi` sets the noise integration band.

The model treats the op-amp as single-pole and uses ballpark noise values. It's good for comparing options and choosing Cf, but measure the real build.

## gen_test_tones.py

```bash
python3 tools/gen_test_tones.py                       # 500, 1k, 1.5k, 3k, 6k, 10k, 15k Hz
python3 tools/gen_test_tones.py -f 1500,15000 -d 3 -a -12 -o ends.wav
```

Each tone has a gap of silence before it, so the analyzer can measure the noise floor at every frequency.

## analyze_tones.py

```bash
python3 tools/analyze_tones.py recording.wav
python3 tools/analyze_tones.py recording.wav -f 1500,15000 --ref 1500
python3 tools/analyze_tones.py capped.wav            # noise floor only
```

It reads 16-, 24- or 32-bit PCM WAV files and analyzes channel 0 by default (`--channel 1` for the right channel). Use the "Rel" column for flatness and "Noise dBFS/Hz" for before-and-after comparisons. See [docs/test-procedure.md](../docs/test-procedure.md).
