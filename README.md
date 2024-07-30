# AI Writing Notebook UI

![AI Writing Notebook UI Screenshot](images/UI.JPG)

## Description
A GUI-based AI writing assistant that supports text generation, session saving and loading, advanced options toggling, and voice generation for the generated text.

## Features
- **Text Generation:** Generates text based on the provided prompt using AI models.
- **Session Management:** Saves and loads the current session to resume writing from where you left off.
- **Advanced Options:** Provides additional settings that can be toggled on or off for more nuanced control over the text generation process.
- **Voice Generation:** Converts the generated text into speech for auditory feedback.
- **Accessibility:** Supports text font size adjustment for better readability, and the generated text is highlighted in blue for easy identification.

## Installation and Usage
### Starting the Application
- Rename `config.json.example` to `config.json` and fill in the required fields, leave `USE_TTS` as `false` if you don't have a NovelAI API key.
- For Windows users, you can simply run the `start.bat` file to start the application, at the first run it will install the required dependencies on a venv (isolated environment) and then ask you to press any key to continue before starting the application.
- For Linux and macOS users, be sure to make the script executable before running:
```bash
chmod +x install.sh
chmod +x start.sh
```
- Then you can run the `start.sh` script to install dependencies and start the application.

### Using the Application
- Write your initial prompt in the text area and click "Generate" to start the text generation process.
- Use the "Check Grammar" button to check for grammatical errors in the generated text.
- Adjust the text font size using the "+" and "-" buttons at the bottom right.
- If you have enabled TTS support, you can toggle the "Enable Audio" checkbox to hear the generated text.
- Save your session by closing the application or by using the buttons `Generate` and `Cancel` to save the current state of the text area.
- Load your session by reopening the application.

## Configuration
The application uses a `config.json` file for configuration. You can customize the following settings:
- `INFERMATIC_API_KEY`: Your Infermatic API key for accessing the AI models.
- `NOVELAI_API_KEY`: Your NovelAI API key for voice generation (optional).
- `USE_TTS`: Enable or disable text-to-speech functionality.

### Session Management
- The application automatically saves your session when you close the window.

### Advanced Options
- Toggle the advanced options to adjust parameters like temperature, top_k, presence_penalty, min_p, and top_p, etc. for more control over the text generation.

### Voice Generation
- If enabled, the generated text will be converted to speech using the voice generation feature.

## Requirements
- Python 3.x (Tested to work on 3.10 and 3.11)
- Tkinter (`sudo apt-get install python-tk` or `sudo apt-get install python3-tk` for python3) needed for linux users.

## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.