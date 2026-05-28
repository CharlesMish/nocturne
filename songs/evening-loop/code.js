// === Evening Loop — Strudel starter sketch ===
// One progression: Em7 -> A7 -> Dmaj7 -> B7 (one chord per bar)
// A warm four-bar groove with 4-on-the-floor drums, octave bass movement,
// and a muted-guitar response.

const TRANSPOSE = 0
const BPM = 111
setcpm(BPM / 4)

// === SHARED HARMONY ===
const loopChords = "<[e4,g4,b4,d5] [e4,g4,a4,c#5] [d4,f#4,a4,c#5] [b3,d#4,f#4,a4]>"
// Disco octave-jumping bass
const loopRoots = "<[e2 ~ e2 ~ e2 ~ ~ ~] [~ a2 ~ a2 a2 ~ ~ [a2 b2]] [d2 ~ d2 ~ d2 ~ ~ [~ b2]] [~ b2 ~ b2 b2 ~ ~ [~ b2]]>"

// === DRUMS ===
// Soft: classic disco — 4-on-floor kick, backbeat snare, alternating
// closed/open hats on 8ths (the genre signature)
const drumsSoft = stack(
  s("bd ~ bd ~ bd ~ bd ~").gain(.95),
  s("~ ~ sd ~ ~ ~ sd ~"),
  stack(
    s("hh oh hh oh hh oh hh oh")
      .gain(.18)
      .pan(sine.range(.38, .62).slow(1.5)),
    s("hh*16")
      .gain(.08)
      .pan(sine.range(.42, .58).slow(2))
  )
)
.compressor("-18:6:8:.01:.08")
.postgain(1.1)
.orbit(1)

const postSnareChatter = stack(
  s("~ ~ ~ [~ hh hh] ~ ~ ~ [~ hh hh]")
    .gain(.08)
    .pan(sine.range(.35, .65).slow(1.25)),
  s("~ ~ ~ [~ sd] ~ ~ ~ [~ sd]")
    .gain(.04)
)

// Lift: same 4-on-floor with a kick double, snare ghosts, clap on 2 & 4
const drumsLift = stack(
  s("bd ~ bd [~ bd] bd ~ bd ~").gain(.95),
  stack(
    s("~ ~ sd ~ ~ ~ sd ~"),
    s("[~ sd] ~ ~ ~ [~ sd] ~ ~ ~").gain(.12)
  ),
  s("hh oh hh oh hh oh hh oh")
    .gain(.2)
    .pan(sine.range(.35, .65).slow(1.5)),
  s("hh*16")
    .gain(.1),
  s("~ ~ cp ~ ~ ~ cp ~")
    .gain(.14),
  postSnareChatter
)
.compressor("-18:6:8:.01:.08")
.postgain(1.1)
.orbit(1)

// === PAD ===
const pad = notes => note(notes)
  .transpose(-12 + TRANSPOSE)
  .s("gm_electric_guitar_clean")
  .clip(.95)
  .attack(.08)
  .decay(.45)
  .sustain(.72)
  .release(.38)
  .gain(.78)
  .vib(4.5)
  .vibmod(.16)
  .lpf(7400)
  .lpq(2.8)
  .lpa(.02)
  .lpd(.6)
  .lps(0)
  .lpr(.12)
  .lpenv(10)
  .phaser(.55)
  .phaserdepth(.5)
  .delay(.26)
  .delaytime(.22)
  .delayfeedback(.3)
  .room(.34)
  .roomsize(9)
  .pan(sine.range(.46, .54).slow(3.5))
  .orbit(8)

// === BASS ===
const bass = notes => note(notes)
  .transpose(TRANSPOSE-12)
  .s("gm_synth_bass_1")
  .clip(.78)
  .compressor("-18:2.4:8:.05:.08")
  .postgain(1.0)
  .attack(.001)
  .decay(.69)
  .sustain(0)
  .release(.014)
  .gain(.69)
  .vib(1.0)
  .vibmod(.04)
  .lpf(420)
  .lpq(5.2)
  .lpa(.01)
  .lpd(.16)
  .lps(0)
  .lpr(.06)
  .lpenv(2.6)
  .room(.18)
  .roomsize(2.5)
  .orbit(4)

// === PLUCK HELPERS ===
const hookPluck = notes => note(notes)
  .transpose(TRANSPOSE)
  .s("gm_electric_guitar_muted")
  .clip(.45)
  .compressor("-18:2.8:2:.04:.07")
  .attack(.001)
  .decay(.34)
  .sustain(0)
  .release(.025)
  .gain(.76)
  .lpf(11000)
  .lpq(4.6)
  .lpa(.02)
  .lpd(.12)
  .lps(0)
  .lpr(.01)
  .lpenv(2.4)
  .delay(.22)
  .delaytime(.0185)
  .delayfeedback(.36)
  .room(.2)
  .roomsize(16)
  .pan(sine.range(.32, .68).slow(2))
  .orbit(13)

