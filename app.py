import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import json
import keyring
from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = Path.home() / ".md_converter_config.json"
KEYCHAIN_SERVICE = "AndysMDConversionTool"
KEYCHAIN_USER = "anthropic_api_key"


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}


def save_config(data):
    # Never write the API key to disk — it lives in Keychain only
    data.pop("api_key", None)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def load_api_key():
    try:
        return keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USER) or ""
    except Exception:
        return ""


def save_api_key(key):
    keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_USER, key)


def delete_api_key():
    try:
        keyring.delete_password(KEYCHAIN_SERVICE, KEYCHAIN_USER)
    except Exception:
        pass


# ── Custom widgets ────────────────────────────────────────────────────────────

class Divider(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=1, fg_color=("gray75", "gray35"), **kwargs)


class SectionLabel(ctk.CTkLabel):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text=text, font=ctk.CTkFont(size=13, weight="bold"), **kwargs)


# ── Welcome dialog (shown on first run) ───────────────────────────────────────

class WelcomeDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Welcome")
        self.geometry("560x640")
        self.resizable(False, False)
        self.grab_set()  # modal
        self.result = {"images_enabled": True}

        self.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray17"))
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="Welcome to\nAndy's MD Conversion Tool",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left"
        ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            hdr,
            text="Convert PowerPoint and PDF files into clean, structured Markdown.",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
            justify="left"
        ).grid(row=1, column=0, padx=24, pady=(0, 18), sticky="w")

        # Body
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        body.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # What it does
        ctk.CTkLabel(
            body, text="What this app does",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(4, 4))

        ctk.CTkLabel(
            body,
            text=(
                "Drop in any .pptx or .pdf file and the app converts it into a "
                "Markdown (.md) file — preserving the document title, slide or page "
                "numbers, headings, bullet points, tables, and speaker notes."
            ),
            font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray75"),
            wraplength=490,
            justify="left",
            anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        Divider(body).grid(row=2, column=0, sticky="ew", pady=6)

        # Image descriptions
        ctk.CTkLabel(
            body, text="AI-powered image descriptions (optional)",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).grid(row=3, column=0, sticky="w", pady=(4, 4))

        ctk.CTkLabel(
            body,
            text=(
                "When a slide or page contains an image, the app can use Claude AI "
                "(Anthropic's Haiku model) to automatically describe it — including "
                "extracting any text visible inside the image, describing charts and "
                "graphs, and summarizing diagrams.\n\n"
                "This makes your Markdown much more useful for LLMs, search, and "
                "accessibility — images become readable descriptions rather than "
                "silent gaps in the document."
            ),
            font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray75"),
            wraplength=490,
            justify="left",
            anchor="w"
        ).grid(row=4, column=0, sticky="w", pady=(0, 12))

        # Cost note
        cost_frame = ctk.CTkFrame(body, fg_color=("gray85", "gray22"), corner_radius=8)
        cost_frame.grid(row=5, column=0, sticky="ew", pady=(0, 12))
        cost_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cost_frame,
            text="💡  Cost & API key",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            cost_frame,
            text=(
                "Image descriptions use the Anthropic API (Claude Haiku), which requires "
                "a free account and a small per-use fee — typically fractions of a cent "
                "per image. You'll need your own API key.\n\n"
                "Get yours at:  console.anthropic.com  → API Keys"
            ),
            font=ctk.CTkFont(size=12),
            text_color=("gray35", "gray70"),
            wraplength=460,
            justify="left",
            anchor="w"
        ).grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")

        Divider(body).grid(row=6, column=0, sticky="ew", pady=8)

        # Toggle choice
        ctk.CTkLabel(
            body, text="How would you like to get started?",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).grid(row=7, column=0, sticky="w", pady=(4, 8))

        self.choice_var = ctk.StringVar(value="on")

        on_frame = ctk.CTkFrame(body, fg_color=("gray85", "gray22"), corner_radius=8)
        on_frame.grid(row=8, column=0, sticky="ew", pady=(0, 6))
        on_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkRadioButton(
            on_frame, text="", variable=self.choice_var, value="on", width=24
        ).grid(row=0, column=0, padx=(12, 6), pady=12)
        ctk.CTkLabel(
            on_frame,
            text="Enable AI image descriptions  (I have / will get an API key)",
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).grid(row=0, column=1, padx=(0, 14), pady=12, sticky="w")

        off_frame = ctk.CTkFrame(body, fg_color=("gray85", "gray22"), corner_radius=8)
        off_frame.grid(row=9, column=0, sticky="ew", pady=(0, 4))
        off_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkRadioButton(
            off_frame, text="", variable=self.choice_var, value="off", width=24
        ).grid(row=0, column=0, padx=(12, 6), pady=12)
        ctk.CTkLabel(
            off_frame,
            text="Skip image descriptions  (no API key needed — text only)",
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).grid(row=0, column=1, padx=(0, 14), pady=12, sticky="w")

        ctk.CTkLabel(
            body,
            text="You can change this at any time in the settings panel.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w"
        ).grid(row=10, column=0, sticky="w", pady=(6, 4))

        # Footer button
        ctk.CTkButton(
            self, text="Get Started →",
            height=42, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._confirm
        ).grid(row=2, column=0, padx=20, pady=(6, 20), sticky="ew")

        self.center_on(parent)

    def center_on(self, parent):
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w, h = 560, 640
        self.geometry(f"{w}x{h}+{px - w // 2}+{py - h // 2}")

    def _confirm(self):
        self.result["images_enabled"] = (self.choice_var.get() == "on")
        self.destroy()


