# Build and layout

The front end is a 1 MΩ, few-picofarad circuit. Most problems you'll see (hum, oscillation, a dead top end) come from layout, not component values.

## Physical arrangement

- **Front-end board:** the PD49PI, LM358 TIA, 78L05 and its filters all go in **one grounded metal box mounted at the lens focus**. A die-cast aluminum box or a tinned-steel enclosure works well. The photodiode looks out through a small hole, behind an optional IR-pass filter.
- **Main box:** holds the TDA2050 module, the battery or its connector, the fuse, the switch, and the output jacks.
- **Cable:** shielded 2-conductor, such as microphone cable. One conductor carries the signal (from the 100 Ω resistor), the other carries +13 V, and the shield is ground. Keep it as short as the mechanical layout allows.

## The pin-2 node

This is the part of the build that matters most.

1. Solder the **photodiode anode, Rf and Cf directly to LM358 pin 2**, with leads as short as you can make them. Dead-bug or perfboard is fine. Just keep that node tiny.
2. **No ground plane or ground pour under or around pin 2.** Every 0.5 pF of stray capacitance there shifts the response.
3. Mount Rf and Cf in parallel, side by side, spanning pin 2 to pin 1.
4. Use an **NP0/C0G** ceramic for Cf. X7R and similar dielectrics drift with voltage and temperature.
5. Lead-length capacitance across a 1 MΩ resistor is often 0.2 to 0.5 pF. That's part of why 3.3 pF is chosen rather than the 2.2 pF minimum.
6. If the photodiode can't sit right at the chip, use a short coax pigtail for the anode, with its shield tied to Vref, not ground. That bootstraps the cable capacitance, because pin 2 also sits at Vref.

## Decoupling

- 100 nF ceramic from **pin 8 to pin 4**, at the chip.
- The 10 µF on Vref and the 10 µF on the photodiode bias are both electrolytics. Put the + side toward Vref and toward the 1 kΩ node.
- Keep C4 and C5 (the post-regulator 100 µF and 100 nF) close to the LM358 too.

## The unused LM358 half

Tie **pin 7 to pin 6** and **pin 5 to Vref**. A floating op-amp section can oscillate and couple noise into its neighbor.

## Optical

- The PD49PI's active area is only a few millimeters across, and the lens's focused spot has to land on it. Focus on a distant IR source, then peak the signal by sliding the board along and across the axis.
- **Focusing aid:** an IR viewer card, or a phone camera without an IR-cut filter (front cameras often lack one), will show where the 940 nm spot lands.
- A **rear-projection TV lens** is a fast, multi-element design with a short focal length. Expect a small sweet spot and a narrow field of view. Mount the front-end box on an adjustable slide.
- Add a **lens hood** to keep stray light and sunlight off the photodiode. Ambient light eats the stage's roughly 2.4 µA of DC headroom.
- **IR-pass filter:** optional at night, because the PD49PI's resin already cuts visible light. It helps a lot with any IR-rich ambient light, such as sunlight or incandescent lamps.

## Output

- The TDA2050 module drives a speaker or headphones directly. During setup, use an **8 Ω dummy load** or keep the volume low, since a 1 MΩ front end with nothing connected is loud.
- For WSJT-X or a CW decoder, feed the sound card through a **divider**, such as 4.7 kΩ in series and 470 Ω to ground (about −21 dB), from the module output. If the module is a bridged (BTL) design, neither speaker lead is ground, so use a small isolation transformer or take the signal ahead of the amp instead.
