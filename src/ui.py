import threading
try:
    import breach_checker as breach
except Exception:
    breach = None

import tkinter as tk
from tkinter import ttk, messagebox
from scorer_logic import compute_score
from entropy import format_duration
from password_generator import generate_password

# NEW: import the passphrase generator module
try:
    import passphrase_generator as pgen
except Exception as e:
    print("Passphrase module load error:", e)
    pgen = None

def show_about():
    messagebox.showinfo(
        "About PSBC",
        "Password Strength & Breach Checker (PSBC)\n"
        "Version 1.0.0\n\n"
        "Made by Walter Tairo (Cybercyphertz)\n"
        "Privacy-first, offline strength analysis with optional safe breach checks."
    )


def create_main_window():
    root = tk.Tk()
    # after: root = tk.Tk()
    if pgen is None:
        messagebox.showerror(
            "Setup error",
            "passphrase_generator.py not found or failed to import.\n\n"
            "Make sure the file is in the SAME folder as app.py and ui.py."
    )

    root.title("PSBC-Password Strength & Breach Checker")
    root.geometry("640x800")
    root.resizable(True, True)

    menubar = tk.Menu(root)
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="About", command=show_about)
    menubar.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menubar)

    # ---- styles ----
    score_style = ttk.Style(root)
    try:
        # keep current theme
        score_style.theme_use(score_style.theme_use())
    except Exception:
        pass
    score_style.configure("Weak.Horizontal.TProgressbar",   background="#e06666")
    score_style.configure("Med.Horizontal.TProgressbar",    background="#ffd966")
    score_style.configure("Strong.Horizontal.TProgressbar", background="#93c47d")

    # ---- container ----
    # ---- scrollable container (replaces the old container = ttk.Frame...) ----
    outer = ttk.Frame(root)
    outer.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer, highlightthickness=0)
    vbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)

    vbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # This is the frame you’ll keep using below (same name as before)
    container = ttk.Frame(canvas, padding=16)
    container_id = canvas.create_window((0, 0), window=container, anchor="nw")

    def _on_container_configure(event):
        # Update scrollregion to fit inner frame
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        # Keep inner frame the same width as the canvas (responsive)
        canvas.itemconfig(container_id, width=event.width)

    container.bind("<Configure>", _on_container_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    # Mouse wheel support (Windows/macOS)
    def _on_mousewheel(event):
        # On Windows/macOS, event.delta is a multiple of 120
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Linux (X11) often uses Button-4/5
    def _on_linux_scroll_up(event): canvas.yview_scroll(-3, "units")
    def _on_linux_scroll_down(event): canvas.yview_scroll(3, "units")

    # Activate wheel scrolling when pointer is over the canvas
    def _bind_wheel(_):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)        # Win/macOS
        canvas.bind_all("<Button-4>", _on_linux_scroll_up)     # Linux
        canvas.bind_all("<Button-5>", _on_linux_scroll_down)   # Linux

    def _unbind_wheel(_):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _bind_wheel)
    canvas.bind("<Leave>", _unbind_wheel)


    title_label = ttk.Label(
        container,
        text="Password Checker",
        font=("Segoe UI", 14, "bold")
    )
    title_label.pack(anchor="w", pady=(0, 8))

    # ---- Input row (with eye press-and-hold) ----
    password_var = tk.StringVar()

    entry_row = ttk.Frame(container)
    entry_row.pack(anchor="w", pady=(0, 6), fill="x")

    entry = ttk.Entry(
        entry_row,
        textvariable=password_var,
        show="•",
        width=56,
        font=("Segoe UI", 12)
    )
    entry.pack(side="left", fill="x", expand=True)

    # Eye button (press to reveal, release to hide)
    def _peek_press(_):
        entry.config(show="")       # reveal while pressed

    def _peek_release(_):
        entry.config(show="•")      # hide when released / pointer leaves

    eye_btn = ttk.Button(entry_row, text="👁", width=2, style="Toolbutton")
    # Make the eye look "inside" the entry by overlaying it on the right
    eye_btn.place(in_=entry, relx=1.0, x=-4, rely=0.5, anchor="e")
    def _reposition_eye(_=None):
        # keep it pinned at the right when resized
        eye_btn.place_configure(in_=entry, relx=1.0, x=-4, rely=0.5, anchor="e")
    entry.bind("<Configure>", _reposition_eye)
    entry_row.bind("<Configure>", _reposition_eye)

    eye_btn.bind("<ButtonPress-1>", _peek_press)
    eye_btn.bind("<ButtonRelease-1>", _peek_release)
    eye_btn.bind("<Leave>", _peek_release)

    entry.focus()


    # ---- random password generator controls (existing) ----
    gen_frame = ttk.LabelFrame(container, text="Generate a strong password", padding=10)
    gen_frame.pack(anchor="w", fill="x", pady=(6, 6))

    length_var = tk.StringVar(value="16")
    symbols_var = tk.IntVar(value=1)

    rowg1 = ttk.Frame(gen_frame); rowg1.pack(anchor="w", pady=(0, 4))
    ttk.Label(rowg1, text="Length (12–24): ").pack(side="left")
    length_spin = ttk.Spinbox(rowg1, from_=12, to=24, textvariable=length_var, width=5)
    length_spin.pack(side="left", padx=(4, 12))
    symbols_check = ttk.Checkbutton(rowg1, text="Include symbols", variable=symbols_var)
    symbols_check.pack(side="left")

    # forward declarations (labels we update later)
    length_value_label = ttk.Label(container, text="0")
    score_bar = ttk.Progressbar(container, orient="horizontal", length=520, mode="determinate", maximum=100)
    score_label = ttk.Label(container, text="Score: 0 (Weak)")

    entropy_frame = ttk.LabelFrame(container, text="Strength Details", padding=10)
    row1 = ttk.Frame(entropy_frame)
    entropy_value_label = ttk.Label(row1, text="0.0 bits")
    row2 = ttk.Frame(entropy_frame)
    crack1_value_label = ttk.Label(row2, text="—")
    row3 = ttk.Frame(entropy_frame)
    crack2_value_label = ttk.Label(row3, text="—")
    status_label = ttk.Label(container, text="Type a password…", font=("Segoe UI", 10))
    tips_var = tk.StringVar(value="")
    tips_label = ttk.Label(container, textvariable=tips_var, justify="left")

    # ---- actions (existing) ----
    def set_bar_style(level: str):
        if level == "weak":
            score_bar.configure(style="Weak.Horizontal.TProgressbar")
        elif level == "medium":
            score_bar.configure(style="Med.Horizontal.TProgressbar")
        else:
            score_bar.configure(style="Strong.Horizontal.TProgressbar")

    def update_view(pwd: str):
        length_value_label.config(text=str(len(pwd)))

        if len(pwd) == 0:
            status_label.config(text="Type a password…")
            score_bar["value"] = 0
            score_label.config(text="Score: 0 (Weak)")
            tips_var.set("")
            entropy_value_label.config(text="0.0 bits")
            crack1_value_label.config(text="—")
            crack2_value_label.config(text="—")
            set_bar_style("weak")
            return

        score, label, reasons, bits, t1, t2 = compute_score(pwd)
        score_bar["value"] = score
        score_label.config(text=f"Score: {score} ({label})")
        set_bar_style(label.lower())

        entropy_value_label.config(text=f"{bits:.1f} bits")
        crack1_value_label.config(text=f"{format_duration(t1)} @ 1e9/s")
        crack2_value_label.config(text=f"{format_duration(t2)} @ 1e12/s")

        if len(reasons) == 0:
            status_label.config(text="Looks okay so far")
            tips_var.set("")
        else:
            status_label.config(text="Suggestions:")
            tips_var.set(" • " + "\n • ".join(reasons))

    _clipboard_timer_id = {"id": None}  # avoid nonlocal

    def clear_clipboard():
        try:
            root.clipboard_clear()
            status_label.config(text="Clipboard cleared.")
        except Exception:
            pass

    def copy_to_clipboard():
        pwd = password_var.get()
        if not pwd:
            status_label.config(text="Nothing to copy.")
            return
        root.clipboard_clear()
        root.clipboard_append(pwd)
        status_label.config(text="Copied to clipboard (auto‑clears in 20s).")
        if _clipboard_timer_id["id"] is not None:
            root.after_cancel(_clipboard_timer_id["id"])
        _clipboard_timer_id["id"] = root.after(20000, clear_clipboard)

    def on_generate():
        try:
            length = int(length_var.get())
        except Exception:
            length = 16
        include_symbols = symbols_var.get() == 1
        pwd = generate_password(length, include_symbols)
        password_var.set(pwd)
        update_view(pwd)

    def on_key_release(event=None):
        update_view(password_var.get())
        if auto_check_var.get():
            _schedule_auto_breach()

    # second row of generator controls (buttons)
    rowg2 = ttk.Frame(gen_frame); rowg2.pack(anchor="w", pady=(4, 0))
    gen_btn = ttk.Button(rowg2, text="Generate Strong", command=on_generate)
    gen_btn.pack(side="left", padx=(0, 8))
    copy_btn = ttk.Button(rowg2, text="Copy (auto‑clear 20s)", command=copy_to_clipboard)
    copy_btn.pack(side="left")

    # ---- length row ----
    length_row = ttk.Frame(container)
    length_row.pack(anchor="w")
    ttk.Label(length_row, text="Length: ").pack(side="left")
    length_value_label.pack(side="left")

    # ---- score bar + label ----
    score_bar.pack(anchor="w", pady=(12, 4))
    score_label.pack(anchor="w")

    # ---- entropy + crack time panel ----
    entropy_frame.pack(anchor="w", fill="x", pady=(12, 4))
    row1.pack(anchor="w")
    ttk.Label(row1, text="Entropy: ").pack(side="left")
    entropy_value_label.pack(side="left")
    row2.pack(anchor="w", pady=(4, 0))
    crack1_value_label.pack(side="left")
    row3.pack(anchor="w", pady=(2, 0))
    crack2_value_label.pack(side="left")

    status_label.pack(anchor="w", pady=(12, 6))
    tips_label.pack(anchor="w")

    entry.bind("<KeyRelease>", on_key_release)
    set_bar_style("weak")

    # ==============================
    # NEW: Diceware-style Passphrase
    # ==============================
    pass_frame = ttk.LabelFrame(container, text="Generate a memorable passphrase (Diceware style)", padding=10)
    pass_frame.pack(anchor="w", fill="x", pady=(12, 6))

    # Controls
    pr = ttk.Frame(pass_frame); pr.pack(anchor="w", pady=(0, 4), fill="x")
    ttk.Label(pr, text="Words (3–10): ").pack(side="left")
    pp_words_var = tk.IntVar(value=4)
    ttk.Spinbox(pr, from_=3, to=10, textvariable=pp_words_var, width=5).pack(side="left", padx=(4, 12))

    ttk.Label(pr, text="Separator: ").pack(side="left")
    pp_sep_var = tk.StringVar(value="-")
    ttk.Entry(pr, textvariable=pp_sep_var, width=6).pack(side="left", padx=(4, 12))

    pp_capital_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(pr, text="Capitalize", variable=pp_capital_var).pack(side="left")

    pr2 = ttk.Frame(pass_frame); pr2.pack(anchor="w", pady=(4, 4), fill="x")
    pp_digit_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(pr2, text="Append one random digit", variable=pp_digit_var).pack(side="left", padx=(0, 12))
    pp_symbol_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(pr2, text="Append one random symbol", variable=pp_symbol_var).pack(side="left")

    # Output
    pp_out = tk.Text(pass_frame, height=3, width=60, wrap="word")
    pp_out.pack(anchor="w", fill="x", padx=2, pady=(6, 4))

    pp_entropy_label = ttk.Label(pass_frame, text="Entropy: –")
    pp_entropy_label.pack(anchor="w")

    # Actions container + "Send to checker" checkbox
    pr3 = ttk.Frame(pass_frame)
    pr3.pack(anchor="w", pady=(6, 0))

    # Checkbox must be defined before the generate function so it is in scope
    pp_send_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(pr3, text="Send to checker", variable=pp_send_var).pack(side="left", padx=(0, 12))

    # Actions
    def on_generate_passphrase():
        phrase = None  # ensure defined even if an error happens
        try:
            if pgen is None:
                messagebox.showerror(
                    "Error",
                    "passphrase_generator.py is missing or failed to import.\n"
                    "Put it in the same folder as app.py and ui.py."
                )
                return

            # Read UI options safely
            try:
                k = int(pp_words_var.get())
            except Exception:
                k = 4
            if k < 3:  # keep reasonable strength
                k = 3
            elif k > 10:
                k = 10

            sep = (pp_sep_var.get() or "-")

            # Generate the passphrase
            phrase = pgen.generate_passphrase(
                num_words=k,
                separator=sep,
                capitalize=pp_capital_var.get(),
                add_number=pp_digit_var.get(),
                add_symbol=pp_symbol_var.get(),
            )

            # Show it in the output box
            pp_out.config(state="normal")
            pp_out.delete("1.0", "end")
            pp_out.insert("1.0", phrase)

            # Update entropy label
            wl = pgen.get_wordlist_size()
            bits = pgen.estimate_entropy_bits(
                num_words=k,
                add_number=pp_digit_var.get(),
                add_symbol=pp_symbol_var.get(),
                wordlist_size=wl
            )
            pp_entropy_label.config(text=f"Entropy: ~{bits} bits (wordlist size {wl})")

            # Optionally send to the main checker
            if pp_send_var.get():
                password_var.set(phrase)
                update_view(phrase)

            status_label.config(text="Passphrase generated.")
        except Exception as e:
            # Do NOT reference 'phrase' here; it may be None
            messagebox.showerror("Passphrase error", f"{type(e).__name__}: {e}")



    def on_copy_passphrase():
        phrase = pp_out.get("1.0", "end").strip()
        if not phrase:
            status_label.config(text="Nothing to copy.")
            return
        root.clipboard_clear()
        root.clipboard_append(phrase)
        status_label.config(text="Passphrase copied to clipboard")

    ttk.Button(pr3, text="Generate Passphrase", command=on_generate_passphrase).pack(side="left", padx=(0, 8))
    ttk.Button(pr3, text="Copy", command=on_copy_passphrase).pack(side="left")

    # ==============================
        # ==============================
    # Breach check (Have I Been Pwned)
    # ==============================
    try:
        breach_frame = ttk.LabelFrame(container, text="Breach check (Have I Been Pwned)", padding=10)
        breach_frame.pack(anchor="w", fill="x", pady=(12, 6))

        breach_status_var = tk.StringVar(value="Ready")
        breach_lbl = ttk.Label(breach_frame, textvariable=breach_status_var)
        breach_lbl.pack(anchor="w")

        auto_check_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            breach_frame,
            text="Auto-check while typing (debounced)",
            variable=auto_check_var
        ).pack(anchor="w", pady=(6, 4))

        breach_btn = ttk.Button(breach_frame, text="Check breach (HIBP)")
        breach_btn.pack(anchor="e")

        _breach_after = {"id": None}

        def _set_breach(text: str, color: str = "#444"):
            breach_status_var.set(text)
            try:
                breach_lbl.configure(foreground=color)
            except Exception:
                pass

        def _breach_worker(pwd_snapshot: str):
            if breach is None:
                root.after(0, lambda: _set_breach("Module missing: breach_checker.py", "#b00020"))
                root.after(0, lambda: breach_btn.config(state="normal"))
                return
            result = breach.check_pwned_password(pwd_snapshot)

            def finish():
                breach_btn.config(state="normal")
                if not result["ok"]:
                    err = result.get("error", "error")
                    if isinstance(err, str) and err.startswith("rate_limited:"):
                        secs = err.split(":")[1]
                        _set_breach(f"Rate limited. Retry after ~{secs}s.", "#b00020")
                    elif err == "network_error":
                        _set_breach("Network error. Check connection and try again.", "#b00020")
                    else:
                        _set_breach("Error checking password.", "#b00020")
                    return
                if result["found"]:
                    _set_breach(f"⚠️ PWNED: seen {result['count']:,} times.", "#b00020")
                else:
                    _set_breach("✅ Not found in HIBP.", "#2b8a3e")

            root.after(0, finish)

        def start_breach_check(event=None):
            pwd = password_var.get()
            if not pwd:
                _set_breach("Enter a password first.", "#666")
                return
            breach_btn.config(state="disabled")
            _set_breach("Checking…", "#666")
            threading.Thread(target=_breach_worker, args=(pwd,), daemon=True).start()

        breach_btn.config(command=start_breach_check)

        def _schedule_auto_breach():
            if not auto_check_var.get():
                return
            if _breach_after["id"]:
                root.after_cancel(_breach_after["id"])
            _breach_after["id"] = root.after(800, start_breach_check)

        # Re-bind the key handler so auto-check can call the scheduler safely
        entry.unbind("<KeyRelease>")
        def on_key_release(event=None):
            update_view(password_var.get())
            try:
                if auto_check_var.get():
                    _schedule_auto_breach()
            except Exception:
                pass
        entry.bind("<KeyRelease>", on_key_release)

    except Exception as e:
        ttk.Label(
            container,
            text=f"HIBP panel failed: {type(e).__name__}: {e}",
            foreground="#b00020"
        ).pack(anchor="w", pady=(6, 0))

    footer = tk.Label(
        root,
        text="Made by Walter Tairo (Cybercyphertz)",
        font=("Segoe UI", 8),
        fg="#777"
    )
    footer.pack(side="bottom", pady=4)



    return root
