# hello-world
Clay's First Repo

## SCP Agent Orientation

A diegetic, mobile-first onboarding terminal for new SCP Foundation "agents". It's built to teach the vocabulary and reading habits that make the [SCP Wiki](https://scp-wiki.wikidot.com/) easier to enjoy.

- **7 briefings** (Foundation, Reading a File, Object Classes, Personnel, Hazards, Groups of Interest, Navigating the Archive), each with an in-character briefing and an out-of-character reader's note, then a 4-question assessment.
- **Clearance progression** from Level 0 to Level 4 as you clear briefings and the certification exam. Level 5 is never issued.
- **Lexicon** of 73 terms, redacted until you've been briefed on them, with a search and an override switch.
- **Archive** of curated reading paths that link to the real wiki files, with read tracking.
- **Interactive pieces**: an annotated training file (SCP-TRN-07), a Locked Box classification exercise and an ACS explainer.
- **Android touches**: bottom tab bar, swiping between cards, the back gesture closes sheets, haptic feedback, safe-area insets, light and dark themes, and an installable offline PWA.

### Files

| Path | What it is |
| --- | --- |
| `src/orientation.html` | The app source (a bare page body, also publishable as a claude.ai Artifact) |
| `build.py` | Wraps the source into a full PWA in `docs/` (manifest, service worker) |
| `docs/` | Built site for GitHub Pages: `index.html`, `manifest.webmanifest`, `sw.js`, icons |

Rebuild after editing the source:

```sh
python3 build.py
```

### Install on Android

1. In the repo settings, go to **Pages** and deploy from the `master` branch, `/docs` folder.
2. Open the Pages URL in Chrome on your phone.
3. Open the menu (⋮) and tap **Add to Home screen** (or **Install app**).

Progress is saved on the device (localStorage).

### Licence

Concepts are summarized from the SCP Wiki, which is licensed [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). The orientation text, quizzes and SCP-TRN-07 are original to this project and shared under the same licence.
