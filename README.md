# Thrym
An OpenCV-based robot for Ragnarock players

## Requirements
To run this script, you need Python 3.10 or higher, along with the following packages:

- `opencv-python`
- `vidgear`
- `pyautogui`
- `pygetwindow`
- `numpy`

##Installation

To install these packages, you can use pip. Run the following command in your terminal:

```bash
pip install opencv-python vidgear pyautogui pygetwindow numpy

## Read carefully before using
Thrym is an open-source project provided "as is," without warranty of any kind, express or implied. By using Thrym, you agree that:

1. The project is provided for educational and informational purposes only.
2. The developers and contributors of Thrym make no representations or warranties of any kind concerning the safety, suitability, or accuracy of the project.
3. You are solely responsible for your use of Thrym and any consequences that may arise from it.
4. The developers and contributors of Thrym will not be liable for any direct, indirect, special, incidental, or consequential damages, whether based on contract, tort, or any other legal theory, arising out of your use or inability to use the project.
5. Thrym is not intended for use in any high-risk activities where the failure of the project could lead to harm, injury, or death. You agree not to use Thrym for such purposes.
6. The developers and contributors of Thrym are not responsible for any unauthorized or inappropriate use of the project.
7. You understand that Thrym may have bugs, errors, or other issues, and you use it at your own risk.

**By using Thrym, you acknowledge and agree to these terms. If you do not agree with these terms, you should not download, use, modify, distribute, share, and/or refer others to Thrym.**

Do not cause trouble in the community. **Your actions have consequences.**

## What?
This single Python script will "play" the game for you, so you have at least one "person" to play against. It's basically a dummy player that will actually put up some semblance of a fight.

The point of this robot is NOT to play the game perfectly, it's just to play it well enough to not feel lonely.

## Why?
I live in a region where this game is really (and I do mean REALLY) not well-known. I often had to wait until midnight just to play with others, even then many will (not "would") have latency issues or will eventually need to leave to do their things, leaving me with nobody to play. This was not good, so I have developed a solution.

## How?
This uses OpenCV to detect the notes and decide which keys to press. It uses various ways to try and optimize the process, such as using LUT (Lookup Table) and using masks to cut away sections that don't require processing.

## Cool, what do I need?
You need the following to use this robot.
1. A full copy of Ragnarock on Steam (PC)
2. (Optional) Additional DLCs to play
3. Another computer or a VR headset on another computer to join the multiplayer match
4. Second copy of Ragnarock on Steam (PC) to run on the computer/headset you'll use to play the game
5. Python libraries: `vidgear, opencv-python, pyautogui, pygetwindow, numpy, pynput`
6. Python 3.10 or newer

## Note
- Using this bot to cheat on the leaderboards will not end well.
- This is strictly for entertainment purposes and must not be used for any other purposes, including but not limited to, fraud and cheating.
- This script uses a lot of CPU processing power. You may need a better processor to run both the game and this script. I used AMD Ryzen 5 5600X for the development and testing rig.
- The author is not responsible for any damages or trouble you may encounter by choosing to use this script.

## A short story based on the development background
It was one of the nights before the Yuletide. A lone poet, whose friends have all but disappeared, was writing a tome. A tome, birthed in sorrow and loneliness, that will create an imperfect copy of what his friends used to be -- a jotunn. With the power of the snake and Thor's hammer, fueled by the water from the Seed of Determination and the gift of Freya, he has brought his creation to life and named the jotunn Thrym. The first jotunn created by the tome had five imperfect and flawed eyes, and when he visited the village, he was met with the Viking warriors who challenged him to a battle. In this battle, Thrym has shown that even with flawed eyes, the jotunn could fight reasonably well against them, earning him an honorable name. But it was not enough for Thrym. Thrym has returned to the poet and requested that he be turned back into the dust, and from this dust, a better warrior be born. The poet agreed and went to work. From the dust the first jotunn Thrym has returned to, the second jotunn Thrym was born. Thrym now had two eyes, two hands, and six fingers, and was taught a short list of actions to perform. Thrym has returned to the village and now awaits any warrior who will challenge him to a battle of drums with arcane powers.
