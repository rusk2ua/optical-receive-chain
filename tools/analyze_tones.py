#!/usr/bin/env python3
"""
analyze_tones.py - Measure tone levels, flatness and SNR in a receiver recording.

Record the TDA2050 module output (line level into a sound card, or through a
resistive divider from a dummy load) while the transmitter or a test jig sends
the tones from gen_test_tones.py, or tones from the beacon firmware. Then:

    python3 tools/analyze_tones.py recording.wav
    python3 tools/analyze_tones.py recording.wav -f 1500,15000 --ref 1500

For each frequency it slices the file into short blocks, measures the level at
that frequency in every block (Hann-windowed single-bin DFT), and reports:

  * tone level   - median of the blocks within 6 dB of the loudest one
                   (i.e. while that tone is on)
  * noise level  - median of the quietest 50% of blocks (when it is off)
  * SNR          - tone minus noise, in the block's noise bandwidth
  * noise density, normalized to a 1 Hz bandwidth (dBFS/Hz, approximate,
    within ~2 dB; good for before/after comparisons)
  * response relative to the --ref frequency, for flatness checks

Requires numpy.
"""

import argparse
import sys
import wave

try:
    import numpy as np
except ImportError:
    sys.exit("analyze_tones.py needs numpy:  pip install -r tools/requirements.txt")

DEFAULT_FREQS = "500,1000,1500,3000,6000,10000,15000"


def read_wav(path, channel):
    with wave.open(path, "rb") as wf:
        nch, width, rate, n = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
        raw = wf.readframes(n)
    if width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        ints = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16))
        ints = np.where(ints & 0x800000, ints - 0x1000000, ints)
        data = ints.astype(np.float64) / 8388608.0
    elif width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        sys.exit(f"Unsupported sample width: {width * 8} bits")
    data = data.reshape(-1, nch)
    if channel >= nch:
        sys.exit(f"File has {nch} channel(s); --channel {channel} doesn't exist")
    return data[:, channel], rate


def block_levels(x, rate, freq, block_s):
    """Peak amplitude (FS units) of a sine at `freq` in each block."""
    n = int(block_s * rate)
    nblocks = len(x) // n
    if nblocks < 4:
        sys.exit("Recording is too short for the chosen block size")
    win = np.hanning(n)
    t = np.arange(n) / rate
    ref = win * np.exp(-2j * np.pi * freq * t)
    blocks = x[: nblocks * n].reshape(nblocks, n)
    blocks = blocks - blocks.mean(axis=1, keepdims=True)
    # 2/sum(win) scales the single-bin DFT to sine peak amplitude
    return np.abs(blocks @ ref) * 2.0 / win.sum(), n


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("wav", help="recorded WAV file (16/24/32-bit PCM)")
    p.add_argument("-f", "--freqs", default=DEFAULT_FREQS, help=f"tone frequencies, Hz (default {DEFAULT_FREQS})")
    p.add_argument("--ref", type=float, default=1500.0, help="reference frequency for relative response (default 1500)")
    p.add_argument("--block", type=float, default=0.1, help="analysis block length, s (default 0.1)")
    p.add_argument("--channel", type=int, default=0, help="channel to analyze, 0 = left (default 0)")
    args = p.parse_args(argv)

    x, rate = read_wav(args.wav, args.channel)
    freqs = [float(f) for f in args.freqs.split(",") if f.strip()]
    if args.ref not in freqs:
        freqs.append(args.ref)
        freqs.sort()

    clip = np.mean(np.abs(x) > 0.999) * 100
    print(f"{args.wav}: {len(x) / rate:.1f} s at {rate} Hz, peak {db(np.max(np.abs(x))):.1f} dBFS"
          + (f"  ** {clip:.2f}% of samples clipped **" if clip > 0 else ""))

    results = {}
    for f in freqs:
        if f >= rate / 2:
            print(f"  skipping {f:g} Hz (above Nyquist)")
            continue
        lv, n = block_levels(x, rate, f, args.block)
        srt = np.sort(lv)
        # "on" blocks: within 6 dB of the loudest block for this frequency
        tone = np.median(srt[srt >= srt[-1] / 2.0])
        noise = np.median(srt[: max(1, len(srt) // 2)])
        enbw = 1.5 * rate / n  # Hann window equivalent noise bandwidth, Hz
        results[f] = (tone, noise, enbw)

    ref_tone = results[args.ref][0] if args.ref in results else None
    print()
    print(f"{'Freq':>8} {'Tone dBFS':>10} {'Noise dBFS':>11} {'SNR dB':>7} "
          f"{'Noise dBFS/Hz':>14} {'Rel ' + format(args.ref, 'g') + ' Hz':>12}")
    for f, (tone, noise, enbw) in results.items():
        # noise is an RMS-ish amplitude in ENBW; normalize to 1 Hz
        nd = db(noise) - 10 * np.log10(enbw)
        rel = db(tone / ref_tone) if ref_tone else float("nan")
        print(f"{f:>7g}  {db(tone):>10.1f} {db(noise):>11.1f} {db(tone / noise):>7.1f} "
              f"{nd:>14.1f} {rel:>+12.2f}")

    print()
    print(f"Block {args.block:g} s, noise bandwidth per block {1.5 / args.block:.1f} Hz.")
    print("SNR here is in that narrow bandwidth; a CW/Q65 decoder's effective bandwidth sets the real figure.")
    if ref_tone:
        spread = [db(t / ref_tone) for t, _, _ in results.values()]
        print(f"Response spread across tested tones: {min(spread):+.2f} to {max(spread):+.2f} dB "
              f"relative to {args.ref:g} Hz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
