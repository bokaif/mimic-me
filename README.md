# Mimic Me

A brutalist keyboard and mouse automation tool.

<img src="assets/mimic-me.png" alt="Mimic Me UI" width="350">

## Backstory

I actually started this project back in my early high school days. The whole point was to automate making super repetitive certificate designs. I'd just record my keystrokes and mouse movements doing it once, and then set it to play over and over again so it would generate the designs without me needing to do anything.

_(Note: I was completely unaware of Illustrator's built-in bulk creation capability back then :p)_

This thing was basically rotting on my hard drive for years. I recently dug it up, gave it a completely new brutalist overhaul, and now it's actually a solid, polished macro tool for whatever repetitive stuff you want to automate.

## Features

- **Record & Playback:** Grabs all your mouse clicks, movements, and keyboard inputs, then mimics them exactly.
- **Controls:** Run things in a loop, add delays between loops, and tweak the playback speed multiplier.
- **Custom Stop Keys:** Bind a single key (`esc`) or a multi-key combo (`ctrl+shift+a`) to kill the recording/playback instantly.
- **Save & Load:** Export your recorded sequences to a `.mimic` file and load them up whenever.

## Installation & Usage

**Use the app:**  
Grab the executable from [Releases](../../releases). No setup. Just download and run.

**Running from source:**  
If you want to run it locally or tweak the code, just set up a standard python environment:

```bash
# clone the repo
git clone https://github.com/bokaif/mimic-me.git
cd mimic-me

# install dependencies
pip install -r requirements.txt

# run the app
python gui.py
```
