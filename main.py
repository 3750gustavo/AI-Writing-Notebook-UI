import os,json,hashlib
import threading,asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import requests,sseclient
import re

# Import the new markdown_viewer module
from markdown_viewer import show_markdown_viewer

with open("config.json", "r") as f:
    config = json.load(f)

if config['USE_TTS']:
    from generate_voice import generate_voice, stop_audio

class Button:
    def __init__(self, master, text, command, side='top', padx=5, pady=5):
        self.button = tk.Button(master, text=text, command=command)
        self.button.pack(side=side, padx=padx, pady=pady)

    def disable(self):
        self.button.config(state=tk.DISABLED)

    def enable(self):
        self.button.config(state=tk.NORMAL)

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
    def close_session(response):
        if response:
            response.close()

    @staticmethod
    async def check_grammar(text):
        try:
            response = requests.post(
                "https://api.languagetool.org/v2/check",
                data={"text": text, "language": "auto"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error checking grammar: {e}")
            return {}

class PresetManager:
    def __init__(self, presets_file):
        self.presets_file = presets_file
        self.presets = self.load_presets()

    def load_presets(self):
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error loading presets from {self.presets_file}: {e}")
                return {}
        return {}

    def save_presets(self):
        try:
            with open(self.presets_file, "w") as f:
                json.dump(self.presets, f, indent=4)
        except OSError as e:
            error_message = os.strerror(e.errno)
            print(f"Failed to save presets to {self.presets_file}: {error_message}")

    def get_preset_names(self):
        return list(self.presets.keys())

    def get_preset(self, preset_name):
        return self.presets.get(preset_name, {})

    def save_preset(self, preset_name, preset_data):
        if preset_name in self.presets:
            self.presets[preset_name] = preset_data
        else:
            self.presets[preset_name] = preset_data
        self.save_presets()

    def delete_preset(self, preset_name):
        if preset_name in self.presets:
            del self.presets[preset_name]
            self.save_presets()

class StyleManager:
    def __init__(self, root):
        self.root = root
        self.dark_mode = False
        self.light_bg = 'white'
        self.light_fg = 'black'
        self.dark_bg = '#1E1E2E'  # Dark blue-ish color
        self.dark_fg = 'white'

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_styles(self.root)

    def apply_styles(self, widget):
        bg_color = self.dark_bg if self.dark_mode else self.light_bg
        fg_color = self.dark_fg if self.dark_mode else self.light_fg

        widget_styles = {
            tk.Tk: lambda: widget.config(bg=bg_color),
            tk.Frame: lambda: widget.config(bg=bg_color),
            tk.Label: lambda: widget.config(bg=bg_color, fg=fg_color),
            tk.Button: lambda: widget.config(bg=bg_color, fg=fg_color),
            tk.Checkbutton: lambda: widget.config(bg=bg_color, fg=fg_color, selectcolor=bg_color),
            tk.Text: lambda: widget.config(bg=bg_color, fg=fg_color),
            scrolledtext.ScrolledText: lambda: widget.config(bg=bg_color, fg=fg_color),
            ttk.Combobox: lambda: self.configure_combobox(widget, bg_color, fg_color)
        }

        if type(widget) in widget_styles:
            widget_styles[type(widget)]()
            if isinstance(widget, tk.Tk) or isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    self.apply_styles(child)

        # Update any text inside text_widget with highlight tag to match the new color scheme
        if isinstance(widget, tk.Text) and widget.tag_ranges('highlight'):
            widget.tag_config('highlight', foreground='blue' if self.dark_mode == False else 'cyan')

    def configure_combobox(self, widget, bg_color, fg_color):
        style = ttk.Style()
        style.configure('TCombobox', background=bg_color, foreground=fg_color)
        widget.config(style='TCombobox')

class TextGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Register the close event handler
        self.root.title("AI Writing Notebook UI")
        self.style_manager = StyleManager(self.root)

        self.lorebook_entries_widgets = []
        self.preset_manager = PresetManager("presets.json")
        self.setup_ui()
        self.setup_variables()
        self.fetch_models()
        self.load_session()

        self.preset_manager = PresetManager("presets.json")
        self.presets = self.preset_manager.get_preset_names()
        self.update_preset_dropdown()

        self.grammar_cache = {}
        self.font_size = 12  # default font size

    def save_session(self):
        text = self.text_widget.get("1.0", tk.END).strip()
        session_data = {
            "text": text,
            "memory": getattr(self, 'memory_text', ''),
            "author_notes": getattr(self, 'author_notes_text', ''),
            "lorebook_entries": getattr(self, 'lorebook_entries_data', {})
        }
        try:
            with open("session.json", "w") as f:
                json.dump(session_data, f)
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save session: {e}")

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
            messagebox.showerror("Session Load Error", str(e))
            self.root.destroy()
        except IOError as e:
            messagebox.showerror("Error", f"Failed to load session: {e}")
            self.root.destroy()

    def on_close(self):
        self.save_session()
        self.root.destroy()

    def setup_ui(self):
        self.text_widget = scrolledtext.ScrolledText(self.root, wrap='word', width=60, height=20)
        self.text_widget.pack(fill='both', expand=True, side='left', padx=10, pady=10)
        self.text_widget.bind("<Button-1>", self.on_text_click)  # Bind click event

        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='y', padx=10, pady=10)

        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill='x', pady=10)

        self.buttons = {
            'generate': Button(button_frame, "Generate", self.start_generation, side='left'),
            'cancel': Button(button_frame, "Cancel", self.cancel_generation, side='left'),
            'retry': Button(button_frame, "Retry", lambda: self.retry_or_undo_generation('retry'), side='left'),
            'undo': Button(button_frame, "Undo", lambda: self.retry_or_undo_generation('undo'), side='left'),
            'info': Button(button_frame, "Story Info", lambda: self.story_info(), side='left'),
        }

        self.setup_advanced_options(control_frame)

        if config['USE_TTS']:
            self.audio_toggle_var = tk.BooleanVar(value=True)
            self.audio_toggle_checkbox = tk.Checkbutton(control_frame, text="Enable Audio", variable=self.audio_toggle_var)
            self.audio_toggle_checkbox.pack(fill='x', pady=5)

        # Bottom buttons
        bottom_button_frame = tk.Frame(self.root)
        bottom_button_frame.pack(fill='x', side='bottom', padx=10, pady=(0, 10))

        tk.Button(bottom_button_frame, text="+", command=self.increase_font_size).pack(side='left')
        tk.Button(bottom_button_frame, text="-", command=self.decrease_font_size).pack(side='left')

        self.dark_mode_toggle = tk.Button(bottom_button_frame, text="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.dark_mode_toggle.config(font=("TkDefaultFont", 8))
        self.dark_mode_toggle.pack(side='left', padx=2, pady=2)

        tk.Button(bottom_button_frame, text="Check Grammar", command=self.check_grammar).pack(side='left')
        tk.Button(bottom_button_frame, text="Markdown", command=self.show_markdown_viewer).pack(side='left')  # New Markdown button

    def toggle_dark_mode(self):
        self.style_manager.toggle_dark_mode()

    def setup_advanced_options(self, parent):
        self.advanced_frame = tk.Frame(parent)
        self.advanced_frame.pack(side='top', fill='x', pady=10)

        self.show_advanced = tk.BooleanVar()
        self.advanced_checkbox = tk.Checkbutton(self.advanced_frame, text="Show Advanced Options",
                                          variable=self.show_advanced, command=self.toggle_advanced_options)
        self.advanced_checkbox.pack(side='top')

        self.advanced_options = tk.Frame(self.advanced_frame)

        # Presets Dropdown and Buttons
        preset_frame = tk.Frame(self.advanced_options)
        preset_frame.pack(side='top', fill='x', pady=5)

        self.preset_label = tk.Label(preset_frame, text="Presets:")
        self.preset_label.pack(side='left')

        self.preset_var = tk.StringVar(value="")
        self.preset_dropdown = ttk.Combobox(preset_frame, textvariable=self.preset_var, state="readonly")
        self.preset_dropdown.pack(side='left', fill='x', expand=True)
        self.preset_dropdown.bind("<<ComboboxSelected>>", self.apply_preset)

        self.save_preset_button = tk.Button(preset_frame, text="Save", command=self.save_preset)
        self.save_preset_button.pack(side='left', padx=2)

        self.delete_preset_button = tk.Button(preset_frame, text="Delete", command=self.delete_preset)
        self.delete_preset_button.pack(side='left', padx=2)

        self.create_preset_button = tk.Button(preset_frame, text="Create", command=self.create_preset)
        self.create_preset_button.pack(side='left', padx=2)

        # Load presets into the dropdown
        self.presets = self.preset_manager.get_preset_names()
        self.update_preset_dropdown()

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

    def create_preset(self):
        preset_name = simpledialog.askstring("New Preset", "Enter a name for the new preset:")
        if not preset_name:
            return  # User cancelled the dialog

        if preset_name in self.presets:
            messagebox.showerror("Error", "A preset with this name already exists.")
            return

        new_preset = {}
        for param, input_widget in self.parameters.items():
            new_preset[param] = input_widget.get()

        self.preset_manager.save_preset(preset_name, new_preset)
        self.presets = self.preset_manager.get_preset_names()
        self.update_preset_dropdown()
        self.preset_var.set(preset_name)
        messagebox.showinfo("Success", f"Preset '{preset_name}' created successfully.")

    def save_preset(self):
        preset_name = self.preset_var.get()
        if not preset_name:
            messagebox.showerror("Error", "Please select a preset to save.")
            return

        preset_data = {}
        for param, input_widget in self.parameters.items():
            preset_data[param] = input_widget.get()

        self.preset_manager.save_preset(preset_name, preset_data)
        messagebox.showinfo("Success", f"Preset '{preset_name}' saved successfully.")

    def delete_preset(self):
        preset_name = self.preset_var.get()
        if not preset_name:
            messagebox.showerror("Error", "Please select a preset to delete.")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the preset '{preset_name}'?"):
            self.preset_manager.delete_preset(preset_name)
            self.presets = self.preset_manager.get_preset_names()
            self.update_preset_dropdown()
            messagebox.showinfo("Success", f"Preset '{preset_name}' deleted successfully.")

    def update_preset_dropdown(self):
        self.presets = self.preset_manager.get_preset_names()
        self.preset_dropdown['values'] = self.presets
        if self.presets:
            self.preset_var.set(self.presets[0])
        else:
            self.preset_var.set("")

    def apply_preset(self, event=None):
        preset_name = self.preset_var.get()
        preset = self.preset_manager.get_preset(preset_name)
        for param, value in preset.items():
            if param in self.parameters and isinstance(value, (int, float)):
                self.parameters[param].var.set(value)
            else:
                print(f"Warning: Parameter '{param}' in preset '{preset_name}' is invalid or has an incorrect type.")

    def setup_variables(self):
        self.cancel_requested = False
        self.last_prompt = ""
        self.last_generated_text = ""
        self.grammar_errors = []  # Store grammar errors
        self.context_viewer_open = False
        self.story_info_open = False

    def prepare_prompt(self, prompt):
        """
        Prepares the final prompt for text generation by integrating memory text, author notes, and lorebook entries.

        Args:
            prompt (str): The original prompt text from the text widget.

        Returns:
            str: The final prompt with integrated contextual information at the correct positions.

        Notes:
            - Order -> Memory Text -> Lorebook Entries -> Prompt -> Author Notes
        """
        # Retrieve memory text and author notes text, defaulting to empty strings if not set
        memory_text = getattr(self, 'memory_text', '')
        author_notes_text = getattr(self, 'author_notes_text', '')

        # Retrieve lorebook entries widgets
        lorebook_entries = self.lorebook_entries_widgets

        # Construct lorebook text only if there are actual entries
        lorebook_text = ""
        if lorebook_entries:
            lorebook_text = "\n".join(
                f"Entry {idx+1}: {name_entry.get('1.0', tk.END).strip()}\n{content_entry.get('1.0', tk.END).strip()}"
                for idx, (_, name_entry, content_entry) in enumerate(lorebook_entries)
                if name_entry.get('1.0', tk.END).strip() and content_entry.get('1.0', tk.END).strip()
            )

        # Integrate memory text and lorebook text into the prompt if they are not empty
        if memory_text:
            prompt = memory_text + "\n" + lorebook_text + "\n" + prompt
        elif lorebook_text:
            prompt = lorebook_text + "\n" + prompt

        # Integrate author notes text into the prompt if it is not empty
        if author_notes_text:
            paragraphs = re.split(r'(?<=[.!?])\s+', prompt)
            if len(paragraphs) > 1:
                last_two_paragraphs = paragraphs[-2:]
                rest_of_prompt = paragraphs[:-2]
                prompt = '\n'.join(rest_of_prompt + [last_two_paragraphs[0], author_notes_text, last_two_paragraphs[1]])
            else:
                prompt = '\n'.join([author_notes_text] + paragraphs)

        return prompt

    def show_context_viewer(self):
        if self.context_viewer_open:
            return

        self.buttons['context_viewer'].disable()
        raw_prompt = self.text_widget.get("1.0", tk.END).strip()
        context_prompt = self.prepare_prompt(raw_prompt)

        popup = tk.Toplevel(self.root)
        popup.title("Context Viewer")
        popup.geometry("600x400")
        popup.protocol("WM_DELETE_WINDOW", lambda: self.close_context_viewer(popup))

        context_text = scrolledtext.ScrolledText(popup, wrap='word', width=80, height=20)
        context_text.pack(expand=True, fill='both', side='left', padx=10, pady=10)
        context_text.insert(tk.END, context_prompt)
        context_text.configure(state='disabled')  # Make the text read-only

        self.context_viewer_open = True

    def close_context_viewer(self, popup):
        popup.destroy()
        self.buttons['context_viewer'].enable()
        self.context_viewer_open = False

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
        raw_prompt = self.text_widget.get("1.0", tk.END).strip()
        self.last_prompt = raw_prompt
        prepared_prompt = self.prepare_prompt(raw_prompt)
        self.cancel_requested = False
        self.text_widget.tag_remove('highlight', '1.0', tk.END)

        # Disable the generate button to prevent multiple requests
        self.buttons['generate'].disable()

        threading.Thread(target=self.generate_text, args=(prepared_prompt,)).start()
        self.save_session()

    def cancel_generation(self):
        self.cancel_requested = True
        if config['USE_TTS']:
            stop_audio()
        self.buttons['generate'].enable()

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
                    APIHandler.close_session(response)  # Close the request to abort the server-side processing
                    break
                if event.data:
                    try:
                        if event.data.strip() == '[DONE]':
                            break
                        payload = json.loads(event.data)
                        if 'text' in payload['choices'][0]:
                            chunk = payload['choices'][0]['text']
                            if chunk in ['<|eot_id|>', '<|im_end|>']:
                                break
                            self.last_generated_text += chunk
                            self.text_widget.insert(tk.END, chunk, 'highlight')  # Tag new text
                            if self.style_manager.dark_mode == False:
                                self.text_widget.tag_config('highlight', foreground='blue')  # Style the tag
                            else:
                                self.text_widget.tag_config('highlight', foreground='cyan')
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

        finally:
            self.buttons['generate'].enable()

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
        self.font_size = min(32, self.font_size + 2)  # cap font size at 32
        self.text_widget.config(font=("TkDefaultFont", self.font_size))

    def decrease_font_size(self):
        self.font_size = max(8, self.font_size - 2)  # floor font size at 8
        self.text_widget.config(font=("TkDefaultFont", self.font_size))

    def story_info(self):
        if self.story_info_open:
            return

        self.buttons['info'].disable()
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

        self.story_info_open = True

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
        self.memory_text = self.memory_entry.get("1.0", tk.END).strip()
        self.author_notes_text = self.authornotes_entry.get("1.0", tk.END).strip()

        self.lorebook_entries_data = {}
        for _, name_entry, content_entry in self.lorebook_entries_widgets:
            name = name_entry.get("1.0", tk.END).strip()
            content = content_entry.get("1.0", tk.END).strip()
            if name and content:
                self.lorebook_entries_data[name] = content

        self.save_session()
        popup.destroy()
        self.buttons['info'].enable()
        self.story_info_open = False

    def show_markdown_viewer(self):
        text = self.text_widget.get("1.0", tk.END).strip()
        show_markdown_viewer(self.root, text)

if __name__ == "__main__":
    root = tk.Tk()
    app = TextGeneratorApp(root)
    root.mainloop()