# Copyright 2025 Rainer Schmitz
#
# Lizenziert unter der Apache License, Version 2.0 (die "Lizenz");
# Du darfst diese Datei nur gemäß den Bedingungen der Lizenz nutzen.
# Eine Kopie der Lizenz findest du unter
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Sofern nicht durch anwendbares Recht erforderlich oder schriftlich vereinbart,
# wird die Software ohne Gewährleistung jeglicher Art bereitgestellt,
# entweder ausdrücklich oder stillschweigend, einschließlich, aber nicht beschränkt
# auf die Gewährleistungen der Marktgängigkeit, der Eignung für einen bestimmten Zweck
# und der Nichtverletzung von Rechten. Weitere Informationen findest du in der Lizenz.
#
# Weitere Informationen findest du im GitHub-Repository:
# https://github.com/rain874/ont-SNCheck
__version__ = "1.0.0"

import tkinter as tk
from tkinter import messagebox
import re
import webbrowser
import os
import sys


class DataValidatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ontSNCheck - Formatvalidierung")
        self.root.geometry("400x300")  # Höhe etwas vergrößert

        # Icon setzen
        # Prüfen, ob das Script als EXE läuft (PyInstaller erstellt dann eine "frozen" App)
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS ist ein temporärer Ordner, den PyInstaller erstellt,
            # um eingebundene Dateien (z.B. dein icon.ico) verfügbar zu machen
            base_path = sys._MEIPASS
        else:
            # Wenn das Script normal in Python läuft, nutzen wir den aktuellen Ordner
            base_path = os.path.abspath(".")

        # Pfad zum Icon erstellen
        # os.path.join sorgt dafür, dass der Pfad plattformübergreifend korrekt zusammengesetzt wird
        icon_path = os.path.join(base_path, "icon.ico")

        # Icon setzen
        try:
            # iconbitmap() setzt das Fenster-Icon auf die .ico Datei
            self.root.iconbitmap(icon_path)
        except Exception as e:
            # Falls etwas schiefgeht (z.B. falscher Pfad), wird eine Meldung in der Konsole angezeigt
            print(f"Icon konnte nicht geladen werden: {e}")


        # StringVars
        self.typ_var = tk.StringVar()
        self.sn_var = tk.StringVar()
        self.modem_id_var = tk.StringVar()
        self.cwmp_var = tk.StringVar()

        # Entry-Widgets speichern
        self.entries = {}

        # Trace für Validierung
        for var in (self.typ_var, self.sn_var, self.modem_id_var, self.cwmp_var):
            var.trace_add("write", self.validate_all)

        # Widgets erstellen
        self.create_widgets()

        # Menüleiste erstellen
        self.create_menu()

        # Formatierungs-Traces erst nach Erstellung der Widgets setzen
        self.setup_formatting_traces()

        self.validate_all()

    # ---------------------------------------------------
    # Menüleiste
    # ---------------------------------------------------
    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        # --- GitHub ---
        github_menu = tk.Menu(menu_bar, tearoff=0)
        github_menu.add_command(
            label="Projekt auf GitHub öffnen",
            command=lambda: webbrowser.open("https://github.com/rain874/ont-SNCheck")
        )
        menu_bar.add_cascade(label="GitHub", menu=github_menu)

        # --- Hilfe ---
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(
            label="Hilfe anzeigen",
            command=lambda: messagebox.showinfo(
                "Hilfe",
                "Das Tool führt eine reine Formatvalidierung für die Fritz!Box durch. Es erfolgt keine Validierung durch AVM selbst. Überprüft werden ausschließlich der Gerätetyp, die Seriennummer, die Modem-ID sowie die CWMP-Daten auf korrektes Format\n"
            )
        )
        menu_bar.add_cascade(label="Hilfe", menu=help_menu)

        # --- About ---
        about_menu = tk.Menu(menu_bar, tearoff=0)
        about_menu.add_command(
            label="Über dieses Programm",
            command=lambda: messagebox.showinfo(
                "About",
                "ontSNCheck – Formatvalidierung\n"
                "Version 1.0.0\n"
                "Autor: Rainer Schmitz\n"
                "Lizenz: Apache-2.0 license"
            )
        )
        menu_bar.add_cascade(label="About", menu=about_menu)

        self.root.config(menu=menu_bar)

    # ---------------------------------------------------

    def setup_formatting_traces(self):
        self.sn_var.trace_add("write", lambda *args: self.safe_trace_call(self.format_sn, 'sn'))
        self.cwmp_var.trace_add("write", lambda *args: self.safe_trace_call(self.format_cwmp, 'cwmp'))
        self.modem_id_var.trace_add("write", lambda *args: self.safe_trace_call(self.format_modem_id, 'modem_id'))

    def safe_trace_call(self, func, widget_key):
        try:
            entry_widget = self.entries[widget_key]
            func(entry_widget)
        except tk.TclError:
            pass
        except KeyError:
            pass

    def create_widgets(self):
        labels = ["Typ:", "SN:", "ModemID:", "CWMP:"]
        vars_ = [self.typ_var, self.sn_var, self.modem_id_var, self.cwmp_var]

        self.status_labels = []
        self.hint_labels = []

        for i, (text, var) in enumerate(zip(labels, vars_)):
            tk.Label(self.root, text=text, anchor="w", width=10).grid(row=i*2, column=0, padx=10, pady=5, sticky="w")
            entry = tk.Entry(self.root, textvariable=var, width=35)
            entry.grid(row=i*2, column=1, padx=5, pady=5, sticky="w")
            self.entries[text.rstrip(':').lower()] = entry

            status = tk.Label(self.root, text="❌", fg="red")
            status.grid(row=i*2, column=2, padx=10, pady=5)
            self.status_labels.append(status)

            hint = tk.Label(self.root, text="", fg="gray", font=("Arial", 8), anchor="w", width=40)
            hint.grid(row=i*2+1, column=1, padx=10, pady=(0, 5), sticky="w", columnspan=2)
            self.hint_labels.append(hint)

        button_frame = tk.Frame(self.root)
        button_frame.grid(row=8, column=0, columnspan=3, pady=15)

        self.copy_btn = tk.Button(
            button_frame,
            text="In Zwischenablage kopieren",
            command=self.copy_to_clipboard,
            state="disabled",
            width=22
        )
        self.copy_btn.grid(row=0, column=0, padx=5)

        self.clear_btn = tk.Button(
            button_frame,
            text="Felder leeren",
            command=self.clear_all_fields,
            width=15
        )
        self.clear_btn.grid(row=0, column=1, padx=5)

    def clear_all_fields(self):
        self.typ_var.set("")
        self.sn_var.set("")
        self.modem_id_var.set("")
        self.cwmp_var.set("")

        for label in self.status_labels:
            label.config(text="❌", fg="red")

        for label in self.hint_labels:
            label.config(text="", fg="gray")

        self.copy_btn.config(state="disabled")

    def validate_typ(self, value):
        return bool(re.fullmatch(r'\d{4}', value))

    def validate_modem_id(self, value):
        return bool(re.fullmatch(r'AVMG[A-Za-z0-9]{8}', value))

    def validate_sn(self, value):
        clean = value.replace(".", "")
        return bool(re.fullmatch(r'[A-Za-z]\d{14}', clean))

    def validate_cwmp(self, value):
        clean = value.replace("-", "")
        return bool(re.fullmatch(r'000[A-Za-z0-9]{15}', clean))

    def validate_all(self, *args):
        v_typ = self.validate_typ(self.typ_var.get())
        v_sn = self.validate_sn(self.sn_var.get())
        v_modem = self.validate_modem_id(self.modem_id_var.get())
        v_cwmp = self.validate_cwmp(self.cwmp_var.get())

        results = [v_typ, v_sn, v_modem, v_cwmp]

        for label, valid in zip(self.status_labels, results):
            label.config(text="✅" if valid else "❌", fg="green" if valid else "red")

        self.copy_btn.config(state="normal" if all(results) else "disabled")

        self.update_hints()

    def update_hints(self):
        typ_val = self.typ_var.get()
        hint_label = self.hint_labels[0]
        if len(typ_val) != 4 and len(typ_val) > 0:
            hint_label.config(text="4-stellige Zahl erforderlich", fg="red")
        elif len(typ_val) == 4 and not self.validate_typ(typ_val):
            hint_label.config(text="Ungültige Zahl", fg="red")
        else:
            hint_label.config(text="", fg="gray")

        sn_val = self.sn_var.get()
        clean_sn = sn_val.replace(".", "")
        hint_label = self.hint_labels[1]
        if len(clean_sn) > 15:
            hint_label.config(text="Max. 15 Zeichen (1 Buchstabe + 14 Ziffern)", fg="red")
        elif len(clean_sn) < 15 and len(clean_sn) > 0:
            hint_label.config(text=f"{15 - len(clean_sn)} Zeichen fehlen", fg="gray")
        elif len(clean_sn) == 15 and not self.validate_sn(sn_val):
            hint_label.config(text="Ungültiges SN-Format", fg="red")
        else:
            hint_label.config(text="", fg="gray")

        modem_val = self.modem_id_var.get()
        clean_modem = re.sub(r'[^A-Za-z0-9]', '', modem_val)
        hint_label = self.hint_labels[2]
        if len(clean_modem) > 12:
            hint_label.config(text="Max. 12 Zeichen (AVMG + 8)", fg="red")
        elif not clean_modem.startswith("AVMG") and len(clean_modem) > 0:
            hint_label.config(text="Muss mit AVMG beginnen", fg="red")
        elif len(clean_modem) < 12 and len(clean_modem) > 0:
            hint_label.config(text=f"{12 - len(clean_modem)} Zeichen fehlen", fg="gray")
        elif len(clean_modem) == 12 and not self.validate_modem_id(modem_val):
            hint_label.config(text="Ungültige ModemID", fg="red")
        else:
            hint_label.config(text="", fg="gray")

        cwmp_val = self.cwmp_var.get()
        clean_cwmp = cwmp_val.replace("-", "")
        hint_label = self.hint_labels[3]
        if len(clean_cwmp) > 18:
            hint_label.config(text="Max. 18 Zeichen", fg="red")
        elif len(clean_cwmp) < 18 and len(clean_cwmp) > 0:
            hint_label.config(text=f"{18 - len(clean_cwmp)} Zeichen fehlen", fg="gray")
        elif len(clean_cwmp) == 18 and not self.validate_cwmp(cwmp_val):
            hint_label.config(text="Ungültiges CWMP-Format", fg="red")
        else:
            hint_label.config(text="", fg="gray")

    def format_modem_id(self, entry_widget, *args):
        value = self.modem_id_var.get()
        clean = re.sub(r'[^A-Za-z0-9]', '', value)

        if len(clean) > 12:
            clean = clean[:12]

        if len(clean) >= 4:
            clean = "AVMG" + clean[4:]
        elif len(clean) < 4:
            clean = "AVMG"[:len(clean)]

        clean = clean.upper()

        if value != clean:
            self.modem_id_var.set(clean)

    def format_sn(self, entry_widget, *args):
        original_value = self.sn_var.get()
        clean = re.sub(r'[^A-Za-z0-9]', '', original_value)

        if len(clean) > 15:
            clean = clean[:15]

        if len(clean) >= 2:
            letter = clean[0]
            digits = clean[1:]

            parts = []
            indices = [0, 3, 6, 8, 11]
            for i in range(len(indices)):
                start = indices[i]
                end = indices[i + 1] if i + 1 < len(indices) else len(digits)
                if start < len(digits):
                    parts.append(digits[start:end])

            formatted = letter + parts[0] + "." + ".".join(parts[1:])
        else:
            formatted = clean

        formatted = formatted.upper()

        if original_value != formatted:
            self.sn_var.set(formatted)
            self.root.after_idle(lambda: self.set_cursor_to_end(entry_widget))

    def format_cwmp(self, entry_widget, *args):
        original_value = self.cwmp_var.get()
        clean = re.sub(r'[^A-Za-z0-9]', '', original_value)

        if len(clean) > 18:
            clean = clean[:18]

        if len(clean) >= 6:
            formatted = clean[:6] + "-" + clean[6:]
        else:
            formatted = clean

        formatted = formatted.upper()

        if original_value != formatted:
            self.cwmp_var.set(formatted)
            self.root.after_idle(lambda: self.set_cursor_to_end(entry_widget))

    def set_cursor_to_end(self, entry_widget):
        entry_widget.icursor(tk.END)
        entry_widget.xview_moveto(1)

    def copy_to_clipboard(self):
        output = (
            f"Typ: {self.typ_var.get()}\n"
            f"SN: {self.sn_var.get()}\n"
            f"ModemID: {self.modem_id_var.get()}\n"
            f"CWMP: {self.cwmp_var.get()}"
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(output)
        self.root.update()


if __name__ == "__main__":
    root = tk.Tk()
    app = DataValidatorApp(root)
    root.mainloop()

