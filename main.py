import os,json,hashlib
import threading,asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import requests,sseclient

with open("config.json", "r") as f:
    config = json.load(f)

if config['USE_TTS']:
    from generate_voice import generate_voice, stop_audio

def load_presets():
    if os.path.exists("presets.json"):
        with open("presets.json", "r") as f:
            return json.load(f)
    return {}

class Button:
    def __init__(self, master, text, command, side='top', padx=5, pady=5):
        self.button = tk.Button(master, text=text, command=command)
        self.button.pack(side=side, padx=padx, pady=pady)

class ParameterInput:
    def __init__(self, master, label, default_value):
        self.frame = tk.Frame(master)
        self.frame.pack(side='top', fill='x', pady=2)
        tk.Label(self.frame, text=label).pack(side='left')
        self.var = tk.DoubleVar(value=default_value)
        tk.Entry(self.frame, textvariable=self.var, width=10).pack(side='right')

    def get(self):
        return self.var.get()

class APIHandler:
    BASE_URL = "https://api.totalgpt.ai"

    @classmethod
    def load_api_key(cls):
        cls.HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['INFERMATIC_API_KEY']}"
        }

    @classmethod
    def fetch_models(cls):
        cls.load_api_key()
        try:
            response = requests.get(f"{cls.BASE_URL}/models", headers=cls.HEADERS)
            response.raise_for_status()

            data = response.json()
            print("API Response:", json.dumps(data, indent=2))  # Debug print

            if isinstance(data, list):
                return [model.get('id', model.get('name', '')) for model in data if isinstance(model, dict)]
            elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                return [model.get('id', model.get('name', '')) for model in data['data'] if isinstance(model, dict)]
            else:
                print("Unexpected response structure")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching models: {e}")
            return []

    @classmethod
    def generate_text(cls, data):
        cls.load_api_key()
        return requests.post(f"{cls.BASE_URL}/completions", json=data, headers=cls.HEADERS, timeout=300, stream=True)

    @staticmethod
    async def check_grammar(text):
        try:
            response = requests.post(
                "https://api.languagetool.org/v2/check",
                data={"text": text, "language": "en-US"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error checking grammar: {e}")
            return {}

class TextGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Register the close event handler
        self.root.title("AI Writing Notebook UI")

        self.setup_ui()
        self.setup_variables()
        self.fetch_models()
        self.load_session()

        self.presets = load_presets()
        self.update_preset_dropdown()

        self.grammar_cache = {}

    def save_session(self):
        text = self.text_widget.get("1.0", tk.END).rstrip("\n")
        session_data = {
            "text": text,
            "memory": getattr(self, 'memory_text', ''),
            "author_notes": getattr(self, 'author_notes_text', ''),
            "lorebook_entries": getattr(self, 'lorebook_entries_data', {})
        }
        with open("session.json", "w") as f:
            json.dump(session_data, f)

    def load_session(self):
        if not os.path.exists("session.json"):
            with open("session.json", "w") as f:
                json.dump({"text": "", "memory": "", "author_notes": "", "lorebook_entries": {}}, f)

        try:
            with open("session.json", "r") as f:
                session_data = json.load(f)
                self.text_widget.delete("1.0", tk.END)
                self.text_widget.insert(tk.END, session_data.get("text", ""))
                self.memory_text = session_data.get("memory", "")
                self.author_notes_text = session_data.get("author_notes", "")
                self.lorebook_entries_data = session_data.get("lorebook_entries", {})
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading session data: {e}")
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert(tk.END, "")
            self.memory_text = ""
            self.author_notes_text = ""
            self.lorebook_entries_data = {}

    def on_close(self):
        self.save_session()
        self.root.destroy()

    def setup_ui(self):
        self.text_widget = scrolledtext.ScrolledText(self.root, wrap='word', width=60, height=20)
        self.text_widget.pack(expand=True, fill='both', side='left', padx=10, pady=10)
        self.text_widget.bind("<Button-1>", self.on_text_click)  # Bind click event

        control_frame = tk.Frame(self.root)
        control_frame.pack(side='right', fill='y', pady=10)

        button_frame = tk.Frame(control_frame)
        button_frame.pack(side='top', fill='x', pady=10)

        self.buttons = {
            'generate': Button(button_frame, "Generate", self.start_generation, side='left'),
            'cancel': Button(button_frame, "Cancel", self.cancel_generation, side='left'),
            'retry': Button(button_frame, "Retry", lambda: self.retry_or_undo_generation('retry'), side='left'),
            'undo': Button(button_frame, "Undo", lambda: self.retry_or_undo_generation('undo'), side='left'),
            'info': Button(button_frame, "Story Info", lambda: self.story_info(), side='left'),
        }

        self.setup_advanced_options(control_frame)

        if config['USE_TTS']:
            self.audio_toggle_var = tk.BooleanVar(value=True)  # Default to audio generation enabled
            self.audio_toggle_checkbox = tk.Checkbutton(control_frame, text="Enable Audio", variable=self.audio_toggle_var)
            self.audio_toggle_checkbox.pack(side='top', pady=5)

        font_size_frame = tk.Frame(self.root)
        font_size_frame.pack(side='bottom', fill='x', padx=10, pady=10, anchor='e')

        self.font_size = 12  # Default font size
        self.text_widget.config(font=("TkDefaultFont", self.font_size))

        tk.Button(font_size_frame, text="Check Grammar", command=self.check_grammar).pack(side='right')
        tk.Button(font_size_frame, text="+", command=self.increase_font_size).pack(side='right')
        tk.Button(font_size_frame, text="-", command=self.decrease_font_size).pack(side='right')

    def setup_advanced_options(self, parent):
        self.advanced_frame = tk.Frame(parent)
        self.advanced_frame.pack(side='top', fill='x', pady=10)

        self.show_advanced = tk.BooleanVar()
        self.advanced_checkbox = tk.Checkbutton(self.advanced_frame, text="Show Advanced Options",
                                                variable=self.show_advanced, command=self.toggle_advanced_options)
        self.advanced_checkbox.pack(side='top')

        self.advanced_options = tk.Frame(self.advanced_frame)

        # Presets Dropdown
        self.preset_label = tk.Label(self.advanced_options, text="Presets:")
        self.preset_label.pack(side='top', anchor='w')
        self.preset_var = tk.StringVar(value="")
        self.preset_dropdown = ttk.Combobox(self.advanced_options, textvariable=self.preset_var, state="readonly")
        self.preset_dropdown.pack(side='top', fill='x')
        self.preset_dropdown.bind("<<ComboboxSelected>>", self.apply_preset)

        # Load presets into the dropdown
        self.presets = load_presets()
        self.preset_dropdown['values'] = list(self.presets.keys())

        self.model_label = tk.Label(self.advanced_options, text="Model:")
        self.model_label.pack(side='top', anchor='w')
        self.model_var = tk.StringVar(value="L3-70B-Euryale-v2.1")
        self.model_dropdown = ttk.Combobox(self.advanced_options, textvariable=self.model_var, state="readonly")
        self.model_dropdown.pack(side='top', fill='x')

        self.parameters = {
            "max_tokens": ParameterInput(self.advanced_options, "Max Tokens:", 222),
            "temperature": ParameterInput(self.advanced_options, "Temperature:", 0.8),
            "top_p": ParameterInput(self.advanced_options, "Top P:", 0.98),
            "top_k": ParameterInput(self.advanced_options, "Top K:", -1),
            "min_p": ParameterInput(self.advanced_options, "Min P:", 0.08),
            "repetition_penalty": ParameterInput(self.advanced_options, "Repetition Penalty:", 1.0),
            "presence_penalty": ParameterInput(self.advanced_options, "Presence Penalty:", 0.5)
        }

    def apply_preset(self, event):
        preset_name = self.preset_var.get()
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            for param, value in preset.items():
                if param in self.parameters:
                    self.parameters[param].var.set(value)

    def update_preset_dropdown(self):
        self.preset_dropdown['values'] = list(self.presets.keys())

    def setup_variables(self):
        self.cancel_requested = False
        self.last_prompt = ""
        self.last_generated_text = ""
        self.grammar_errors = []  # Store grammar errors

    def toggle_advanced_options(self):
        if self.show_advanced.get():
            self.advanced_options.pack(side='top', fill='x', pady=10)
        else:
            self.advanced_options.pack_forget()

    def fetch_models(self):
        def fetch():
            models = APIHandler.fetch_models()
            if models:
                self.root.after(0, lambda: self.update_model_dropdown(models))
            else:
                print("No models fetched or empty model list returned")

        threading.Thread(target=fetch).start()

    def start_generation(self):
        self.last_prompt = self.text_widget.get("1.0", tk.END).strip()
        self.cancel_requested = False
        self.text_widget.tag_remove('highlight', '1.0', tk.END)  # Reset color
        threading.Thread(target=self.generate_text, args=(self.last_prompt,)).start()
        self.save_session()

    def cancel_generation(self):
        self.cancel_requested = True
        if config['USE_TTS']:
            stop_audio()

    def generate_text(self, prompt):
        data = {
            "model": self.model_var.get(),
            "prompt": prompt,
            "stream": True,
            "seed": -1,
            **{k: int(v.get()) if k in ['max_tokens', 'top_k'] else v.get() for k, v in self.parameters.items()}
        }

        try:
            response = APIHandler.generate_text(data)
            response.raise_for_status()
            client = sseclient.SSEClient(response)
            self.last_generated_text = ""
            for event in client.events():
                if self.cancel_requested:
                    break
                if event.data:
                    try:
                        if event.data.strip() == '[DONE]':
                            break
                        payload = json.loads(event.data)
                        if 'text' in payload['choices'][0]:
                            chunk = payload['choices'][0]['text']
                            self.last_generated_text += chunk
                            self.text_widget.insert(tk.END, chunk, 'highlight')  # Tag new text
                            self.text_widget.tag_config('highlight', foreground='blue')  # Style the tag
                            self.text_widget.see(tk.END)
                        elif 'finish_reason' in payload['choices'][0]:
                            print(f"Text generation finished. Reason: {payload['choices'][0]['finish_reason']}")
                    except (json.JSONDecodeError, KeyError) as error:
                        print(error)
                        pass

        except requests.exceptions.Timeout:
            self.text_widget.insert(tk.END, "The request timed out")
        except json.JSONDecodeError:
            self.text_widget.insert(tk.END, "Failed to decode JSON response")

        if config['USE_TTS']:
            if self.audio_toggle_var.get():
                generate_voice(self.last_generated_text)

        self.save_session()

    def retry_or_undo_generation(self, action):
        if action == 'retry':
            self.cancel_requested = False
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, self.last_prompt)
        if config['USE_TTS']:
            stop_audio()
        if action == 'retry':
            self.start_generation()
        else:
            self.save_session()

    def check_grammar(self):
        full_text = self.text_widget.get("1.0", "end-1c")
        text_to_check = full_text[-20000:]
        offset = len(full_text) - len(text_to_check)

        text_hash = hashlib.md5(text_to_check.encode()).hexdigest()
        if text_hash in self.grammar_cache:
            results = self.grammar_cache[text_hash]
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(APIHandler.check_grammar(text_to_check))
            loop.close()
            self.grammar_cache[text_hash] = results

        self.display_grammar_errors(results, offset)

    def display_grammar_errors(self, results, offset):
        self.grammar_errors = []  # Clear previous errors
        self.text_widget.tag_remove('grammar_error', '1.0', tk.END)  # Clear previous highlights

        if 'matches' in results:
            for match in results['matches']:
                start_index = self.get_text_widget_index(match['offset'] + offset)
                end_index = self.get_text_widget_index(match['offset'] + match['length'] + offset)

                print(f"Error: {match['message']}")
                print(f"Start index: {start_index}, End index: {end_index}")

                self.text_widget.tag_add('grammar_error', start_index, end_index)
                self.text_widget.tag_config('grammar_error', background='yellow')
                self.grammar_errors.append((start_index, end_index, match['message'], match['replacements']))

    def get_text_widget_index(self, char_index):
        return self.text_widget.index(f"1.0 + {char_index} chars")

    def on_text_click(self, event):
        index = self.text_widget.index(f"@{event.x},{event.y}")

        for start, end, message, replacements in self.grammar_errors:
            if self.text_widget.compare(index, ">=", start) and self.text_widget.compare(index, "<", end):
                self.show_suggestions_popup(start, end, message, replacements)
                break

    def show_suggestions_popup(self, start, end, message, replacements):
        popup = tk.Toplevel(self.root)
        popup.title("Grammar Suggestions")

        tk.Label(popup, text=message, wraplength=400).pack(pady=10)

        for replacement in replacements:
            suggestion = replacement['value']
            button = tk.Button(popup, text=suggestion, command=lambda s=suggestion, p=popup: self.apply_suggestion(start, end, s, p))
            button.pack(fill='x', padx=10, pady=5)

    def apply_suggestion(self, start, end, suggestion, popup):
        self.text_widget.delete(start, end)
        self.text_widget.insert(start, suggestion)
        self.text_widget.tag_remove('grammar_error', start, end)
        self.save_session()
        popup.destroy()

    def update_model_dropdown(self, models):
        sorted_models = sorted(models)
        self.model_dropdown['values'] = sorted_models
        if sorted_models:
            self.model_var.set(sorted_models[0])

    def increase_font_size(self):
        self.font_size += 2
        self.text_widget.config(font=("TkDefaultFont", self.font_size))

    def decrease_font_size(self):
        self.font_size = max(8, self.font_size - 2)
        self.text_widget.config(font=("TkDefaultFont", self.font_size))

    def story_info(self):
        popup = tk.Toplevel(self.root)
        popup.title("Story Information")

        tk.Label(popup, text="Memory:").pack(anchor='w')
        self.memory_entry = scrolledtext.ScrolledText(popup, wrap='word', width=50, height=10)
        self.memory_entry.pack(fill='x', padx=10, pady=5)
        self.memory_entry.insert(tk.END, getattr(self, 'memory_text', ''))

        tk.Label(popup, text="Author Notes:").pack(anchor='w')
        self.authornotes_entry = scrolledtext.ScrolledText(popup, wrap='word', width=50, height=10)
        self.authornotes_entry.pack(fill='x', padx=10, pady=5)
        self.authornotes_entry.insert(tk.END, getattr(self, 'author_notes_text', ''))

        tk.Label(popup, text="Lorebook Entries:").pack(anchor='w')

        lorebook_canvas = tk.Canvas(popup)
        lorebook_canvas.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=lorebook_canvas.yview)
        scrollbar.pack(side='right', fill='y')

        self.lorebook_frame = tk.Frame(lorebook_canvas)
        lorebook_canvas.create_window((0, 0), window=self.lorebook_frame, anchor='nw')
        lorebook_canvas.configure(yscrollcommand=scrollbar.set)

        self.add_lorebook_button = tk.Button(popup, text="New Entry", command=self.add_lorebook_entry)
        self.add_lorebook_button.pack(pady=10)

        self.lorebook_entries_widgets = []
        self.load_lorebook_entries()

        popup.protocol("WM_DELETE_WINDOW", lambda: self.save_story_info(popup))
        self.lorebook_frame.bind("<Configure>", lambda e: lorebook_canvas.configure(scrollregion=lorebook_canvas.bbox("all")))

    def add_lorebook_entry(self):
        entry_id = len(self.lorebook_entries_widgets) + 1
        entry_frame = tk.Frame(self.lorebook_frame)
        entry_frame.pack(fill='x', pady=5)

        tk.Label(entry_frame, text=f"Entry #{entry_id}").pack(anchor='w')

        tk.Label(entry_frame, text="Name:").pack(anchor='w')
        name_entry = scrolledtext.ScrolledText(entry_frame, wrap='word', width=50, height=2)
        name_entry.pack(fill='x', padx=10, pady=5)

        tk.Label(entry_frame, text="Content:").pack(anchor='w')
        content_entry = scrolledtext.ScrolledText(entry_frame, wrap='word', width=50, height=10)
        content_entry.pack(fill='x', padx=10, pady=5)

        self.lorebook_entries_widgets.append((entry_frame, name_entry, content_entry))

    def load_lorebook_entries(self):
        self.lorebook_entries_widgets = []
        if hasattr(self, 'lorebook_entries_data'):
            for idx, (name, content) in enumerate(self.lorebook_entries_data.items(), start=1):
                entry_frame = tk.Frame(self.lorebook_frame)
                entry_frame.pack(fill='x', pady=5)

                tk.Label(entry_frame, text=f"Entry #{idx}").pack(anchor='w')

                tk.Label(entry_frame, text="Name:").pack(anchor='w')
                name_entry = scrolledtext.ScrolledText(entry_frame, wrap='word', width=50, height=2)
                name_entry.pack(fill='x', padx=10, pady=5)
                name_entry.insert(tk.END, name)

                tk.Label(entry_frame, text="Content:").pack(anchor='w')
                content_entry = scrolledtext.ScrolledText(entry_frame, wrap='word', width=50, height=10)
                content_entry.pack(fill='x', padx=10, pady=5)
                content_entry.insert(tk.END, content)

                self.lorebook_entries_widgets.append((entry_frame, name_entry, content_entry))

    def save_story_info(self, popup):
        self.memory_text = self.memory_entry.get("1.0", tk.END).rstrip("\n")
        self.author_notes_text = self.authornotes_entry.get("1.0", tk.END).rstrip("\n")

        self.lorebook_entries_data = {}
        for _, name_entry, content_entry in self.lorebook_entries_widgets:
            name = name_entry.get("1.0", tk.END).strip()
            content = content_entry.get("1.0", tk.END).strip()
            if name and content:
                self.lorebook_entries_data[name] = content

        self.save_session()
        popup.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TextGeneratorApp(root)
    root.mainloop()
