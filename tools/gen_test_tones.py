#!/usr/bin/env python3
"""
gen_test_tones.py - Make a WAV file of stepped, equal-amplitude test tones.

Use it to check the receive chain's frequency response. Play the file from a
computer or phone into an IR LED driver (or into the current-injection test
jig described in docs/test-procedure.md), record the TDA2050 module output,
and run analyze_tones.py on the recording.

Each tone is preceded by a gap of silence, so the analyzer can also estimate
the noise floor at each frequency.

Standard library only.

Examples:
    python3 tools/gen_test_tones.py                     # default 500 Hz-15 kHz set
    python3 tools/gen_test_tones.py -f 1500,15000 -d 3  # just the two endpoints
"""

import argparse
import array
import math
import sys
import wave

DEFAULT_FREQS = "500,1000,1500,3000,6000,10000,15000"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-o", "--out", default="test_tones.wav", help="output WAV (default test_tones.wav)")
    p.add_argument("-f", "--freqs", default=DEFAULT_FREQS,
                   help=f"comma-separated tone frequencies in Hz (default {DEFAULT_FREQS})")
    p.add_argument("-d", "--duration", type=float, default=2.0, help="seconds per tone (default 2)")
    p.add_argument("-g", "--gap", type=float, default=1.0, help="seconds of silence before each tone (default 1)")
    p.add_argument("-a", "--amplitude", type=float, default=-6.0, help="tone level in dBFS (default -6)")
    p.add_argument("-r", "--rate", type=int, default=48000, help="sample rate (default 48000)")
    p.add_argument("--ramp", type=float, default=0.01, help="fade in/out time in seconds (default 0.01)")
    args = p.parse_args(argv)

    freqs = [float(x) for x in args.freqs.split(",") if x.strip()]
    nyq = args.rate / 2
    bad = [f for f in freqs if f >= nyq * 0.9]
    if bad:
        p.error(f"frequencies {bad} are too close to Nyquist ({nyq:g} Hz); raise --rate")

    amp = 32767 * 10 ** (args.amplitude / 20)
    n_tone = int(args.duration * args.rate)
    n_gap = int(args.gap * args.rate)
    n_ramp = max(1, int(args.ramp * args.rate))

    samples = array.array("h")
    for f in freqs:
        samples.extend([0] * n_gap)
        w = 2 * math.pi * f / args.rate
        for n in range(n_tone):
            env = min(1.0, n / n_ramp, (n_tone - 1 - n) / n_ramp)
            samples.append(int(round(amp * env * math.sin(w * n))))
    samples.extend([0] * n_gap)

    if sys.byteorder == "big":
        samples.byteswap()
    with wave.open(args.out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(args.rate)
        wf.writeframes(samples.tobytes())

    total = len(samples) / args.rate
    print(f"Wrote {args.out}: {len(freqs)} tones at {args.amplitude:g} dBFS, "
          f"{args.duration:g} s each with {args.gap:g} s gaps, {total:.1f} s total")
    print("Tone order: " + ", ".join(f"{f:g} Hz" for f in freqs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
