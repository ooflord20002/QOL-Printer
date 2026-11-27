"""Cv2 Printer - import automatique des couleurs dans Rec Room.

1. Colle les couleurs (codes hex) copiees depuis le site ou l'encodeur.
2. Enregistre une fois les clics a faire pour regler UNE couleur (double-clic sur une etape pour la modifier).
3. Le script refait ces clics pour chaque marker, en ecrivant sa couleur.

Touches (marchent meme quand le jeu est au premier plan) :
  F6 = tester sur la couleur 1 (sans compte a rebours)
  F7 = lancer toutes les couleurs (sans compte a rebours)
  F8 = capturer la position de la souris
  F9 = arreter tout de suite
  Souris dans le coin en haut a gauche de l'ecran = arret d'urgence

Windows seulement. Aucune librairie a installer.
Lancer :  python import_couleurs.py
"""
import ctypes
import json
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "import_couleurs.json")
IS_WIN = sys.platform == "win32"

# ---------------------------------------------------------------- palette
LINE_RE = re.compile(r"^\s*(\S)\s*->\s*#?([0-9A-Fa-f]{6})\b")
HEX_RE = re.compile(r"#?\b([0-9A-Fa-f]{6})\b")


def parse_palette(text):
    """Lit les lignes du site ("1 -> #FF855E ...") ou une simple liste de codes hex.
    Retourne [(caractere ou None, (r, g, b)), ...] dans l'ordre."""
    out = []
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if m:
            ch, hx = m.group(1), m.group(2)
        else:
            m = HEX_RE.search(line)
            if not m:
                continue
            ch, hx = None, m.group(1)
        out.append((ch, tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))))
    return out


def _hex(c):
    return "%02X%02X%02X" % c


FORMATS = {  # cle -> (texte affiche, fonction couleur -> texte a ecrire)
    "hex": ("FF855E (hex)", _hex),
    "#hex": ("#FF855E (hex avec #)", lambda c: "#" + _hex(c)),
    "rgb": ("255,133,94 (R,G,B)", lambda c: "%d,%d,%d" % c),
    "rgb01": ("1.00,0.52,0.37 (0-1)", lambda c: ",".join("%.2f" % (v / 255) for v in c)),
    "r": ("R seul (0-255)", lambda c: str(c[0])),
    "g": ("G seul (0-255)", lambda c: str(c[1])),
    "b": ("B seul (0-255)", lambda c: str(c[2])),
    "r01": ("R seul (0-1)", lambda c: "%.2f" % (c[0] / 255)),
    "g01": ("G seul (0-1)", lambda c: "%.2f" % (c[1] / 255)),
    "b01": ("B seul (0-1)", lambda c: "%.2f" % (c[2] / 255)),
}
# ---------------------------------------------------------------- touches perso
# On ecrit une touche ou une combinaison avec des + : "E", "Ctrl+A", "Shift+Tab", "F2", "Espace"...
KEY_SUGGESTIONS = ["Entrée", "Échap", "Tab", "Espace", "Retour arrière", "Suppr", "Ctrl+A", "Ctrl+V",
                   "E", "F", "Q", "R", "Haut", "Bas", "Gauche", "Droite", "Shift+Tab"]
NAMED_KEYS = {
    "entrée": 0x0D, "entree": 0x0D, "enter": 0x0D, "tab": 0x09, "échap": 0x1B, "echap": 0x1B, "esc": 0x1B,
    "espace": 0x20, "space": 0x20, "retour arrière": 0x08, "retour arriere": 0x08, "backspace": 0x08,
    "suppr": 0x2E, "delete": 0x2E, "inser": 0x2D, "insert": 0x2D, "début": 0x24, "debut": 0x24, "home": 0x24,
    "fin": 0x23, "end": 0x23, "page haut": 0x21, "pageup": 0x21, "page up": 0x21,
    "page bas": 0x22, "pagedown": 0x22, "page down": 0x22,
    "haut": 0x26, "up": 0x26, "bas": 0x28, "down": 0x28, "gauche": 0x25, "left": 0x25, "droite": 0x27, "right": 0x27,
    "ctrl": 0x11, "control": 0x11, "shift": 0x10, "maj": 0x10, "alt": 0x12, "win": 0x5B,
}
KEY_NAMES = {0x0D: "Entrée", 0x09: "Tab", 0x1B: "Échap", 0x20: "Espace", 0x08: "Retour arrière", 0x2E: "Suppr",
             0x2D: "Inser", 0x24: "Début", 0x23: "Fin", 0x21: "Page haut", 0x22: "Page bas", 0x26: "Haut",
             0x28: "Bas", 0x25: "Gauche", 0x27: "Droite", 0x11: "Ctrl", 0x10: "Shift", 0x12: "Alt", 0x5B: "Win"}
EXTENDED_KEYS = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B}
MODIFIER_VKS = {0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C}


def vk_of(name):
    """Nom de touche -> code Windows (None si inconnu)."""
    n = name.strip().lower()
    if n in NAMED_KEYS:
        return NAMED_KEYS[n]
    if len(n) == 1 and ("a" <= n <= "z" or "0" <= n <= "9"):
        return ord(n.upper())
    m = re.fullmatch(r"f(\d{1,2})", n)
    if m and 1 <= int(m.group(1)) <= 24:
        return 0x6F + int(m.group(1))
    m = re.fullmatch(r"(?:pavé|pave|num)\s*(\d)", n)
    if m:
        return 0x60 + int(m.group(1))
    return None


def vk_name(vk):
    """Code Windows -> nom lisible (None si on ne sait pas l'ecrire)."""
    if vk in KEY_NAMES:
        return KEY_NAMES[vk]
    if 0x41 <= vk <= 0x5A or 0x30 <= vk <= 0x39:
        return chr(vk)
    if 0x70 <= vk <= 0x87:
        return "F%d" % (vk - 0x6F)
    if 0x60 <= vk <= 0x69:
        return "Pavé %d" % (vk - 0x60)
    return None


def parse_combo(text):
    """"Ctrl+Shift+E" -> [0x11, 0x10, 0x45]. Erreur claire si une touche est inconnue."""
    parts = [p for p in re.split(r"\s*\+\s*", text.strip()) if p]
    if not parts:
        raise ValueError("aucune touche écrite")
    vks = []
    for p in parts:
        vk = vk_of(p)
        if vk is None:
            raise ValueError("touche inconnue : « %s » (exemples : E, Ctrl+A, F2, Espace, Haut)" % p)
        vks.append(vk)
    if any(vk in vks for vk in (VK_F6, VK_F7, VK_F8, VK_F9)):
        raise ValueError("F6, F7, F8 et F9 sont réservées au script (tester, lancer, capturer, arrêter)")
    return vks


