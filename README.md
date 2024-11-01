# AI Writing Notebook UI

![AI Writing Notebook UI Screenshot](images/UI.JPG)

## Description
A GUI-based AI writing assistant that supports text generation, session saving and loading, advanced options toggling, and voice generation for the generated text.

## Table of Contents
- [Description](#description)
- [Features](#features)
- [Installation and Usage](#installation-and-usage)
  - [Starting the Application](#starting-the-application)
  - [Using the Application](#using-the-application)
- [What preset I choose?](#what-preset-i-choose)
    - [Preset Selection Guide](#preset-selection-guide)
    - [Additional Tips for Choosing a Preset](#additional-tips-for-choosing-a-preset)
- [Configuration](#configuration)
  - [Session Management](#session-management)
  - [Advanced Options](#advanced-options)
  - [Voice Generation](#voice-generation)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)


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

## **What Preset Should I Choose?**
------------------------------------
| **Preset** | **Description** | **Best For** | **Key Characteristics** |
| --- | --- | --- | --- |
| **Default** | Balanced creativity and coherence for general use. | **Most Tasks**, **Beginners** | Medium Temperature, Balanced Parameters |
| **NovelAI-Best Guess** | Tamed version of Default, more predictable. | **Consistency-Driven Tasks** | Higher Consistency, Lower Creativity |
| **NovelAI-Storywriter** | Coherent, focused, and less repetitive for storytelling. | **Storytelling**, **Structured Content** | Smaller Token Pool, Low Temperature, High Repetition Penalty |
| **Starchat (Qwen2 variant)** | Deterministic tasks without min_p. | **Specific, Predictable Outcomes** | High Predictability, Low Creativity |
| **Lunaris & Universal Fight** | Experimental, low control, potentially chaotic. | **Experimental Writing**, **High Risk, High Reward** | Very Low Control, High Potential for Incoherence |
| **Asterism** | Highly randomized, controlled chaos. | **Highly Creative, Abstract Content** | Very High Temperature, Intense Token Filter |
| **MagnumHotLane & Texy_norep** | Balanced randomness for diverse responses. | **Tasks Requiring Variance**, **Intermediate Users** | Medium-High Temperature, Lower min_p for Texy |
| **Nexus Stable Event & Lzlv Universal** | Stable, coherent outputs similar to Storywriter. | **Consistent, Structured Writing** | Similar to Storywriter, but Less Effective |

### **Preset Selection Guide**
-----------------------------

* **Need a starting point?** → **Default**
* **Want something more predictable?** → **NovelAI-Best Guess** or **NovelAI-Storywriter**
* **Writing a story?** → **NovelAI-Storywriter**
* **Math or code generation?** → **Starchat** or just pick one of the more predictable presets
* **Want to unleash chaos?** → **Lunaris & Universal Fight** or **Asterism** for a controlled chaos
* **Need a balanced randomness?** → **MagnumHotLane & Texy_norep**

### **Additional Tips for Choosing a Preset**

* **Beginners**: Start with **Default**, but consider **NovelAI-Storywriter** when things start to get repetitive.
* **Consistency**: **NovelAI-Best Guess** and **NovelAI-Storywriter** are your best bets.
* **Creativity**: **Asterism** and **Lunaris & Universal Fight** are the most creative presets.

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