# ── Main application ──────────────────────────────────────────────────────────

class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Andy's MD Conversion Tool")
        self.geometry("1000x740")
        self.minsize(860, 640)

        self.selected_files: list[str] = []
        self.file_checkboxes: list[ctk.BooleanVar] = []
        self.output_folder = ctk.StringVar()
        self.api_key_var = ctk.StringVar()
        self.overwrite_var = ctk.StringVar(value="ask")
        self.images_enabled = ctk.BooleanVar(value=True)
        self.converting = False

        cfg = load_config()
        self.api_key_var.set(load_api_key())
        if cfg.get("output_folder"):
            self.output_folder.set(cfg["output_folder"])
        if "images_enabled" in cfg:
            self.images_enabled.set(cfg["images_enabled"])

        self._build_ui()

        # Show welcome dialog on first run
        if not cfg.get("welcomed"):
            self.after(200, self._show_welcome)

    # ── Welcome dialog ────────────────────────────────────────────────────────

    def _show_welcome(self):
        dlg = WelcomeDialog(self)
        self.wait_window(dlg)
        enabled = dlg.result.get("images_enabled", True)
        self.images_enabled.set(enabled)
        self._update_api_section()

        cfg = load_config()
        cfg["welcomed"] = True
        cfg["images_enabled"] = enabled
        save_config(cfg)

    # ── UI layout ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._build_header()
        self._build_main()
        self._build_footer()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray17"))
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="Andy's MD Conversion Tool",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=24, pady=(16, 2), sticky="w")

        ctk.CTkLabel(
            hdr,
            text="Convert PowerPoint and PDF files into structured Markdown — with optional AI-powered image descriptions.",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65")
        ).grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=18, pady=14)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        self._build_file_panel(main)
        self._build_settings_panel(main)

    def _build_file_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(frame, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        toolbar.grid_columnconfigure(0, weight=1)

        SectionLabel(toolbar, text="Selected Files").grid(row=0, column=0, sticky="w")

        btns = ctk.CTkFrame(toolbar, fg_color="transparent")
        btns.grid(row=0, column=1)
        ctk.CTkButton(btns, text="+ Add Files", width=95, height=30,
                      command=self._add_files).grid(row=0, column=0, padx=2)
        ctk.CTkButton(btns, text="Remove", width=80, height=30,
                      fg_color=("gray60", "gray35"), hover_color=("gray50", "gray28"),
                      command=self._remove_selected).grid(row=0, column=1, padx=2)
        ctk.CTkButton(btns, text="Clear All", width=80, height=30,
                      fg_color=("gray60", "gray35"), hover_color=("gray50", "gray28"),
                      command=self._clear_files).grid(row=0, column=2, padx=2)

        self.file_list_frame = ctk.CTkScrollableFrame(frame)
        self.file_list_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 6))
        self.file_list_frame.grid_columnconfigure(0, weight=1)

        self._show_empty_state()

        self.file_count_label = ctk.CTkLabel(
            frame, text="0 files selected",
            text_color=("gray50", "gray60"), font=ctk.CTkFont(size=11)
        )
        self.file_count_label.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="w")

    def _show_empty_state(self):
        ctk.CTkLabel(
            self.file_list_frame,
            text="No files selected.\nClick \"+ Add Files\" to get started.",
            text_color=("gray55", "gray55"),
            font=ctk.CTkFont(size=13)
        ).grid(row=0, column=0, pady=40)

    def _build_settings_panel(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=1, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        # ── Image Descriptions toggle ──
        SectionLabel(frame, text="AI Image Descriptions").grid(
            row=0, column=0, padx=16, pady=(16, 6), sticky="w")

        toggle_frame = ctk.CTkFrame(frame, fg_color=("gray85", "gray22"), corner_radius=8)
        toggle_frame.grid(row=1, column=0, padx=16, sticky="ew")
        toggle_frame.grid_columnconfigure(1, weight=1)

        self.images_switch = ctk.CTkSwitch(
            toggle_frame, text="",
            variable=self.images_enabled,
            command=self._on_images_toggle,
            width=46
        )
        self.images_switch.grid(row=0, column=0, padx=(10, 6), pady=10)

        self.images_toggle_label = ctk.CTkLabel(
            toggle_frame, text="", font=ctk.CTkFont(size=12), anchor="w"
        )
        self.images_toggle_label.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="w")

        self.images_info_label = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            wraplength=220,
            justify="left"
        )
        self.images_info_label.grid(row=2, column=0, padx=16, pady=(5, 6), sticky="w")

        Divider(frame).grid(row=3, column=0, sticky="ew", padx=16, pady=4)

        # ── API Key ──
        self.api_key_section_widgets = []

        lbl = SectionLabel(frame, text="Anthropic API Key")
        lbl.grid(row=4, column=0, padx=16, pady=(10, 4), sticky="w")
        self.api_key_section_widgets.append(lbl)

        self.api_key_entry = ctk.CTkEntry(
            frame, textvariable=self.api_key_var,
            show="•", placeholder_text="sk-ant-api03-..."
        )
        self.api_key_entry.grid(row=5, column=0, padx=16, sticky="ew")
        self.api_key_section_widgets.append(self.api_key_entry)

        key_btns = ctk.CTkFrame(frame, fg_color="transparent")
        key_btns.grid(row=6, column=0, padx=16, pady=(5, 4), sticky="w")
        self.api_key_section_widgets.append(key_btns)

        self.show_key_btn = ctk.CTkButton(
            key_btns, text="Show", width=60, height=28,
            fg_color=("gray60", "gray35"), hover_color=("gray50", "gray28"),
            command=self._toggle_key_visibility)
        self.show_key_btn.grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(key_btns, text="Save Key", width=80, height=28,
                      command=self._save_api_key).grid(row=0, column=1)

        api_hint = ctk.CTkLabel(
            frame, text="Get your key at console.anthropic.com",
            text_color=("gray50", "gray60"), font=ctk.CTkFont(size=11)
        )
        api_hint.grid(row=7, column=0, padx=16, pady=(0, 10), sticky="w")
        self.api_key_section_widgets.append(api_hint)

        Divider(frame).grid(row=8, column=0, sticky="ew", padx=16, pady=4)

        # ── Output Folder ──
        SectionLabel(frame, text="Output Folder").grid(
            row=9, column=0, padx=16, pady=(10, 4), sticky="w")

        self.output_entry = ctk.CTkEntry(
            frame, textvariable=self.output_folder,
            placeholder_text="Choose where to save .md files..."
        )
        self.output_entry.grid(row=10, column=0, padx=16, sticky="ew")

        ctk.CTkButton(frame, text="Browse...", width=90, height=28,
                      command=self._choose_output).grid(
                          row=11, column=0, padx=16, pady=(5, 10), sticky="w")

        Divider(frame).grid(row=12, column=0, sticky="ew", padx=16, pady=4)

        # ── Existing Files ──
        SectionLabel(frame, text="If Output File Exists").grid(
            row=13, column=0, padx=16, pady=(10, 6), sticky="w")

        for i, (val, label) in enumerate([
            ("ask",       "Ask each time"),
            ("overwrite", "Always overwrite"),
            ("skip",      "Always skip"),
        ]):
            ctk.CTkRadioButton(
                frame, text=label,
                variable=self.overwrite_var, value=val
            ).grid(row=14 + i, column=0, padx=22, pady=2, sticky="w")

        Divider(frame).grid(row=17, column=0, sticky="ew", padx=16, pady=10)

        # ── Actions ──
        self.analyze_btn = ctk.CTkButton(
            frame, text="Analyze Files", height=36,
            command=self._analyze_files
        )
        self.analyze_btn.grid(row=18, column=0, padx=16, pady=(0, 6), sticky="ew")

        self.estimate_label = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
            wraplength=220
        )
        self.estimate_label.grid(row=19, column=0, padx=16, pady=(0, 8))

        self.convert_btn = ctk.CTkButton(
            frame, text="Convert to Markdown",
            height=44, font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self._start_conversion
        )
        self.convert_btn.grid(row=20, column=0, padx=16, pady=(0, 16), sticky="ew")

        # Initialize toggle state
        self._update_api_section()

    # ── Image toggle logic ────────────────────────────────────────────────────

    def _on_images_toggle(self):
        enabled = self.images_enabled.get()
        cfg = load_config()
        cfg["images_enabled"] = enabled
        save_config(cfg)
        self._update_api_section()
        self.estimate_label.configure(text="")
        self.convert_btn.configure(state="disabled")

    def _update_api_section(self):
        enabled = self.images_enabled.get()

        if enabled:
            self.images_toggle_label.configure(text="Enabled — images will be described")
            self.images_info_label.configure(
                text="Claude Haiku will describe each image and extract any text inside it. Requires an API key."
            )
        else:
            self.images_toggle_label.configure(text="Disabled — images will be skipped")
            self.images_info_label.configure(
                text="Images will be noted as [Image — description disabled]. No API key required."
            )

        state = "normal" if enabled else "disabled"
        for w in self.api_key_section_widgets:
            try:
                w.configure(state=state)
            except Exception:
                pass

    # ── File management ───────────────────────────────────────────────────────

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Files to Convert",
            filetypes=[
                ("Supported files", "*.pptx *.ppt *.pdf"),
                ("PowerPoint", "*.pptx *.ppt"),
                ("PDF", "*.pdf"),
            ]
        )
        added = 0
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                added += 1
        if added:
            self._refresh_file_list()
            self.estimate_label.configure(text="")
            self.convert_btn.configure(state="disabled")

    def _remove_selected(self):
        self.selected_files = [
            f for i, f in enumerate(self.selected_files)
            if i >= len(self.file_checkboxes) or not self.file_checkboxes[i].get()
        ]
        self._refresh_file_list()
        self.estimate_label.configure(text="")
        self.convert_btn.configure(state="disabled")

    def _clear_files(self):
        self.selected_files = []
        self._refresh_file_list()
        self.estimate_label.configure(text="")
        self.convert_btn.configure(state="disabled")

    def _refresh_file_list(self):
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        self.file_checkboxes = []

        if not self.selected_files:
            self._show_empty_state()
            self.file_count_label.configure(text="0 files selected")
            return

        for i, fp in enumerate(self.selected_files):
            p = Path(fp)
            icon = "📊" if p.suffix.lower() in ('.ppt', '.pptx') else "📄"
            cb_var = ctk.BooleanVar(value=False)
            self.file_checkboxes.append(cb_var)

            row = ctk.CTkFrame(self.file_list_frame, fg_color=("gray92", "gray22"))
            row.grid(row=i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkCheckBox(row, text="", variable=cb_var, width=24, height=24
                            ).grid(row=0, column=0, padx=(8, 2), pady=6)
            ctk.CTkLabel(row, text=f"{icon}  {p.name}", anchor="w",
                         font=ctk.CTkFont(size=12)
                         ).grid(row=0, column=1, padx=4, pady=6, sticky="w")
            ctk.CTkLabel(row, text=p.parent.name, anchor="e",
                         font=ctk.CTkFont(size=11), text_color=("gray55", "gray60")
                         ).grid(row=0, column=2, padx=10)

        n = len(self.selected_files)
        self.file_count_label.configure(text=f"{n} file{'s' if n != 1 else ''} selected")

    # ── Settings actions ──────────────────────────────────────────────────────

    def _toggle_key_visibility(self):
        showing = self.api_key_entry.cget("show") == ""
        self.api_key_entry.configure(show="•" if showing else "")
        self.show_key_btn.configure(text="Show" if showing else "Hide")

    def _save_api_key(self):
        save_api_key(self.api_key_var.get().strip())
        self.status_label.configure(text="API key saved securely to Mac Keychain.")

    def _choose_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            cfg = load_config()
            cfg["output_folder"] = folder
            save_config(cfg)

    # ── Analyze ───────────────────────────────────────────────────────────────

    def _analyze_files(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Add files before analyzing.")
            return

        images_on = self.images_enabled.get()

        if images_on and not self.api_key_var.get().strip():
            messagebox.showwarning(
                "No API Key",
                "AI image descriptions are enabled but no API key is entered.\n\n"
                "Enter your key above, or turn off image descriptions to convert without one."
            )
            return

        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.status_label.configure(text="Counting images across selected files...")

        def run():
            try:
                from converter import FileConverter
                conv = FileConverter(
                    self.api_key_var.get().strip() if images_on else None,
                    images_enabled=images_on
                )
                count = conv.estimate_images(self.selected_files)
                cost = conv.estimate_cost(count) if images_on else 0.0
                self.after(0, lambda: self._show_estimate(count, cost, images_on))
            except Exception as e:
                self.after(0, lambda err=str(e): self._analyze_error(err))

        threading.Thread(target=run, daemon=True).start()

    def _show_estimate(self, image_count, cost, images_on):
        self.analyze_btn.configure(state="normal", text="Analyze Files")

        if not images_on:
            msg = (f"{image_count} image{'s' if image_count != 1 else ''} found\n"
                   "Images will be noted but not described.\nEstimated cost: $0.00"
                   ) if image_count else "No images found.\nEstimated cost: $0.00"
        elif image_count == 0:
            msg = "No images found.\nEstimated cost: $0.00"
        else:
            msg = (f"{image_count} image{'s' if image_count != 1 else ''} to describe\n"
                   f"Estimated cost: ~${cost:.4f}\n(Claude Haiku, approximate)")

        self.estimate_label.configure(text=msg)
        self.status_label.configure(text=f"Analysis complete — {image_count} images found.")
        self.convert_btn.configure(state="normal")

    def _analyze_error(self, error):
        self.analyze_btn.configure(state="normal", text="Analyze Files")
        self.status_label.configure(text=f"Analysis error: {error}")
        messagebox.showerror("Analysis Error", f"Could not analyze files:\n\n{error}")

    # ── Conversion ────────────────────────────────────────────────────────────

    def _start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Add files before converting.")
            return
        if not self.output_folder.get().strip():
            messagebox.showwarning("No Output Folder", "Choose an output folder first.")
            return

        images_on = self.images_enabled.get()
        if images_on and not self.api_key_var.get().strip():
            messagebox.showwarning(
                "No API Key",
                "AI image descriptions are enabled but no API key is entered.\n\n"
                "Enter your key above, or turn off image descriptions to convert without one."
            )
            return

        overwrite_mode = self.overwrite_var.get()
        if overwrite_mode == "ask":
            existing = [
                Path(fp).name for fp in self.selected_files
                if (Path(self.output_folder.get()) / f"{Path(fp).stem}.md").exists()
            ]
            if existing:
                names = "\n".join(f"  • {n}" for n in existing[:6])
                if len(existing) > 6:
                    names += f"\n  ...and {len(existing) - 6} more"
                result = messagebox.askyesnocancel(
                    "Output Files Already Exist",
                    f"These Markdown files already exist:\n\n{names}\n\n"
                    "Yes = Overwrite all\nNo = Skip all\nCancel = Abort"
                )
                if result is None:
                    return
                overwrite_mode = "overwrite" if result else "skip"

        self.converting = True
        self.convert_btn.configure(state="disabled", text="Converting...")
        self.analyze_btn.configure(state="disabled")
        self.progress_bar.set(0)

        threading.Thread(
            target=self._run_conversion,
            args=(overwrite_mode, images_on),
            daemon=True
        ).start()

    def _run_conversion(self, overwrite_mode, images_on):
        from converter import FileConverter

        results = {"success": [], "skipped": [], "failed": []}
        total = len(self.selected_files)

        def log_cb(msg):
            self.after(0, lambda m=msg: self.status_label.configure(text=m))

        conv = FileConverter(
            self.api_key_var.get().strip() if images_on else None,
            images_enabled=images_on,
            log_callback=log_cb
        )

        for idx, fp in enumerate(self.selected_files):
            fname = Path(fp).name

            def file_progress(p, i=idx):
                overall = (i + p) / total
                self.after(0, lambda v=overall: self.progress_bar.set(v))

            conv.progress_callback = file_progress

            self.after(0, lambda f=fname, i=idx: self.status_label.configure(
                text=f"Converting {f}  ({i + 1}/{total})"
            ))

            try:
                success, out_path, msg = conv.convert_file(
                    fp, self.output_folder.get(), overwrite_mode
                )
                if success:
                    results["success"].append(fname)
                elif msg.startswith("Skipped"):
                    results["skipped"].append(fname)
                else:
                    results["failed"].append((fname, msg))
            except Exception as e:
                results["failed"].append((fname, str(e)))

            self.after(0, lambda v=(idx + 1) / total: self.progress_bar.set(v))

        self.after(0, lambda: self._conversion_done(results))

    def _conversion_done(self, results):
        self.converting = False
        self.convert_btn.configure(state="normal", text="Convert to Markdown")
        self.analyze_btn.configure(state="normal")
        self.progress_bar.set(1.0)

        parts = []
        if results["success"]:
            parts.append(f"✓ {len(results['success'])} converted")
        if results["skipped"]:
            parts.append(f"⏭ {len(results['skipped'])} skipped")
        if results["failed"]:
            parts.append(f"✗ {len(results['failed'])} failed")
        self.status_label.configure(text="  |  ".join(parts) if parts else "Done.")

        detail_parts = []
        if results["success"]:
            detail_parts.append(
                "Successfully converted:\n" +
                "\n".join(f"  • {f}" for f in results["success"])
            )
        if results["skipped"]:
            detail_parts.append(
                "Skipped (already exist):\n" +
                "\n".join(f"  • {f}" for f in results["skipped"])
            )
        if results["failed"]:
            detail_parts.append(
                "Failed:\n" +
                "\n".join(f"  • {f}: {m}" for f, m in results["failed"])
            )

        messagebox.showinfo("Conversion Complete",
                            "\n\n".join(detail_parts) or "Nothing to report.")

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self):
        footer = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray88", "gray17"))
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(footer, height=6)
        self.progress_bar.grid(row=0, column=0, padx=18, pady=(10, 4), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            footer, text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65")
        )
        self.status_label.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="w")


if __name__ == "__main__":
    app = ConverterApp()
    app.mainloop()
