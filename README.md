# Obsidian Backlink Automation Script 💎🔗 

This Python script automates the creation of backlinks in [Obsidian](https://obsidian.md/), a powerful note-taking application that uses plain text Markdown files. Backlinks are essential in Obsidian for connecting ideas and building a network of interconnected notes, making it easier to navigate your knowledge base.

## Features

- Automatically scans your Obsidian vault for notes.
- Identifies potential connections between notes based on keywords or titles.
- Creates backlinks between related notes, enhancing your note organization and knowledge management.
- Saves time by automating the backlink creation process.
- Try to create backlinks with acronyms depending of your notes names

## Prerequisites

- **Python 3.x**: Ensure you have Python installed on your system.
- **Obsidian**: This script works with Markdown files in your Obsidian vault.
- You can also add a plugin to Obsidian to launch the script from within the app.

## Installation

You only need the `linkify.py` file to run the script. You can download it directly from this repository. Then add it 
to your Obsidian .obsidian/scripts/python folder. You need [the complementary plugin to run the script from within Obsidian](obsidian://show-plugin?id=python-scripter).

## Usage

- ⚠️ **Important**: by default, the script is in safe mode which means it will create a backup of your vault before running (you can find it in the same directory as you vault). You can disable this by setting `SAFE_MODE = False` in the script. This is to ensure that you don't lose any data in case something goes wrong.

- For a single file, run the script with obsidian open and the file you want to link to open.

  ![Obsidian_wGsVu7F7sB](https://github.com/user-attachments/assets/3c477974-b890-4061-99e5-917939ae26fc)
  
- For the whole vault, run the script with obsidian open and no file open (you can open the graph view and it will count as no file open).

![Obsidian_6Pa1wBb9m8](https://github.com/user-attachments/assets/05b58f7d-e30e-4d45-9a80-0b439b505c83)

# Acknowledgements

This script was based on the code of [Onyr](https://github.com/0nyr)

## Contribution

Feel free to submit issues or pull requests if you'd like to contribute to the improvement of this script!