const versePluck = notes => note(notes)
  .transpose(TRANSPOSE)
  .s("gm_electric_guitar_muted")
  .clip(.7)
  .compressor("-18:2.6:2:.06:.08")
  .attack(.0012)
  .decay(.62)
  .sustain(0)
  .release(.03)
  .gain(.62)
  .lpf(9600)
  .lpq(4.2)
  .lpa(.035)
  .lpd(.14)
  .lps(0)
  .lpr(.012)
  .lpenv(2.2)
  .delay(.16)
  .delaytime(.0018)
  .delayfeedback(.4)
  .room(.18)
  .roomsize(7)
  .pan(sine.range(.40, .60).slow(2.2))
  .orbit(12)

// === HOOKS AND TEXTURES ===
// Main descending motif.
// Each bar outlines its chord with a syncopated descending phrase.
const riffA = hookPluck("<[b4 g4 ~ e5 d5 ~ b4 g4] [c#5 a4 ~ e5 g5 ~ e5 c#5] [a4 f#4 ~ d5 c#5 ~ a4 f#4] [a4 f#4 ~ d#5 b4 ~ a4 f#4]>")

// Sparkle: high airy sister of riffA, dotted delays for the lift section.
const riffASparkle = hookPluck("<[~ g5 ~ b5 ~ ~ d6 ~ ~ b5 ~ g5 ~ e5 ~ ~] [~ a5 ~ c#6 ~ ~ e6 ~ ~ c#6 ~ a5 ~ g5 ~ ~] [~ d6 ~ f#6 ~ ~ a6 ~ ~ f#6 ~ d6 ~ c#6 ~ ~] [~ b5 ~ d#6 ~ ~ f#6 ~ ~ d#6 ~ b5 ~ a5 ~ ~]>")
  .gain(.22)
  .delay(.4)
  .delaytime(.2175)
  .delayfeedback(.42)

// Secondary riff: low ascending chord-tone pluck.
const riffB = versePluck("<[~ ~ e3 ~ ~ g3 ~ b3] [~ ~ a3 ~ ~ c#4 ~ e4] [~ ~ d3 ~ ~ f#3 ~ a3] [~ ~ b2 ~ ~ d#3 ~ f#3]>")

// Quiet melodic chatter, slightly degraded.
const textureBed = note("<[~ b5 ~ d6 ~ g5 d6 ~] [~ c#6 ~ e6 ~ a5 e6 ~] [~ f#5 ~ a5 ~ d6 a5 ~] [~ f#5 ~ a5 ~ d#6 a5 ~]>")
  .transpose(TRANSPOSE)
  .s("square")
  .clip(.12)
  .attack(.001)
  .decay(.07)
  .sustain(0)
  .release(.02)
  .gain(.12)
  .hpf(900)
  .lpf(4200)
  .lpq(2.5)
  .pan(sine.range(.42, .58).slow(4))
  .degradeBy(.08)
  .delay(.08)
  .delaytime(.125)
  .delayfeedback(.12)
  .room(.08)
  .roomsize(4)
  .orbit(14)

// === SECTION MODULES ===
const harmonicBedSoft = stack(
  drumsSoft,
  pad(loopChords),
  bass(loopRoots)
)

const harmonicBedLift = stack(
  drumsLift,
  pad(loopChords),
  bass(loopRoots)
)

// Intro — just the hook over a quiet pad, no drums
const openingHook = stack(
  pad(loopChords).gain(.35),
  riffA
)

// Light section: full bed + secondary low pluck.
const lightSection = stack(
  harmonicBedSoft,
  riffB
)

// Main section: full bed + primary motif.
const mainSection = stack(
  harmonicBedSoft,
  riffA
)

// Lift section: main groove with sparkle on top.
const liftSection = stack(
  harmonicBedSoft,
  riffA,
  riffASparkle
)

// Dense section: lifted drums + texture.
const denseSection = stack(
  harmonicBedLift,
  riffB,
  textureBed
)

// Outro — pad + bass + hook, drums drop out (echo of intro)
const outro = stack(
  pad(loopChords).gain(.5),
  bass(loopRoots).gain(.55),
  riffA.gain(.7)
)

// === LOOP FORM ===
arrange(
  [4,  openingHook],   // intro motif
  [8,  mainSection],   // main pass 1
  [8,  lightSection],  // light pass
  [4,  liftSection],   // lift
  [8,  mainSection],   // main pass 2
  [16, denseSection],  // dense pass
  [8,  mainSection],   // main pass 3
  [4,  liftSection],   // final lift
  [4,  outro]          // outro
)