# ---------------------------------------------------------------- langue (Francais / English)
LANG = "fr"
TR = {
    "Cv2 Printer · Import des couleurs": "Cv2 Printer · Color import",
    "1 · Palette (depuis le site)": "1 · Palette (from the site)",
    "Sur le site, clique « Copier les couleurs (hex) »,\npuis colle-les ici.": "On the site, click « Copy colors (hex) »,\nthen paste them here.",
    "Coller": "Paste",
    "2 · Les clics pour régler UNE couleur": "2 · The clicks to set ONE color",
    "Fais une fois à la main ce qu'il faut pour changer la couleur d'un marker, et note les étapes ici.\nLe script les refait pour chaque marker. Glisse une étape pour la déplacer, double-clic = modifier, clic droit = supprimer (Ctrl+Z pour annuler).":
        "Do it once by hand to change one marker's color, and write the steps here.\nThe script repeats them for each marker. Drag a step to move it, double-click = edit, right-click = delete (Ctrl+Z to undo).",
    "+ Clic": "+ Click", "+ Double-clic": "+ Double-click", "+ Clic droit": "+ Right-click",
    "+ Écrire la couleur": "+ Type the color", "+ Touche": "+ Key", "+ Attendre": "+ Wait",
    "Couleur écrite :": "Color format:", "Attente (s) :": "Wait (s):", "Touche :": "Key:",
    "Appuyer sur une touche…": "Press a key…", "Maintenir (s) :": "Hold (s):",
    "Capturer la position (F8)": "Capture position (F8)", "Monter": "Up", "Descendre": "Down",
    "Supprimer": "Delete", "Remettre l'exemple": "Reset example", "Montrer les clics à l'écran": "Show clicks on screen",
    "3 · Lancer": "3 · Run", "Pause entre actions (s) :": "Pause between actions (s):",
    "Compte à rebours (s) :": "Countdown (s):", "Écrire la couleur en :": "Type the color by:",
    "tapant": "typing", "collant (Ctrl+V)": "pasting (Ctrl+V)",
    "Essai à blanc (montre les actions sans bouger la souris)": "Dry run (shows the actions without moving the mouse)",
    "Tester sur la couleur 1": "Test on color 1", "Lancer toutes les couleurs": "Run all colors", "Arrêter (F9)": "Stop (F9)",
    "Raccourcis, même dans le jeu :   F6 = tester la couleur 1   ·   F7 = lancer toutes les couleurs   ·   F9 = arrêter":
        "Shortcuts, even in the game:   F6 = test color 1   ·   F7 = run all colors   ·   F9 = stop",
    "Arrêt d'urgence : F9, ou souris dans le coin en haut à gauche de l'écran.": "Emergency stop: F9, or mouse in the top-left corner of the screen.",
    "Langue :": "Language:",
    "Le presse-papiers est vide : copie d'abord la palette sur le site.": "The clipboard is empty: copy the colors on the site first.",
    "Choisir une touche": "Choose a key",
    "Appuie sur la touche ou la combinaison\n(ex. : E, ou Ctrl puis A).": "Press the key or the combination\n(e.g. E, or Ctrl then A).",
    "F6 à F9 sont réservées": "F6 to F9 are reserved", "Touche pas reconnue": "Key not recognized",
    "Nom de ce clic (ex. : la case de la couleur) :": "Name of this click (e.g. the color box):",
    "Nom :": "Name:", "Type de clic :": "Click type:", "Position (x , y) :": "Position (x , y):",
    "Recapturer avec F8": "Recapture with F8", "Attendre (s) :": "Wait (s):", "Annuler": "Cancel",
    "Clic": "Click", "Double-clic": "Double-click", "Clic droit": "Right-click",
    "Sélectionne d'abord une étape « Clic sur … » dans la liste.": "First select a « Click on … » step in the list.",
    "Remplacer tes étapes par l'exemple ?": "Replace your steps with the example?",
    "Aucune position capturée pour l'instant.": "No position captured yet.",
    "Glisse un cercle pour déplacer le clic  ·  clic droit = supprimer  ·  clique ici ou Échap pour fermer":
        "Drag a circle to move the click  ·  right-click = delete  ·  click here or Esc to close",
    "Glisse les cercles orange pour déplacer les clics. Échap ou F9 pour fermer.": "Drag the orange circles to move the clicks. Esc or F9 to close.",
    "Arrêt demandé (F9).": "Stop requested (F9).", "Arrêté avant le départ.": "Stopped before starting.",
    "Lancé avec F6 (couleur 1).": "Started with F6 (color 1).", "Lancé avec F7 (toutes les couleurs).": "Started with F7 (all colors).",
    "Colle d'abord la palette (bouton « Copier la palette » sur le site).": "Paste the colors first (button « Copy colors (hex) » on the site).",
    "Ajoute au moins une étape.": "Add at least one step.",
    "La pause ou le compte à rebours n'est pas un nombre.": "The pause or the countdown is not a number.",
    "position à capturer (F8)": "position to capture (F8)",
    "#FF855E (hex avec #)": "#FF855E (hex with #)",
    "R seul (0-255)": "R only (0-255)", "G seul (0-255)": "G only (0-255)", "B seul (0-255)": "B only (0-255)",
    "R seul (0-1)": "R only (0-1)", "G seul (0-1)": "G only (0-1)", "B seul (0-1)": "B only (0-1)",
    "aucune touche écrite": "no key written",
    "F6, F7, F8 et F9 sont réservées au script (tester, lancer, capturer, arrêter)": "F6, F7, F8 and F9 are reserved by the script (test, run, capture, stop)",
}
TR.update({
    "le marker (ouvrir son menu)": "the marker (open its menu)", "la case de la couleur": "the color box",
    "le texte de la couleur": "the color text", "fermer le menu": "close the menu",
    "passer au marker suivant": "go to the next marker", "endroit": "spot",
})
KEY_EN = {"Entrée": "Enter", "Échap": "Esc", "Espace": "Space", "Retour arrière": "Backspace", "Suppr": "Delete",
          "Inser": "Insert", "Début": "Home", "Fin": "End", "Page haut": "Page Up", "Page bas": "Page Down",
          "Haut": "Up", "Bas": "Down", "Gauche": "Left", "Droite": "Right"}


def tr_key(combo):
    """Nom de touche dans la langue choisie ("Ctrl+Entrée" -> "Ctrl+Enter")."""
    if LANG == "fr":
        return combo
    return "+".join(KEY_EN.get(p, p.replace("Pavé", "Num")) for p in combo.split("+"))


_CLICK_EN = {"Clic": "Click", "Double-clic": "Double-click", "Clic droit": "Right-click",
             "clic": "click", "double-clic": "double-click", "clic droit": "right-click"}
TR_PATTERNS = [(re.compile(p), r) for p, r in [
    (r"^(\d+) couleurs? trouvées?$", lambda m: "%s color%s found" % (m[1], "" if m[1] == "1" else "s")),
    (r"^Va dans le jeu, survole « (.*) » et appuie sur F8\.$", lambda m: "Go in the game, hover « %s » and press F8." % tr(m[1])),
    (r"^Position de « (.*) » capturée : (\(.*\))\.$", lambda m: "Position of « %s » captured: %s." % (tr(m[1]), m[2])),
    (r"^Étape (\d+) supprimée \((.*)\)\. Ctrl\+Z pour la remettre\.$", lambda m: "Step %s deleted (%s). Ctrl+Z to undo." % (m[1], tr(m[2]))),
    (r"^Étape (\d+) remise\.$", r"Step \1 restored."),
    (r"^Étape déplacée en position (\d+)\.$", r"Step moved to position \1."),
    (r"^« (.*) » déplacé en (\(.*\))\.$", r"« \1 » moved to \2."),
    (r"^Étape (\d+) : (.*)$", lambda m: "Step %s: %s" % (m[1], tr(m[2]))),
    (r"^Modifier l'étape (\d+)$", r"Edit step \1"),
    (r"^Départ dans (\d+)… Clique dans le jeu\. \(F9 = arrêt\)$", r"Starting in \1… Click in the game. (F9 = stop)"),
    (r"^Couleur (\d+)/(\d+)(?: \(caractère .\))? : (#\w+)$", r"Color \1/\2: \3"),
    (r"^Arrêté à la couleur (\d+)\.$", r"Stopped at color \1."),
    (r"^Fini : (\d+) couleurs? faites?( \(essai à blanc\))?\.$", lambda m: "Done: %s color%s%s." % (m[1], "" if m[1] == "1" else "s", " (dry run)" if m[2] else "")),
    (r"^Erreur : (.*)$", r"Error: \1"),
    (r"^Il manque la position des étapes : (.*)\. Sélectionne-les et clique « Capturer la position \(F8\) »\.$",
     r"Missing position for steps: \1. Select them and click « Capture position (F8) »."),
    (r"^Touche pas valide : (.*)$", lambda m: "Invalid key: " + tr(m[1])),
    (r"^Valeur pas valide : (.*)$", r"Invalid value: \1"),
    (r"^touche inconnue : « (.*) » \(exemples.*\)$", r"unknown key: « \1 » (examples: E, Ctrl+A, F2, Space, Up)"),
    (r"^(Clic|Double-clic|Clic droit) sur « (.*) » → (.*)$", lambda m: "%s on « %s » → %s" % (_CLICK_EN[m[1]], tr(m[2]), tr(m[3]))),
    (r"^Écrire la couleur : (.*)$", lambda m: "Type the color: " + tr(m[1])),
    (r"^Touche : (.*?)(?: \(maintenue ([\d.]+) s\))?$", lambda m: "Key: %s%s" % (tr_key(m[1])," (held %s s)" % m[2] if m[2] else "")),
    (r"^Attendre ([\d.]+) s$", r"Wait \1 s"),
    (r"^(\d+) : (.*)$", lambda m: "%s : %s" % (m[1], tr(m[2]))),
    (r"^(clic|double-clic|clic droit) en (\(.*\))$", lambda m: "%s at %s" % (_CLICK_EN[m[1]], m[2])),
    (r"^écrire « (.*) »$", r"type « \1 »"),
    (r"^touche (.*?)(?: maintenue ([\d.]+) s)?$", lambda m: "key %s%s" % (tr_key(m[1])," held %s s" % m[2] if m[2] else "")),
    (r"^attendre ([\d.]+) s$", r"wait \1 s"),
]]


