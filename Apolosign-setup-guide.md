# Setting Up the Family Dashboard on the Apolosign 21.5" Calendar

*A step-by-step guide for someone who has never used Android. Written for Matt, October 2026.*

> **QUICK REFERENCE**
>
> **Dashboard address:** `https://mattski360.github.io/family-dashboard/landscape/`
>
> **Check what the screen reports:** add `?info` to the end, i.e. `https://mattski360.github.io/family-dashboard/landscape/?info`
>
> **Fully Kiosk exit:** swipe in from the **left edge** (hold your finger at the edge for a moment first), then type the PIN.
>
> **Kiosk PIN:** ______________ (write it here and keep this page somewhere safe, not taped to the screen)
>
> **Power button:** short press = screen off/on. Hold 2–3 s = Shut down / Restart menu. [M p.8]
>
> **Mode switch (Calendar ↔ Android):** Settings › Advanced › Default Launcher (Apolosign calls it "Default Home Screen" in some versions). [S], [M p.11]

**Sources** (cited in square brackets):

- [M] Apolosign *Smart Digital Calendar User Guide* (the printed manual in the box; PDF: https://m.media-amazon.com/images/I/E15kOv2-kIL.pdf).
- [S] Apolosign Support, "How Can I Quickly Switch Between Calendar Mode and System Mode?" https://support.apolosign.com/hc/en-us/articles/54586764561177
- [P] Apolosign product page: https://www.apolosign.com/products/21-5-digital-calendar
- [F-K] Fully Kiosk docs, Kiosk Mode: https://www.fully-kiosk.com/docs/en/configuration/kiosk-mode
- [F-D] Fully Kiosk docs, Device Management: https://www.fully-kiosk.com/docs/en/configuration/device-management
- [F-P] Fully Kiosk docs, Power Settings: https://www.fully-kiosk.com/docs/en/configuration/power
- [F-A] Fully Kiosk docs, All Features (PLUS list): https://www.fully-kiosk.com/docs/en/features/all
- [F-L] Fully Kiosk docs, Fully PLUS License: https://www.fully-kiosk.com/docs/en/legal/fully-plus-license
- [F-H] Fully Kiosk help (Toolbars and Appearance): https://www.fully-kiosk.com/en/
- [3M] Command Picture Hanging Strips instructions: https://www.command.com/3M/en_US/command/how-to-use/picture-hanging-strips/ and the Large-strip package insert https://multimedia.3m.com/mws/media/2161800O

Where this guide says **"look for …"**, it means the exact menu name couldn't be confirmed for this device. Android menus vary a little; use the search box at the top of Settings if you can't find it.

---

## A few Android words first

- **Tap** = touch and let go. **Long-press** = touch and hold about a second.
- **Swipe down from the top edge** = opens the notification shade / quick settings (Wi-Fi, brightness).
- **Home / Back:** at the bottom of the screen there are either three buttons (◁ back, ○ home, ▢ recent apps) or a thin bar you swipe up on (swipe up = home). Either works.
- **Settings** = the gear icon ⚙.
- **Google Play Store** = the colourful triangle icon; it's Android's App Store.

---

## 1. Unbox and check the parts

1. In the box: the calendar, a power adapter, a wall-mount bracket, wall anchors and long screws, a drill bit, a spirit level, and a paper mounting template. [M p.5]
2. The screen is 21.5", 1920 × 1080 pixels, 16:9, with a 10-point touch screen. It has a light sensor and a "G-sensor" (it can tell which way up it is). [M p.6–7]
3. The buttons (Power, Volume +, Volume −) and the ports are on the back/side. **DC IN** is for power. The **USB-C port is for service only (ADB)**; it does not charge or power the device. [M p.8]

## 2. Mounting it LANDSCAPE (wide) with 3M Command strips

You've chosen Command strips instead of the bracket. That can work, but read this section through first. **The device weighs about 14.7 lb**, and it's close to the limits of what Command strips are rated to hold.

**What 3M says:**

- The **Large** Command Picture Hanging Strips are rated **"4 pairs hold 16 lbs"**, for frames up to 24 × 36 in. [3M] **Check the weight rating printed on the package you buy.** There are several sizes and "heavy duty" variants, and the rating is printed on each pack. Go by the pack, not by this guide.
- 3M's own cautions: **"Do not hang valuable or irreplaceable items"**, do not hang objects **more than 2 in thick**, don't use on wallpaper or over beds, use indoors at **50–105 °F**, and **wait 7 days after painting**. [3M]

**Honest assessment:** at 14.7 lb, one pack of 4 Large pairs (16 lb) gives almost no margin. A $379 electronic device is the kind of "valuable item" 3M warns against. It is also thicker than 2 in, and its back gets warm. The power cord pulls on it, kids will be tapping it, and strips grip poorly on textured walls (orange-peel or knockdown finish). If you still use strips:

1. **Use more pairs than the minimum.** Aim for a rating well above 15 lb, e.g. **6–8 Large pairs (24–32 lb rated)**, spread across the back. Only stick them to flat, hard parts of the back, never over vents (the manual says not to block the ventilation openings [M p.4]), labels, or the buttons.
2. **Use a smooth, painted wall only.** Don't use them on texture, wallpaper, or fresh paint (wait 7 days). [3M]
3. **Prep:** wipe the wall spots with **isopropyl (rubbing) alcohol**, not water or household cleaner, and let it dry. Wipe the device's back where the strips go the same way. [3M]
4. Click each strip pair together, peel one liner, and press the strips onto the device back. Peel the other liners and press the device firmly onto the wall, **wide side horizontal (landscape)**. Use the spirit level. [3M]
5. **The critical step:** peel the device back off the wall (from the bottom corners, never straight out). Then **press each strip left on the wall firmly for 30 seconds**. [3M]
6. **Wait 1 hour** for the adhesive to build, then line it up and press until every pair clicks. [3M] Use two people. 3M says large items need two people. [3M]
7. **Strain-relieve the cord.** Run the power cord straight down and tape or clip it to the wall a few inches below the device, so it can't tug on the screen. Leave a little slack.
8. **Add a backup. This is strongly recommended.** For example:
   - a small **picture ledge or two screws/L-hooks under the bottom edge**, so the device rests on them and the strips mostly keep it against the wall; or
   - just use the included bracket. It's made for this, and the manual says to **use the horizontal slots for landscape** (vertical slots are for portrait). [M p.10] The back also has a standard **100 × 100 mm VESA** pattern, so any small VESA wall mount will fit. [M p.6]
9. **Don't hang it over a bed or where a fall could hurt someone**, and check the strips after a few days.

**To remove the strips later:** pull each tab slowly **straight down along the wall**, at least 15–18 in. Never pull it toward you. [3M]

## 3. First power-on and Wi-Fi

1. Plug the adapter into **DC IN**, then into the outlet. If it doesn't turn on by itself, **hold the Power button for 2–3 seconds**. [M p.8, p.10]
2. The **Google setup wizard** starts. [M p.11] Pick your language, then **choose your home Wi-Fi network** and type the password. (Tap the eye icon to check what you typed.)
3. It may download updates. Let it finish.

## 4. Google account (or skip)

1. When asked, sign in with **mattski360@gmail.com** (recommended: you need it for the Google Play Store, to install Fully Kiosk). Approve the sign-in on your phone if Google asks.
2. If you'd rather not: tap **"Set up Offline"** or **"Skip Sign in"**. [M p.11] You can add an account later (look for **Accounts** or **Passwords & accounts** in Settings). Without an account you can't use the Play Store, so the Chrome method (step 9) would be your only option.
3. Accept or decline the Google services toggles as you like. None of them matter for the dashboard.

## 5. Choose Android Mode (not Calendar Mode)

The device has two "modes". **Calendar Mode** is Apolosign's own calendar app. **Android Mode** is a normal Android tablet with the Play Store. [M p.11] The dashboard needs **Android Mode**.

1. At the end of setup it asks you to choose. **Tap "Android Mode."** [M p.11]
2. If you already chose Calendar Mode, or want to switch later: open **Settings** in the Apolosign calendar → **Advanced** → **Default Launcher** (some versions say **Default Home Screen**) → choose **Android Mode**. Your data is kept. [S], [M p.11]
3. Switching back works the same way, from Android Mode's Settings app. Look for **Default Launcher** or **Default Home Screen**.

## 6. Make sure it shows landscape

1. Since it's mounted wide, the screen should already be landscape. The device has an orientation sensor (G-sensor). [M p.6]
2. Swipe down from the top edge to open quick settings. Look for **Auto-rotate**. Either **leave it on**, or tap it to lock the screen while it's showing landscape. (On some Android versions, when auto-rotate is off the tile says "Portrait" or "Landscape". Make sure it says Landscape.)
3. Fully Kiosk can also force landscape (step 8). [F-D]

## 7. Turn off Apolosign's screensaver and sleep, and set the brightness

1. **Screensaver:** in Android Mode, open the **"Screensaver"** app and turn it off (or set it to never start). [M p.13]
2. **Sleep Mode** (Apolosign's built-in sleep/wake schedule): in Android Mode, **Settings › Sleep Mode**. [M p.13] Turn it **off** for now. (Step 11 uses it for an optional night schedule.)
3. **Screen timeout:** look for **Screen timeout** in Settings (usually under **Display**) and set it to the longest option or **Never** if offered.
4. **Brightness:** swipe down from the top and drag the brightness slider. The device has a light sensor that can auto-adjust. [M p.7] If the dashboard looks too dim at night or too bright in the day, look for **Adaptive brightness** in Settings › Display and turn it on or off to taste. Fully Kiosk can also set a fixed brightness (step 8).

## 8. Install and set up Fully Kiosk Browser (recommended)

Fully Kiosk Browser shows one web page full-screen, keeps the screen on, and restarts after a power cut.

**Free vs PLUS (being honest):** the free version does **full-screen, Start URL, Keep Screen On, Launch on Boot, and brightness/orientation**. These features are marked **PLUS** (paid): **Kiosk Mode (lock with a PIN), the Scheduled Wakeup/Sleep (night screen-off), the Screen Off Timer**, the Screensaver, Remote Admin and more. [F-A], [F-P], [F-D] **All PLUS features are free to try** (with a watermark and reminders) before you buy. The license is a **one-time payment, lifetime, per device**. [F-L] Check the current price on their site. **For a family dashboard the free version is enough**: you just won't have the PIN lock. You can use Apolosign's own Sleep Mode for nights (step 11).

1. On the home screen, open the **Play Store**. Tap the search bar and type **Fully Kiosk Browser**. Install the one by **Fully Kiosk / ozerov.de** (blue icon). Tap **Open**.
2. Allow the permissions it asks for (tap **Allow**/**OK**). If it asks to be allowed to "display over other apps" or "modify system settings", allow it. That's how it keeps the screen on and starts at boot.
3. It shows a start screen. Open the **settings**: **swipe in from the left edge** to show the menu, then tap **Settings**. [F-K]
4. **Web Content Settings → Start URL:** type `https://mattski360.github.io/family-dashboard/landscape/` and tap OK.
5. **Toolbars and Appearance:** turn **off "Show Status Bar"** and **"Show Navigation Bar"**. Keep them disabled for full screen. Also turn **off** "Show Action Bar" and "Show Address Bar". [F-H]
6. **Device Management:** [F-D]
   - **Keep Screen On** → **on**.
   - **Launch on Boot** → **on** (so it comes back after a power outage).
   - **Force Screen Orientation** → **Landscape**.
   - **Screen Brightness** → leave empty to use the system brightness, or set a number (usually 0–255).
7. Go back. The dashboard loads full-screen. Tap anywhere to flip pages. It turns back on its own after 2 minutes.
8. **(PLUS) Kiosk Mode + PIN:** **Kiosk Mode → Enable Kiosk Mode**, set a **Kiosk Mode PIN**, and keep the exit gesture as **"Swipe from Left"**. Optionally turn on **Disable Status Bar** and **Disable Home Button**. Fully then asks to become the **Home app** and always starts on boot. [F-K] **Write the PIN in the quick-reference box.** Note: on Android 12+ Fully says the lock isn't 100 % tamper-proof without extra provisioning. It's fine for a family kitchen. [F-K]

## 9. Make it open by itself after a power cut

- **Fully Kiosk free:** **Launch on Boot** (step 8.6) is enough. [F-D] Test it: hold Power 2–3 s → **Restart** [M p.8] and wait. It should come back to the dashboard on its own.
- **Fully Kiosk PLUS with Disable Home Button:** Fully becomes the Home app and starts automatically. [F-K]
- **Making Fully the Home app without PLUS:** look for **Default apps › Home app** in Settings and pick Fully Kiosk Browser. *Caution:* the Apolosign launcher switch (step 5) also controls the home screen. If something gets confusing, set it back to Apolosign's Android Mode launcher here.

## 10. Alternative: Chrome + "Add to Home screen" (simpler, no extra app)

1. Open **Chrome** and go to `https://mattski360.github.io/family-dashboard/landscape/`.
2. Tap the **⋮** (three dots, top right) → **Add to Home screen** (it may say **Install app**) → **Add/Install**.
3. Go Home and tap the new **Jensens** icon. The page opens full-screen without the address bar (the page tells Chrome to run it full-screen in landscape).
4. The page asks the screen to stay awake while it's showing (the "Wake Lock" feature). Also do the screen-timeout step in 7.3.
5. Downsides vs Fully: it won't reopen by itself after a power cut (tap the icon again), and it has no PIN lock.

## 11. Optional: screen off at night

- **Free and built in:** in Android Mode, **Settings › Sleep Mode**. Set a sleep time (e.g. 10:00 pm) and a wake time (e.g. 6:00 am). [M p.13]
- **Or Fully Kiosk PLUS:** **Power Settings › Schedule Wakeup and Sleep** (24-hour HH:MM). Fully notes that not every device wakes on schedule. [F-P]
- After waking, the dashboard refreshes itself within 30 minutes. Tap it, or use Fully's reload, if you want it fresh immediately.
- **Manually:** a short press of the Power button turns the screen off or on. [M p.8]

## 12. How to get out of the dashboard to change things

- **Fully Kiosk (no kiosk mode):** swipe in from the **left edge** → **Settings**, or press Home / swipe up to leave.
- **Fully Kiosk with Kiosk Mode:** swipe in from the **left edge**. If the bottom bar is a gesture bar, hold your finger at the left edge for a moment first, then swipe. Enter the **PIN**. You can now open Settings or tap **Exit**. [F-K]
- **Chrome app icon:** swipe up from the bottom (or tap ○ Home).

## 13. Troubleshooting

**The page doesn't fit / looks too small or too big**
1. Open `https://mattski360.github.io/family-dashboard/landscape/?info` (set it as the Start URL temporarily). A box in the corner shows the **viewport** size, **dpr** (pixel ratio) and **wake lock** status. Expected values are around **1920×1080, 1280×720 or 960×540** with dpr 1, 1.5 or 2. The page is built to fit all of them, with or without the system bars.
2. In Fully Kiosk, look in **Advanced Web Settings** for **"Use Wide Viewport"** and zoom/**Initial Scale**. Leave zoom at the default (100 %) so the page controls its own size.
3. If you see a status bar or navigation bar, recheck step 8.5.
4. Put the normal Start URL back when you're done.

**It went to sleep / screen turned off**
- Check Fully's **Keep Screen On** (step 8.6), Apolosign's **Sleep Mode** and **Screensaver** (step 7), and **Screen timeout**. If the `?info` box says *wake lock: active*, the page itself is holding the screen on.

**It lost Wi-Fi**
- Swipe down from the top → long-press **Wi-Fi** → choose your network again. In Fully kiosk mode, exit first (step 12). The dashboard keeps showing the last loaded data and reloads every 30 minutes once Wi-Fi is back. If it says "needs refresh" in the corner, it hasn't been rebuilt for more than about a week.

**It's stuck on an old version**
- The page checks for a newer version every 10 minutes and reloads itself every 30 minutes. To force it: in Fully, open the left-edge menu and tap **Reload** (look for **Clear Cache** in Fully's settings if that doesn't help). In Chrome: ⋮ → reload, or Settings › Privacy › **Delete browsing data** → *Cached images and files*.
- Last resort: hold Power 2–3 s → **Restart**. [M p.8]

**Touch does nothing / taps are ignored**
- Clean the screen with a dry or slightly damp soft cloth. No alcohol on the screen. [M p.4, p.7]

**Need Apolosign help:** in Android Mode open the **"Help & Feedback"** app [M p.13], or email support@apolosign.com. [M]
