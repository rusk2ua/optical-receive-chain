#!/usr/bin/env python3
"""
tia_calc.py - Transimpedance amplifier (TIA) design calculator for the
optical-receive-chain photodiode front end.

Models a photodiode TIA with a feedback resistor Rf and feedback capacitor Cf
around a single-pole op-amp, and reports:

  * minimum stable Cf and the bandwidth you get with it
  * closed-loop transimpedance response (and any peaking) at chosen frequencies
  * noise gain at those frequencies
  * output noise density, broken out by source
  * integrated output noise and input-referred noise over a band
  * DC headroom: how much ambient photocurrent the stage can take before clipping

Standard library only. Op-amp presets use ballpark datasheet values; check your
own parts' datasheets and override with --gbw / --en / --in as needed.

Examples:
    python3 tools/tia_calc.py                       # LM358 stopgap defaults
    python3 tools/tia_calc.py --opamp opa350 --cf 2.2e-12
    python3 tools/tia_calc.py --cd 48e-12 --cf 3.3e-12   # zero-bias photodiode
    python3 tools/tia_calc.py --csv response.csv         # sweep for plotting
"""

import argparse
import cmath
import csv
import math
import sys

K_BOLTZMANN = 1.380649e-23
Q_ELECTRON = 1.602176634e-19

# Ballpark datasheet values. gbw in Hz, en in V/rtHz, i_n in A/rtHz,
# cin = op-amp input capacitance in F, a0 = open-loop DC gain.
OPAMPS = {
    "lm358": dict(gbw=1.0e6, en=40e-9, i_n=0.2e-12, cin=3e-12, a0=1e5,
                  note="Bipolar, single-supply, output swings to ~GND, ~Vcc-1.5 V"),
    "opa350": dict(gbw=38e6, en=7e-9, i_n=4e-15, cin=6.5e-12, a0=1e6,
                   note="CMOS rail-to-rail, 2.7-5.5 V supply ONLY"),
    "ne5532": dict(gbw=10e6, en=5e-9, i_n=0.7e-12, cin=3e-12, a0=1e5,
                   note="Needs >= +/-3 V (6 V total); won't run on 5 V single"),
}


def eng(x, unit=""):
    """Format a number with an engineering prefix."""
    if x == 0 or not math.isfinite(x):
        return f"{x:g} {unit}".strip()
    prefixes = [(1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""),
                (1e-3, "m"), (1e-6, "u"), (1e-9, "n"), (1e-12, "p"), (1e-15, "f")]
    ax = abs(x)
    for scale, p in prefixes:
        if ax >= scale * 0.9995:  # so 999,999.7 prints as 1 M, not 1e+03 k
            return f"{x / scale:.3g} {p}{unit}".strip()
    return f"{x / 1e-15:.3g} f{unit}".strip()