def tr(s):
    """Traduit un texte de l'interface si la langue est l'anglais."""
    if LANG == "fr" or not isinstance(s, str) or not s:
        return s
    if s in TR:
        return TR[s]
    for rx, rep in TR_PATTERNS:
        m = rx.match(s)
        if m:
            return rep(m) if callable(rep) else m.expand(rep)
    return s


class TrVar(tk.StringVar):
    """Texte d'etat traduit automatiquement."""

    def set(self, value):
        super().set(tr(value))


def default_steps():
    """Exemple pour une rangee de markers ou un clic fait passer au marker suivant :
    le marker est donc toujours au meme endroit de l'ecran."""
    return [
        {"type": "click", "name": "le marker (ouvrir son menu)", "x": None, "y": None},
        {"type": "wait", "s": 0.6},
        {"type": "click", "name": "la case de la couleur", "x": None, "y": None},
        {"type": "wait", "s": 0.5},
        {"type": "click", "name": "le texte de la couleur", "x": None, "y": None, "double": True},
        {"type": "wait", "s": 0.2},
        {"type": "type", "fmt": "hex"},
        {"type": "key", "key": "Entrée"},
        {"type": "wait", "s": 0.4},
        {"type": "click", "name": "fermer le menu", "x": None, "y": None},
        {"type": "wait", "s": 0.5},
        {"type": "click", "name": "passer au marker suivant", "x": None, "y": None},
        {"type": "wait", "s": 1.0},
    ]


def step_label(s):
    t = s["type"]
    if t == "click":
        where = "(%d, %d)" % (s["x"], s["y"]) if s.get("x") is not None else "position à capturer (F8)"
        kind = "Double-clic" if s.get("double") else ("Clic droit" if s.get("btn") == "right" else "Clic")
        return "%s sur « %s » → %s" % (kind, s.get("name") or "endroit", where)
    if t == "type":
        return "Écrire la couleur : " + FORMATS.get(s.get("fmt"), FORMATS["hex"])[0]
    if t == "key":
        hold = float(s.get("hold", 0) or 0)
        return "Touche : " + s.get("key", "Entrée") + (" (maintenue %.1f s)" % hold if hold else "")
    if t == "wait":
        return "Attendre %.1f s" % float(s.get("s", 0.5))
    return "?"


def plan_for(steps, color):
    """Transforme les etapes en actions concretes pour UNE couleur."""
    actions = []
    for s in steps:
        t = s["type"]
        if t == "click":
            if s.get("x") is None:
                raise ValueError("une position de clic n'est pas capturée")
            actions.append(("click", s["x"], s["y"], s.get("btn", "left"), bool(s.get("double"))))
        elif t == "type":
            actions.append(("text", FORMATS.get(s.get("fmt"), FORMATS["hex"])[1](color)))
        elif t == "key":
            actions.append(("key", s.get("key", "Entrée"), float(s.get("hold", 0) or 0)))
        elif t == "wait":
            actions.append(("wait", float(s.get("s", 0.5))))
    return actions


def describe(a):
    if a[0] == "click":
        kind = "double-clic" if a[4] else ("clic droit" if a[3] == "right" else "clic")
        return "%s en (%d, %d)" % (kind, a[1], a[2])
    if a[0] == "text":
        return "écrire « %s »" % a[1]
    if a[0] == "key":
        return "touche %s%s" % (a[1], " maintenue %.1f s" % a[2] if a[2] else "")
    return "attendre %.1f s" % a[1]


# ---------------------------------------------------------------- souris / clavier (Windows, sans librairie)
VK_F6, VK_F7, VK_F8, VK_F9 = 0x75, 0x76, 0x77, 0x78  # F6 tester, F7 lancer, F8 capturer, F9 arreter
if IS_WIN:
    import ctypes.wintypes as wt

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    ULONG_PTR = ctypes.c_size_t

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                    ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                    ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wt.DWORD), ("wParamL", wt.WORD), ("wParamH", wt.WORD)]

    class _INPUTU(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wt.DWORD), ("u", _INPUTU)]

    user32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    user32.OpenClipboard.argtypes = [wt.HWND]
    user32.SetClipboardData.argtypes = [wt.UINT, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wt.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

    MOUSE_LEFTDOWN, MOUSE_LEFTUP = 0x0002, 0x0004
    MOUSE_RIGHTDOWN, MOUSE_RIGHTUP = 0x0008, 0x0010
    KEY_UP, KEY_UNICODE = 0x0002, 0x0004

    def _send(*inputs):
        arr = (INPUT * len(inputs))(*inputs)
        user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))

    def _mouse(flags):
        i = INPUT(type=0)
        i.mi = MOUSEINPUT(0, 0, 0, flags, 0, 0)
        return i

    def _key(vk, up=False):
        i = INPUT(type=1)
        flags = (KEY_UP if up else 0) | (0x0001 if vk in EXTENDED_KEYS else 0)
        i.ki = KEYBDINPUT(vk, user32.MapVirtualKeyW(vk, 0), flags, 0, 0)
        return i

    def _uchar(ch, up=False):
        i = INPUT(type=1)
        i.ki = KEYBDINPUT(0, ord(ch), KEY_UNICODE | (KEY_UP if up else 0), 0, 0)
        return i

    def cursor_pos():
        pt = wt.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def key_down(vk):
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)

    def click(x, y, btn="left", double=False):
        user32.SetCursorPos(int(x), int(y))
        time.sleep(0.05)
        down, up = (MOUSE_RIGHTDOWN, MOUSE_RIGHTUP) if btn == "right" else (MOUSE_LEFTDOWN, MOUSE_LEFTUP)
        for n in range(2 if double else 1):
            _send(_mouse(down))
            time.sleep(0.04)
            _send(_mouse(up))
            if double and n == 0:
                time.sleep(0.06)

    def press_combo(vks, hold=0.0):
        for vk in vks:
            _send(_key(vk))
            time.sleep(0.02)
        if hold:
            time.sleep(hold)
        for vk in reversed(vks):
            _send(_key(vk, up=True))
            time.sleep(0.02)

    def type_text(text):
        for ch in text:
            _send(_uchar(ch))
            _send(_uchar(ch, up=True))
            time.sleep(0.02)

    def set_clipboard(text):
        data = ctypes.create_unicode_buffer(text)
        size = ctypes.sizeof(data)
        h = kernel32.GlobalAlloc(0x0002, size)
        p = kernel32.GlobalLock(h)
        ctypes.memmove(p, data, size)
        kernel32.GlobalUnlock(h)
        for _ in range(20):
            if user32.OpenClipboard(None):
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("presse-papiers occupé")
        try:
            user32.EmptyClipboard()
            user32.SetClipboardData(13, h)
        finally:
            user32.CloseClipboard()

    def paste_text(text):
        set_clipboard(text)
        time.sleep(0.05)
        press_combo([0x11, 0x56])


