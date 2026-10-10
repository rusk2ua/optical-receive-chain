# Changelog

Date-based versions (`YYYY.MM.DD`).

## 2026.10.10

First release.

- PD49PI photodiode with an LM358 transimpedance amplifier (Rf 1 MΩ, Cf 3.3 pF), flat from 500 Hz to 15 kHz
- Photodiode run at 2.5 V reverse bias (about 24 pF instead of about 48 pF)
- Interface to an unmodified TDA2050 module (series 50 kΩ pot, 2.2 µF, 22 kΩ) through 100 Ω, with a 10 kΩ pull-down on the LM358 output
- Power moved from the temporary ESP8266 5 V rail to the 13 V LFP battery: the TDA2050 module runs directly from the battery, and the front end gets a 1N5819, 100 Ω / 100 µF, 78L05, 47 Ω / 100 µF filtered 5 V rail, sized for the OPA350's 5.5 V maximum
- Schematics: system wiring and grounding, power supply, front end (SVG)
- Tools: `tia_calc.py`, `gen_test_tones.py`, `analyze_tones.py`
- Docs: design notes, power, build and layout, test procedure, OPA350 upgrade, BOM