class TIA:
    def __init__(self, rf, cf, ct, gbw, a0, en, i_n, temp_k=300.0,
                 i_dc=0.0):
        self.rf, self.cf, self.ct = rf, cf, ct
        self.gbw, self.a0 = gbw, a0
        self.en, self.i_n = en, i_n
        self.temp_k = temp_k
        self.i_dc = i_dc  # DC photocurrent (dark + ambient) for shot noise

    def _parts(self, f):
        w = 2 * math.pi * f
        zf = self.rf / (1 + 1j * w * self.rf * self.cf)
        zs = 1 / (1j * w * self.ct) if f > 0 else complex(1e30, 0)
        fp = self.gbw / self.a0
        a = self.a0 / (1 + 1j * f / fp)
        beta = zs / (zs + zf)
        return zf, zs, a, beta

    def transimpedance(self, f):
        """Closed-loop |Vout / Iphoto| in ohms (complex)."""
        zf, _, a, beta = self._parts(f)
        return -zf * (a * beta) / (1 + a * beta)

    def noise_gain(self, f):
        """|Vout / en| - how much op-amp voltage noise is amplified."""
        _, _, a, beta = self._parts(f)
        return abs(a / (1 + a * beta))

    def noise_density(self, f):
        """Output noise density components in V/rtHz at frequency f."""
        zt = abs(self.transimpedance(f))
        i_rf = math.sqrt(4 * K_BOLTZMANN * self.temp_k / self.rf)
        i_shot = math.sqrt(2 * Q_ELECTRON * self.i_dc) if self.i_dc > 0 else 0.0
        comps = {
            "Rf thermal": i_rf * zt,
            "op-amp i_n": self.i_n * zt,
            "op-amp e_n": self.en * self.noise_gain(f),
            "shot (DC photocurrent)": i_shot * zt,
        }
        comps["total"] = math.sqrt(sum(v * v for v in comps.values()))
        return comps

    def integrated_noise(self, f_lo, f_hi, points=2000):
        """RMS output noise and input-referred RMS current over a band.

        Input-referred figure divides by the transimpedance at each frequency,
        so it is the equivalent photocurrent noise a signal must beat.
        """
        logs = [math.log10(f_lo) + i * (math.log10(f_hi) - math.log10(f_lo)) / (points - 1)
                for i in range(points)]
        freqs = [10 ** x for x in logs]
        vo2 = []
        ii2 = []
        for f in freqs:
            vt = self.noise_density(f)["total"]
            zt = abs(self.transimpedance(f))
            vo2.append(vt * vt)
            ii2.append((vt / zt) ** 2)
        vo, ii = 0.0, 0.0
        for k in range(1, len(freqs)):
            df = freqs[k] - freqs[k - 1]
            vo += 0.5 * (vo2[k] + vo2[k - 1]) * df
            ii += 0.5 * (ii2[k] + ii2[k - 1]) * df
        return math.sqrt(vo), math.sqrt(ii)

    def peak(self, f_lo=10.0, f_hi=10e6, points=3000):
        """Return (max |Zt|/Rf, frequency) and the -3 dB frequency."""
        best, fbest, f3 = 0.0, f_lo, None
        for i in range(points):
            f = 10 ** (math.log10(f_lo) + i * (math.log10(f_hi) - math.log10(f_lo)) / (points - 1))
            r = abs(self.transimpedance(f)) / self.rf
            if r > best:
                best, fbest = r, f
            if f3 is None and f > fbest and r < 1 / math.sqrt(2):
                f3 = f
        return best, fbest, f3


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--opamp", choices=sorted(OPAMPS), default="lm358",
                   help="op-amp preset (default: lm358)")
    p.add_argument("--rf", type=float, default=1e6, help="feedback resistor, ohms (default 1e6)")
    p.add_argument("--cf", type=float, default=3.3e-12, help="feedback capacitor, F (default 3.3e-12)")
    p.add_argument("--cd", type=float, default=24e-12,
                   help="photodiode capacitance at operating bias, F "
                        "(PD49PI: ~48e-12 at 0 V, ~24e-12 at 2.5 V reverse)")
    p.add_argument("--stray", type=float, default=4e-12,
                   help="extra stray capacitance on the inverting node, F (default 4e-12)")
    p.add_argument("--gbw", type=float, help="override op-amp gain-bandwidth, Hz")
    p.add_argument("--en", type=float, help="override op-amp voltage noise, V/rtHz")
    p.add_argument("--in", dest="i_n", type=float, help="override op-amp current noise, A/rtHz")
    p.add_argument("--freqs", type=str, default="500,1000,1500,5000,10000,15000",
                   help="comma-separated report frequencies, Hz")
    p.add_argument("--band", type=str, default="300,20000",
                   help="noise integration band lo,hi in Hz (default 300,20000)")
    p.add_argument("--idc", type=float, default=1e-9,
                   help="DC photocurrent for shot noise, A (dark + ambient; default 1e-9)")
    p.add_argument("--vref", type=float, default=2.5, help="non-inverting input bias, V (default 2.5)")
    p.add_argument("--vout-min", type=float, default=0.05,
                   help="lowest output swing the op-amp reaches, V (default 0.05)")
    p.add_argument("--csv", type=str, help="write a 10 Hz-1 MHz response/noise sweep to this CSV")
    args = p.parse_args(argv)

    oa = dict(OPAMPS[args.opamp])
    if args.gbw:
        oa["gbw"] = args.gbw
    if args.en:
        oa["en"] = args.en
    if args.i_n:
        oa["i_n"] = args.i_n

    ct = args.cd + oa["cin"] + args.stray
    tia = TIA(args.rf, args.cf, ct, oa["gbw"], oa["a0"], oa["en"], oa["i_n"], i_dc=args.idc)

    cf_min = math.sqrt(ct / (2 * math.pi * args.rf * oa["gbw"]))
    f3_at_min = math.sqrt(oa["gbw"] / (2 * math.pi * args.rf * ct))
    f_feedback_pole = 1 / (2 * math.pi * args.rf * args.cf)
    pk, fpk, f3 = tia.peak()

    print(f"Op-amp: {args.opamp.upper()}  ({oa['note']})")
    print(f"  GBW {eng(oa['gbw'], 'Hz')}, e_n {eng(oa['en'], 'V/rtHz')}, "
          f"i_n {eng(oa['i_n'], 'A/rtHz')}")
    print(f"Rf {eng(args.rf, 'ohm')}, Cf {eng(args.cf, 'F')}, "
          f"total input C {eng(ct, 'F')} "
          f"(diode {eng(args.cd, 'F')} + op-amp {eng(oa['cin'], 'F')} + stray {eng(args.stray, 'F')})")
    print()
    print("Stability / bandwidth")
    print(f"  Minimum Cf for ~45 deg phase margin : {eng(cf_min, 'F')}"
          + ("   <-- Cf is BELOW this, expect ringing" if args.cf < cf_min else "   (Cf OK)"))
    print(f"  Bandwidth if Cf = minimum           : {eng(f3_at_min, 'Hz')}")
    print(f"  Feedback pole 1/(2 pi Rf Cf)        : {eng(f_feedback_pole, 'Hz')}")
    print(f"  Modeled -3 dB point                 : {eng(f3, 'Hz') if f3 else '> 10 MHz'}")
    print(f"  Peaking                             : {20 * math.log10(pk):+.2f} dB at {eng(fpk, 'Hz')}")
    print()

    freqs = [float(x) for x in args.freqs.split(",") if x.strip()]
    ref = abs(tia.transimpedance(freqs[0]))
    print(f"{'Freq':>9} {'|Zt|':>10} {'rel dB':>7} {'NG':>6} {'Rf':>9} {'i_n':>9} "
          f"{'e_n':>9} {'shot':>9} {'total':>9}   (noise in nV/rtHz at output)")
    for f in freqs:
        zt = abs(tia.transimpedance(f))
        nd = tia.noise_density(f)
        print(f"{eng(f, 'Hz'):>9} {eng(zt, 'ohm'):>10} {20 * math.log10(zt / ref):>7.2f} "
              f"{tia.noise_gain(f):>6.1f} "
              f"{nd['Rf thermal'] * 1e9:>9.1f} {nd['op-amp i_n'] * 1e9:>9.1f} "
              f"{nd['op-amp e_n'] * 1e9:>9.1f} {nd['shot (DC photocurrent)'] * 1e9:>9.1f} "
              f"{nd['total'] * 1e9:>9.1f}")
    print()

    lo, hi = (float(x) for x in args.band.split(","))
    vo_rms, ii_rms = tia.integrated_noise(lo, hi)
    print(f"Integrated noise, {eng(lo, 'Hz')} to {eng(hi, 'Hz')}")
    print(f"  Output RMS noise        : {eng(vo_rms, 'V')}")
    print(f"  Input-referred current  : {eng(ii_rms, 'A')} RMS "
          f"(a signal photocurrent this size gives ~0 dB SNR in this band)")
    print()

    headroom = (args.vref - args.vout_min) / args.rf
    print("DC headroom")
    print(f"  Output idles at Vref {args.vref:g} V and moves DOWN with photocurrent.")
    print(f"  Max DC photocurrent before clipping: {eng(headroom, 'A')} "
          f"(dark + ambient + signal peak)")

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["freq_hz", "zt_ohm", "zt_db_rel_rf", "noise_gain",
                        "out_noise_v_rthz", "in_ref_noise_a_rthz"])
            for i in range(400):
                f = 10 ** (1 + i * 5 / 399)
                zt = abs(tia.transimpedance(f))
                nd = tia.noise_density(f)["total"]
                w.writerow([f"{f:.4g}", f"{zt:.6g}", f"{20 * math.log10(zt / args.rf):.3f}",
                            f"{tia.noise_gain(f):.4g}", f"{nd:.4g}", f"{nd / zt:.4g}"])
        print(f"\nWrote sweep to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