def in_corner():
    x, y = cursor_pos()
    return x <= 2 and y <= 2


# ---------------------------------------------------------------- config
def load_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


class HotkeyPoller(threading.Thread):
    """Surveille F8 et F9 meme quand le jeu a le focus."""

    def __init__(self, q, stop):
        super().__init__(daemon=True)
        self.q, self.stop = q, stop

    def run(self):
        names = {VK_F6: "f6", VK_F7: "f7", VK_F8: "f8", VK_F9: "f9"}
        prev = {vk: False for vk in names}
        while True:
            for vk in prev:
                down = key_down(vk)
                if down and not prev[vk]:
                    if vk == VK_F9:
                        self.stop.set()
                    self.q.put((names[vk],))
                prev[vk] = down
            time.sleep(0.02)


# ---------------------------------------------------------------- fenetre
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cv2 Printer · Import des couleurs")
        self.root.geometry("1220x790")
        self.q = queue.Queue()
        self.stop = threading.Event()
        self.running = False
        self.capture = None  # None, ou numero de l'etape dont on capture la position
        self.guide = None  # fenetre du guide pas a pas
        self.overlay = None  # clics affiches a l'ecran
        self._drag, self._dragged = None, False  # etape qu'on glisse dans la liste
        self._undo = None  # derniere etape supprimee (Ctrl+Z)
        cfg = load_config()
        global LANG
        LANG = "en" if cfg.get("lang") == "en" else "fr"
        steps = [s for s in (cfg.get("steps") or []) if s.get("type") in ("click", "type", "key", "wait")]
        self.steps = steps or default_steps()
        self.colors = []
        self.build(cfg)
        self.parse_palette()
        self.refresh_steps()
        HotkeyPoller(self.q, self.stop).start()
        self.root.after(50, self.poll)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- construction
    def build(self, cfg):
        r = self.root
        for c, w in ((0, 1), (1, 2)):
            r.columnconfigure(c, weight=w)
        r.rowconfigure(1, weight=1)
        pad = dict(padx=8, pady=6)

        r.title(tr("Cv2 Printer · Import des couleurs"))
        top = ttk.Frame(r)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 0))
        ttk.Button(top, text="English" if LANG == "fr" else "Français", command=self.toggle_lang).pack(side="right")
        ttk.Label(top, text="Langue :").pack(side="right", padx=(0, 6))

        f1 = ttk.LabelFrame(r, text="1 · Palette (depuis le site)")
        f1.grid(row=1, column=0, sticky="nsew", **pad)
        ttk.Label(f1, text="Sur le site, clique « Copier les couleurs (hex) »,\npuis colle-les ici.", justify="left").pack(anchor="w", padx=8, pady=(6, 4))
        ttk.Button(f1, text="Coller", command=self.paste_palette).pack(anchor="w", padx=8)
        self.pal_text = tk.Text(f1, width=34, height=12, font=("Consolas", 9), wrap="none")
        self.pal_text.pack(fill="both", expand=True, padx=8, pady=6)
        self.pal_text.insert("1.0", cfg.get("palette", ""))
        self.pal_text.bind("<KeyRelease>", lambda e: self.root.after(150, self.parse_palette))
        self.pal_info = ttk.Label(f1, text="")
        self.pal_info.pack(anchor="w", padx=8)
        self.swatches = tk.Canvas(f1, height=30, bg="#111111", highlightthickness=0)
        self.swatches.pack(fill="x", padx=8, pady=(4, 8))

        f3 = ttk.LabelFrame(r, text="2 · Les clics pour régler UNE couleur")
        f3.grid(row=1, column=1, sticky="nsew", **pad)
        ttk.Label(f3, text="Fais une fois à la main ce qu'il faut pour changer la couleur d'un marker, et note les étapes ici.\nLe script les refait pour chaque marker. Glisse une étape pour la déplacer, double-clic = modifier, clic droit = supprimer (Ctrl+Z pour annuler).", justify="left").pack(anchor="w", padx=8, pady=(6, 4))
        self.st_list = tk.Listbox(f3, height=12, font=("Consolas", 9), exportselection=False)
        self.st_list.pack(fill="both", expand=True, padx=8, pady=4)
        self.st_list.bind("<Double-Button-1>", self.edit_step)
        self.st_list.bind("<ButtonPress-1>", self.drag_start, add="+")
        self.st_list.bind("<B1-Motion>", self.drag_motion, add="+")
        self.st_list.bind("<ButtonRelease-1>", self.drag_end, add="+")
        self.st_list.bind("<Button-3>", self.right_delete)
        r.bind_all("<Control-z>", self.undo_delete)
        r.bind_all("<Control-Z>", self.undo_delete)
        add = ttk.Frame(f3)
        add.pack(anchor="w", padx=8, pady=2)
        ttk.Button(add, text="+ Clic", command=self.add_click_step).pack(side="left")
        ttk.Button(add, text="+ Double-clic", command=lambda: self.add_click_step(double=True)).pack(side="left", padx=4)
        ttk.Button(add, text="+ Clic droit", command=lambda: self.add_click_step(btn="right")).pack(side="left")
        add2 = ttk.Frame(f3)
        add2.pack(anchor="w", padx=8, pady=2)
        ttk.Button(add2, text="+ Écrire la couleur", command=lambda: self.add_step({"type": "type", "fmt": self.fmt_key()})).pack(side="left")
        ttk.Button(add2, text="+ Touche", command=self.add_key_step).pack(side="left", padx=4)
        ttk.Button(add2, text="+ Attendre", command=lambda: self.add_step({"type": "wait", "s": self.wait_v.get()})).pack(side="left")
        opt = ttk.Frame(f3)
        opt.pack(anchor="w", padx=8, pady=4)
        ttk.Label(opt, text="Couleur écrite :").pack(side="left")
        self.fmt_v = tk.StringVar(value=tr(FORMATS["hex"][0]))
        ttk.Combobox(opt, textvariable=self.fmt_v, values=[tr(v[0]) for v in FORMATS.values()], state="readonly", width=22).pack(side="left", padx=(4, 10))
        ttk.Label(opt, text="Attente (s) :").pack(side="left")
        self.wait_v = tk.DoubleVar(value=0.5)
        ttk.Spinbox(opt, from_=0.1, to=10, increment=0.1, textvariable=self.wait_v, width=5).pack(side="left", padx=4)
        keys = ttk.Frame(f3)
        keys.pack(anchor="w", padx=8, pady=(0, 4))
        ttk.Label(keys, text="Touche :").pack(side="left")
        self.key_v = tk.StringVar(value=tr_key("Entrée"))
        ttk.Combobox(keys, textvariable=self.key_v, values=[tr_key(k) for k in KEY_SUGGESTIONS], width=16).pack(side="left", padx=4)
        ttk.Button(keys, text="Appuyer sur une touche…", command=self.record_key).pack(side="left", padx=(0, 10))
        ttk.Label(keys, text="Maintenir (s) :").pack(side="left")
        self.hold_v = tk.DoubleVar(value=0.0)
        ttk.Spinbox(keys, from_=0, to=30, increment=0.1, textvariable=self.hold_v, width=5).pack(side="left", padx=4)
        edit = ttk.Frame(f3)
        edit.pack(anchor="w", padx=8, pady=(2, 8))
        ttk.Button(edit, text="Capturer la position (F8)", command=self.capture_selected_step).pack(side="left")
        ttk.Button(edit, text="Monter", command=lambda: self.move_step(-1)).pack(side="left", padx=4)
        ttk.Button(edit, text="Descendre", command=lambda: self.move_step(1)).pack(side="left")
        ttk.Button(edit, text="Supprimer", command=self.delete_step).pack(side="left", padx=4)
        ttk.Button(edit, text="Remettre l'exemple", command=self.reset_steps).pack(side="left")
        ttk.Button(edit, text="Montrer les clics à l'écran", command=self.show_overlay).pack(side="left", padx=4)

        f4 = ttk.LabelFrame(r, text="3 · Lancer")
        f4.grid(row=2, column=0, columnspan=2, sticky="nsew", **pad)
        sets = ttk.Frame(f4)
        sets.pack(anchor="w", padx=8, pady=6)
        ttk.Label(sets, text="Pause entre actions (s) :").pack(side="left")
        self.pause_v = tk.DoubleVar(value=cfg.get("pause", 0.25))
        ttk.Spinbox(sets, from_=0.05, to=3, increment=0.05, textvariable=self.pause_v, width=5).pack(side="left", padx=(4, 14))
        ttk.Label(sets, text="Compte à rebours (s) :").pack(side="left")
        self.count_v = tk.IntVar(value=cfg.get("countdown", 5))
        ttk.Spinbox(sets, from_=1, to=30, textvariable=self.count_v, width=4).pack(side="left", padx=(4, 14))
        ttk.Label(sets, text="Écrire la couleur en :").pack(side="left")
        paste = str(cfg.get("method", "")) in ("paste",) or str(cfg.get("method", "")).startswith("coll")
        self.method_v = tk.StringVar(value=tr("collant (Ctrl+V)") if paste else tr("tapant"))
        ttk.Combobox(sets, textvariable=self.method_v, values=[tr("tapant"), tr("collant (Ctrl+V)")], state="readonly", width=16).pack(side="left", padx=(4, 14))
        self.dry_v = tk.BooleanVar(value=False)
        ttk.Checkbutton(sets, text="Essai à blanc (montre les actions sans bouger la souris)", variable=self.dry_v).pack(side="left")
        btns = ttk.Frame(f4)
        btns.pack(anchor="w", padx=8, pady=2)
        self.test_btn = ttk.Button(btns, text="Tester sur la couleur 1", command=lambda: self.start(test=True))
        self.test_btn.pack(side="left")
        self.run_btn = ttk.Button(btns, text="Lancer toutes les couleurs", command=self.start)
        self.run_btn.pack(side="left", padx=6)
        self.stop_btn = ttk.Button(btns, text="Arrêter (F9)", command=self.stop.set, state="disabled")
        self.stop_btn.pack(side="left")
        ttk.Label(f4, text="Raccourcis, même dans le jeu :   F6 = tester la couleur 1   ·   F7 = lancer toutes les couleurs   ·   F9 = arrêter", font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=(4, 0))
        self.status = TrVar(value=tr("Arrêt d'urgence : F9, ou souris dans le coin en haut à gauche de l'écran."))
        ttk.Label(f4, textvariable=self.status, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=4)
        self.log_text = tk.Text(f4, height=6, font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="x", padx=8, pady=(0, 8))
        for v in (self.pause_v, self.count_v, self.method_v):
            v.trace_add("write", lambda *a: self.save())
        self.translate_tree(r)

    def translate_tree(self, widget):
        """Traduit le texte de tous les boutons et etiquettes (si la langue est l'anglais)."""
        for w in widget.winfo_children():
            if isinstance(w, (ttk.Entry, tk.Entry, tk.Text)):  # champs : on ne touche pas a leur contenu
                continue
            try:
                t = w.cget("text")
                if t:
                    w.config(text=tr(t))
            except tk.TclError:
                pass
            self.translate_tree(w)

    def toggle_lang(self):
        global LANG
        LANG = "en" if LANG == "fr" else "fr"
        self.close_overlay()
        if self.guide:
            self.close_guide()
        self.save()
        for w in self.root.winfo_children():
            w.destroy()
        self.build(load_config())
        self.parse_palette()
        self.refresh_steps()

    # ---------- palette
    def paste_palette(self):
        try:
            txt = self.root.clipboard_get()
        except tk.TclError:
            self.status.set("Le presse-papiers est vide : copie d'abord la palette sur le site.")
            return
        self.pal_text.delete("1.0", "end")
        self.pal_text.insert("1.0", txt)
        self.parse_palette()

    def parse_palette(self):
        self.colors = parse_palette(self.pal_text.get("1.0", "end"))
        n = len(self.colors)
        self.pal_info.config(text=tr("%d couleur%s trouvée%s" % (n, "s" if n > 1 else "", "s" if n > 1 else "")))
        self.draw_swatches()
        self.refresh_todo()
        self.save()

    def draw_swatches(self):
        c = self.swatches
        c.delete("all")
        size, gap, per = 22, 3, 12
        rows = max(1, -(-len(self.colors) // per))
        c.config(height=rows * (size + gap) + gap)
        for i, (ch, col) in enumerate(self.colors):
            x = gap + (i % per) * (size + gap)
            y = gap + (i // per) * (size + gap)
            c.create_rectangle(x, y, x + size, y + size, fill="#%02x%02x%02x" % col, outline="#333333")
            if ch:
                lum = 0.299 * col[0] + 0.587 * col[1] + 0.114 * col[2]
                c.create_text(x + size / 2, y + size / 2, text=ch, fill="#000000" if lum > 140 else "#ffffff", font=("Consolas", 8, "bold"))

    # ---------- etapes
    def fmt_key(self):
        label = self.fmt_v.get()
        for k, v in FORMATS.items():
            if v[0] == label or tr(v[0]) == label:
                return k
        return "hex"

    def refresh_steps(self, select=None):
        self.st_list.delete(0, "end")
        for i, s in enumerate(self.steps):
            self.st_list.insert("end", "%2d. %s" % (i + 1, tr(step_label(s))))
        if select is not None and 0 <= select < len(self.steps):
            self.st_list.selection_set(select)
            self.st_list.see(select)
        self.refresh_todo()

    def selected(self):
        sel = self.st_list.curselection()
        return sel[0] if sel else None

    def add_step(self, step):
        i = self.selected()
        i = len(self.steps) if i is None else i + 1
        self.steps.insert(i, step)
        self.refresh_steps(select=i)
        self.save()
        return i

    def add_key_step(self):
        try:
            vks = parse_combo(self.key_v.get())
            hold = max(0.0, float(self.hold_v.get()))
        except (ValueError, tk.TclError) as e:
            messagebox.showwarning("Cv2 Printer", tr("Touche pas valide : %s" % e))
            return
        name = "+".join(vk_name(v) or "?" for v in vks)
        step = {"type": "key", "key": name}
        if hold:
            step["hold"] = hold
        self.add_step(step)

    def record_key(self, target=None):
        """Petite fenetre : on appuie sur la touche (ou la combinaison) et elle est ecrite toute seule."""
        target = target or self.key_v
        win = tk.Toplevel(self.root)
        win.title(tr("Choisir une touche"))
        win.transient(self.root)
        win.resizable(False, False)
        ttk.Label(win, text="Appuie sur la touche ou la combinaison\n(ex. : E, ou Ctrl puis A).", justify="center", font=("Segoe UI", 11)).pack(padx=28, pady=(18, 8))
        shown = tk.StringVar(value="…")
        ttk.Label(win, textvariable=shown, font=("Segoe UI", 18, "bold")).pack(pady=(0, 18))

        def mods(e):
            out = []
            if e.state & 0x4:
                out.append("Ctrl")
            if e.state & 0x1:
                out.append("Shift")
            if e.state & 0x20000:
                out.append("Alt")
            return out

        def on_key(e):
            vk = e.keycode  # sous Windows, Tk donne le code de touche Windows
            if vk in MODIFIER_VKS:
                shown.set("+".join(mods(e) + ["…"]))
                return "break"
            if vk in (VK_F6, VK_F7, VK_F8, VK_F9):
                shown.set(tr("F6 à F9 sont réservées"))
                return "break"
            name = vk_name(vk)
            if name is None:
                shown.set(tr("Touche pas reconnue"))
                return "break"
            combo = "+".join(mods(e) + [name])
            target.set(tr_key(combo))
            shown.set(tr_key(combo))
            win.after(600, win.destroy)
            return "break"

        win.bind("<KeyPress>", on_key)
        self.translate_tree(win)
        win.grab_set()
        win.focus_force()

    def add_click_step(self, double=False, btn="left"):
        name = simpledialog.askstring("Cv2 Printer", tr("Nom de ce clic (ex. : la case de la couleur) :"), parent=self.root)
        if name is None:
            return
        step = {"type": "click", "name": name.strip() or "endroit", "x": None, "y": None}
        if double:
            step["double"] = True
        if btn == "right":
            step["btn"] = "right"
        i = self.add_step(step)
        self.capture = i
        self.status.set("Va dans le jeu, survole « %s » et appuie sur F8." % (name.strip() or "endroit"))

    def edit_step(self, event=None):
        """Double-clic sur une etape : petite fenetre pour la modifier."""
        i = self.st_list.nearest(event.y) if event is not None else self.selected()
        if i is None or not 0 <= i < len(self.steps):
            return
        self.st_list.selection_clear(0, "end")
        self.st_list.selection_set(i)
        s, t = self.steps[i], self.steps[i]["type"]
        win = tk.Toplevel(self.root)
        win.title(tr("Modifier l'étape %d" % (i + 1)))
        win.transient(self.root)
        win.resizable(False, False)
        body = ttk.Frame(win, padding=16)
        body.pack(fill="both")
        row = [0]

        def add_row(label, widget):
            ttk.Label(body, text=label).grid(row=row[0], column=0, sticky="w", pady=5, padx=(0, 12))
            widget.grid(row=row[0], column=1, sticky="w", pady=5)
            row[0] += 1

        v = {}
        if t == "click":
            v["name"] = tk.StringVar(value=s.get("name", ""))
            add_row("Nom :", ttk.Entry(body, textvariable=v["name"], width=32))
            v["kind"] = tk.StringVar(value=tr("Double-clic" if s.get("double") else ("Clic droit" if s.get("btn") == "right" else "Clic")))
            add_row("Type de clic :", ttk.Combobox(body, textvariable=v["kind"], values=[tr("Clic"), tr("Double-clic"), tr("Clic droit")], state="readonly", width=14))
            v["x"] = tk.StringVar(value="" if s.get("x") is None else str(s["x"]))
            v["y"] = tk.StringVar(value="" if s.get("y") is None else str(s["y"]))
            pos = ttk.Frame(body)
            ttk.Entry(pos, textvariable=v["x"], width=7).pack(side="left")
            ttk.Label(pos, text=" , ").pack(side="left")
            ttk.Entry(pos, textvariable=v["y"], width=7).pack(side="left")
            ttk.Button(pos, text="Recapturer avec F8", command=lambda: recapture()).pack(side="left", padx=(10, 0))
            add_row("Position (x , y) :", pos)
        elif t == "type":
            v["fmt"] = tk.StringVar(value=tr(FORMATS.get(s.get("fmt"), FORMATS["hex"])[0]))
            add_row("Couleur écrite :", ttk.Combobox(body, textvariable=v["fmt"], values=[tr(f[0]) for f in FORMATS.values()], state="readonly", width=24))
        elif t == "key":
            v["key"] = tk.StringVar(value=tr_key(s.get("key", "Entrée")))
            kf = ttk.Frame(body)
            ttk.Combobox(kf, textvariable=v["key"], values=[tr_key(k) for k in KEY_SUGGESTIONS], width=16).pack(side="left")
            ttk.Button(kf, text="Appuyer sur une touche…", command=lambda: self.record_key(v["key"])).pack(side="left", padx=(8, 0))
            add_row("Touche :", kf)
            v["hold"] = tk.DoubleVar(value=float(s.get("hold", 0) or 0))
            add_row("Maintenir (s) :", ttk.Spinbox(body, from_=0, to=30, increment=0.1, textvariable=v["hold"], width=6))
        elif t == "wait":
            v["s"] = tk.DoubleVar(value=float(s.get("s", 0.5)))
            add_row("Attendre (s) :", ttk.Spinbox(body, from_=0, to=60, increment=0.1, textvariable=v["s"], width=6))

        def apply_click_fields():
            s["name"] = v["name"].get().strip() or "endroit"
            s.pop("double", None)
            s.pop("btn", None)
            if v["kind"].get() == tr("Double-clic"):
                s["double"] = True
            elif v["kind"].get() == tr("Clic droit"):
                s["btn"] = "right"

        def ok():
            try:
                if t == "click":
                    xs, ys = v["x"].get().strip(), v["y"].get().strip()
                    pos_xy = (int(xs), int(ys)) if (xs or ys) else (None, None)
                    apply_click_fields()
                    s["x"], s["y"] = pos_xy
                elif t == "type":
                    s["fmt"] = next((k for k, f in FORMATS.items() if tr(f[0]) == v["fmt"].get()), "hex")
                elif t == "key":
                    vks = parse_combo(v["key"].get())
                    hold = max(0.0, float(v["hold"].get()))
                    s["key"] = "+".join(vk_name(k) or "?" for k in vks)
                    if hold:
                        s["hold"] = hold
                    else:
                        s.pop("hold", None)
                elif t == "wait":
                    s["s"] = max(0.0, float(v["s"].get()))
            except (ValueError, tk.TclError) as e:
                messagebox.showwarning("Cv2 Printer", tr("Valeur pas valide : %s" % e), parent=win)
                return
            win.destroy()
            self.refresh_steps(select=i)
            self.save()

        def recapture():
            apply_click_fields()
            win.destroy()
            self.refresh_steps(select=i)
            self.save()
            self.capture = i
            self.status.set("Va dans le jeu, survole « %s » et appuie sur F8." % s["name"])

        btns = ttk.Frame(body)
        btns.grid(row=row[0], column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="Annuler", command=win.destroy).pack(side="right")
        ttk.Button(btns, text="OK", command=ok).pack(side="right", padx=(0, 6))
        win.bind("<Return>", lambda e: ok())
        win.bind("<Escape>", lambda e: win.destroy())
        self.translate_tree(win)
        win.grab_set()
        win.focus_force()
        return "break"

    def capture_selected_step(self):
        i = self.selected()
        if i is None or self.steps[i]["type"] != "click":
            self.status.set("Sélectionne d'abord une étape « Clic sur … » dans la liste.")
            return
        self.capture = i
        self.status.set("Va dans le jeu, survole « %s » et appuie sur F8." % self.steps[i].get("name", "endroit"))

    def move_step(self, d):
        i = self.selected()
        if i is None or not 0 <= i + d < len(self.steps):
            return
        self.steps[i], self.steps[i + d] = self.steps[i + d], self.steps[i]
        self.refresh_steps(select=i + d)
        self.save()

    def delete_step(self):
        i = self.selected()
        if i is not None:
            self.delete_index(i)

    def delete_index(self, i):
        """Supprime une etape ; Ctrl+Z la remet."""
        if not 0 <= i < len(self.steps):
            return
        s = self.steps.pop(i)
        self._undo = (i, s)
        self.refresh_steps(select=min(i, len(self.steps) - 1))
        self.save()
        self.status.set("Étape %d supprimée (%s). Ctrl+Z pour la remettre." % (i + 1, step_label(s)))

    def right_delete(self, e):
        """Clic droit sur une etape de la liste = la supprimer."""
        if not self.steps:
            return "break"
        i = self.st_list.nearest(e.y)
        box = self.st_list.bbox(i)
        if box and box[1] <= e.y <= box[1] + box[3]:
            self.delete_index(i)
        return "break"

    def undo_delete(self, e=None):
        if not self._undo:
            return
        i, s = self._undo
        self._undo = None
        i = min(i, len(self.steps))
        self.steps.insert(i, s)
        self.refresh_steps(select=i)
        self.save()
        self.status.set("Étape %d remise." % (i + 1))
        if self.overlay:
            self.show_overlay()

    def reset_steps(self):
        if messagebox.askyesno("Cv2 Printer", tr("Remplacer tes étapes par l'exemple ?")):
            self.steps = default_steps()
            self.refresh_steps()
            self.save()

    # ---------- a faire / guide pas a pas / clics a l'ecran
    def missing_clicks(self):
        return [i for i, s in enumerate(self.steps) if s["type"] == "click" and s.get("x") is None]

    def refresh_todo(self):
        if not hasattr(self, "todo_v"):
            return
        guide = False
        if not self.colors:
            txt = "Colle la palette du site dans la case 1."
        elif self.missing_clicks():
            txt = "Montre où cliquer pour « %s »." % self.steps[self.missing_clicks()[0]].get("name", "endroit")
            guide = True
        else:
            txt = "Tout est prêt : clique « Tester sur la couleur 1 » en bas."
        self.todo_v.set(txt)
        self.guide_btn.config(state="normal" if guide and not self.guide else "disabled")

    def start_guide(self):
        if self.running or self.guide:
            return
        bg = "#0f1115"
        win = tk.Toplevel(self.root)
        win.title("Guide · Cv2 Printer")
        win.attributes("-topmost", True)
        win.resizable(False, False)
        win.configure(bg=bg)
        win.geometry("+%d+%d" % (max(0, win.winfo_screenwidth() - 540), 40))
        g = {"win": win, "step_v": tk.StringVar(), "text_v": tk.StringVar(), "pos_v": tk.StringVar()}
        tk.Label(win, textvariable=g["step_v"], bg=bg, fg="#7cc4ff", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        row = tk.Frame(win, bg=bg)
        row.pack(anchor="w", padx=16, fill="x")
        g["swatch"] = tk.Label(row, text="", width=3, bg=bg)
        g["swatch"].pack(side="left", padx=(0, 10), ipady=8)
        tk.Label(row, textvariable=g["text_v"], bg=bg, fg="#ffffff", font=("Segoe UI", 14, "bold"), wraplength=430, justify="left").pack(side="left")
        tk.Label(win, text="F8 = c'est ici   ·   F9 = arrêter le guide", bg=bg, fg="#ffd21f", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(win, textvariable=g["pos_v"], bg=bg, fg="#8b93a2", font=("Consolas", 9)).pack(anchor="w", padx=16, pady=(2, 4))
        ttk.Button(win, text="Arrêter le guide", command=lambda: self.close_guide("Guide arrêté.")).pack(anchor="e", padx=16, pady=(0, 12))
        win.protocol("WM_DELETE_WINDOW", lambda: self.close_guide("Guide arrêté."))
        self.guide = g
        self.guide_btn.config(state="disabled")
        self.track_mouse()
        self.guide_next()

    def track_mouse(self):
        if not self.guide:
            return
        x, y = cursor_pos()
        self.guide["pos_v"].set("Ta souris est en (%d, %d)" % (x, y))
        self.root.after(100, self.track_mouse)

    def guide_next(self):
        g = self.guide
        if not g:
            return
        missing = self.missing_clicks()
        if missing:
            i = missing[0]
            total = sum(1 for s in self.steps if s["type"] == "click")
            self.capture = i
            g["step_v"].set("CLIC  %d / %d" % (total - len(missing) + 1, total))
            g["text_v"].set("Mets la souris là où tu cliques pour « %s », puis appuie sur F8." % self.steps[i].get("name", "endroit"))
            g["swatch"].config(bg=g["win"].cget("bg"))
            return
        self.close_guide("C'est bon, tout est capturé. Clique « Montrer les clics à l'écran » pour vérifier, puis « Tester sur la couleur 1 ».")

    def close_guide(self, msg=""):
        g, self.guide = self.guide, None
        self.capture = None
        if g:
            g["win"].destroy()
        if msg:
            self.status.set(msg)
        self.refresh_todo()

    def show_overlay(self):
        """Affiche les clics par-dessus le jeu. On peut glisser chaque cercle pour deplacer le clic."""
        if self.overlay:
            self.close_overlay()
        pts = [(i, s) for i, s in enumerate(self.steps) if s["type"] == "click" and s.get("x") is not None]
        if not pts:
            self.status.set("Aucune position capturée pour l'instant.")
            return
        vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
        vw, vh = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
        key = "#010203"  # cette couleur devient transparente : le jeu reste visible et cliquable
        color = "#ff8a3d"
        ov = tk.Toplevel(self.root)
        ov.overrideredirect(True)
        ov.attributes("-topmost", True)
        ov.configure(bg=key)
        ov.attributes("-transparentcolor", key)
        ov.geometry("%dx%d+%d+%d" % (vw, vh, vx, vy))
        c = tk.Canvas(ov, bg=key, highlightthickness=0, width=vw, height=vh)
        c.pack()
        self.overlay = ov

        def label(x, y, text, outline, tags):
            t = c.create_text(x, y, text=text, fill="#ffffff", font=("Segoe UI", 11, "bold"), anchor="w", tags=tags)
            b = c.bbox(t)
            box = c.create_rectangle(b[0] - 6, b[1] - 3, b[2] + 6, b[3] + 3, fill="#111318", outline=outline, width=2, tags=tags)
            c.tag_lower(box, t)

        for i, s in pts:
            tags = ("step%d" % i, "drag")
            cx, cy = s["x"] - vx, s["y"] - vy
            c.create_oval(cx - 16, cy - 16, cx + 16, cy + 16, outline=color, width=4, tags=tags)
            c.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=color, outline="", tags=tags)  # poignee pleine
            label(cx + 22, cy, tr("Étape %d : %s" % (i + 1, s.get("name", "clic"))), color, tags)
        label(max(10, vw / 2 - 330), 30, tr("Glisse un cercle pour déplacer le clic  ·  clic droit = supprimer  ·  clique ici ou Échap pour fermer"), "#ffffff", ("close",))

        drag = {}

        def press(e):
            cur = c.find_withtag("current")
            tag = next((t for t in c.gettags(cur[0]) if t.startswith("step")), None) if cur else None
            if tag:
                drag.update(tag=tag, i=int(tag[4:]), x=e.x, y=e.y, dx=0, dy=0)
                ov.config(cursor="fleur")

        def motion(e):
            if drag:
                c.move(drag["tag"], e.x - drag["x"], e.y - drag["y"])
                drag["dx"] += e.x - drag["x"]
                drag["dy"] += e.y - drag["y"]
                drag["x"], drag["y"] = e.x, e.y

        def release(e):
            if drag:
                s = self.steps[drag["i"]]
                s["x"] += drag["dx"]
                s["y"] += drag["dy"]
                self.refresh_steps(select=drag["i"])
                self.save()
                self.status.set("« %s » déplacé en (%d, %d)." % (s.get("name", "clic"), s["x"], s["y"]))
                drag.clear()
                ov.config(cursor="")

        def right(e):
            cur = c.find_withtag("current")
            tag = next((t for t in c.gettags(cur[0]) if t.startswith("step")), None) if cur else None
            if tag:
                self.delete_index(int(tag[4:]))
                self.show_overlay()  # on redessine : les numeros des etapes ont change

        c.tag_bind("drag", "<ButtonPress-1>", press)
        c.tag_bind("drag", "<Button-3>", right)
        c.bind("<B1-Motion>", motion)
        c.bind("<ButtonRelease-1>", release)
        c.tag_bind("close", "<Button-1>", lambda e: self.close_overlay())
        ov.bind("<Escape>", lambda e: self.close_overlay())
        ov.focus_force()
        self.status.set("Glisse les cercles orange pour déplacer les clics. Échap ou F9 pour fermer.")

    def close_overlay(self):
        ov, self.overlay = self.overlay, None
        if ov:
            ov.destroy()

    # ---------- glisser les etapes dans la liste
    def drag_start(self, e):
        self._drag = self.st_list.nearest(e.y) if self.steps else None
        self._dragged = False

    def drag_motion(self, e):
        i = getattr(self, "_drag", None)
        if i is None:
            return
        j = self.st_list.nearest(e.y)
        if 0 <= j < len(self.steps) and j != i:
            self.steps.insert(j, self.steps.pop(i))
            self._drag, self._dragged = j, True
            self.st_list.config(cursor="fleur")
            self.refresh_steps(select=j)

    def drag_end(self, e):
        if getattr(self, "_dragged", False):
            self.save()
            self.status.set("Étape déplacée en position %d." % (self._drag + 1))
        self._drag, self._dragged = None, False
        self.st_list.config(cursor="")

    # ---------- F8 / F9 et messages du lanceur
    def poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "f8":
                    self.on_f8()
                elif kind in ("f6", "f7") and not self.running:
                    self.start(test=(kind == "f6"), hotkey=True)
                elif kind == "f9":
                    if self.running:
                        self.log("Arrêt demandé (F9).")
                    elif self.guide:
                        self.close_guide("Guide arrêté.")
                    if self.overlay:
                        self.close_overlay()
                elif kind == "status":
                    self.status.set(msg[1])
                elif kind == "log":
                    self.log(msg[1])
                elif kind == "done":
                    self.set_running(False)
                    self.status.set(msg[1])
                    self.log(msg[1])
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def on_f8(self):
        if self.running or self.capture is None:
            return
        x, y = cursor_pos()
        i = self.capture
        self.capture = None
        if 0 <= i < len(self.steps) and self.steps[i]["type"] == "click":
            self.steps[i]["x"], self.steps[i]["y"] = x, y
            self.refresh_steps(select=i)
            self.status.set("Position de « %s » capturée : (%d, %d)." % (self.steps[i].get("name", "endroit"), x, y))
        self.save()
        if self.guide:
            self.guide_next()

    def log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", time.strftime("[%H:%M:%S] ") + tr(text) + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ---------- lancement
    def check(self, test):
        if not self.colors:
            return None, "Colle d'abord la palette (bouton « Copier la palette » sur le site)."
        if not self.steps:
            return None, "Ajoute au moins une étape."
        missing = [str(i + 1) for i, s in enumerate(self.steps) if s["type"] == "click" and s.get("x") is None]
        if missing:
            return None, "Il manque la position des étapes : %s. Sélectionne-les et clique « Capturer la position (F8) »." % ", ".join(missing)
        for i, s in enumerate(self.steps):
            if s["type"] == "key":
                try:
                    parse_combo(s.get("key", ""))
                except ValueError as e:
                    return None, "Étape %d : %s" % (i + 1, e)
        return (1 if test else len(self.colors)), ""

    def start(self, test=False, hotkey=False):
        """hotkey=True : lance depuis le jeu avec F6/F7, sans compte a rebours."""
        if self.running:
            return
        n, msg = self.check(test)
        if not n:
            if msg and hotkey:  # la fenetre est sans doute cachee derriere le jeu
                self.status.set(msg)
                self.log(msg)
            elif msg:
                messagebox.showwarning("Cv2 Printer", tr(msg))
            return
        if self.guide:
            self.close_guide()
        if self.overlay:
            self.close_overlay()
        self.capture = None
        try:
            opts = {"pause": max(0.0, float(self.pause_v.get())), "countdown": 0 if hotkey else max(0, int(self.count_v.get())),
                    "delay": 0.4 if hotkey else 0, "paste": "Ctrl+V" in self.method_v.get(), "dry": self.dry_v.get()}
        except (tk.TclError, ValueError):
            messagebox.showwarning("Cv2 Printer", tr("La pause ou le compte à rebours n'est pas un nombre."))
            return
        if hotkey:
            self.log("Lancé avec %s." % ("F6 (couleur 1)" if test else "F7 (toutes les couleurs)"))
        self.stop.clear()
        self.set_running(True)
        threading.Thread(target=self.job, args=(n, opts, [dict(s) for s in self.steps], list(self.colors)), daemon=True).start()

    def set_running(self, on):
        self.running = on
        self.test_btn.config(state="disabled" if on else "normal")
        self.run_btn.config(state="disabled" if on else "normal")
        self.stop_btn.config(state="normal" if on else "disabled")

    def job(self, n, o, steps, colors):
        q, stop = self.q, self.stop
        try:
            for t in range(o["countdown"], 0, -1):
                q.put(("status", "Départ dans %d… Clique dans le jeu. (F9 = arrêt)" % t))
                if stop.wait(1):
                    return q.put(("done", "Arrêté avant le départ."))
            if o.get("delay") and stop.wait(o["delay"]):  # laisse le temps de relacher F6/F7
                return q.put(("done", "Arrêté avant le départ."))
            for i in range(n):
                ch, col = colors[i]
                q.put(("status", "Couleur %d/%d%s : #%s" % (i + 1, n, " (caractère %s)" % ch if ch else "", _hex(col))))
                actions = plan_for(steps, col)
                for a in actions:
                    if stop.is_set() or (not o["dry"] and in_corner()):
                        return q.put(("done", "Arrêté à la couleur %d." % (i + 1)))
                    if o["dry"]:
                        q.put(("log", "%d : %s" % (i + 1, describe(a))))
                        continue
                    if a[0] == "wait":
                        if stop.wait(a[1]):
                            return q.put(("done", "Arrêté à la couleur %d." % (i + 1)))
                        continue
                    if a[0] == "click":
                        click(a[1], a[2], a[3], a[4])
                    elif a[0] == "text":
                        (paste_text if o["paste"] else type_text)(a[1])
                    elif a[0] == "key":
                        press_combo(parse_combo(a[1]), a[2])
                    if stop.wait(o["pause"]):
                        return q.put(("done", "Arrêté à la couleur %d." % (i + 1)))
            q.put(("done", "Fini : %d couleur%s faite%s%s." % (n, "s" if n > 1 else "", "s" if n > 1 else "", " (essai à blanc)" if o["dry"] else "")))
        except Exception as e:  # on remonte l'erreur dans la fenetre
            q.put(("done", "Erreur : %s" % e))

    # ---------- sauvegarde
    def save(self):
        data = {"palette": self.pal_text.get("1.0", "end-1c"), "steps": self.steps}
        try:
            data.update(pause=float(self.pause_v.get()), countdown=int(self.count_v.get()),
                        method="paste" if "Ctrl+V" in self.method_v.get() else "type")
        except (tk.TclError, ValueError, AttributeError):
            pass
        data["lang"] = LANG
        try:
            with open(CONFIG, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
        except OSError:
            pass

    def on_close(self):
        self.stop.set()
        self.save()
        self.root.destroy()


def main():
    if not IS_WIN:
        print("Ce script marche seulement sous Windows.")
        return 1
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # positions exactes meme avec le zoom Windows
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()
    App().root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
