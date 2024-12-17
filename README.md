# EditorConfig Generator

A Python tool to heuristically generate an `.editorconfig` file based on existing code styles in your project.

## Features

- **Automatic Detection**: Analyzes your codebase to detect indentation styles, EOL characters, charset, and more.
- **Custom Path Scanning**: Specify directories or files to scan using glob patterns.
- **Accurate Binary Detection**: Utilizes `libmagic` for reliable binary file detection.
- **Easy Integration**: Helps maintain consistent coding styles across different editors and IDEs.

## Installation

1. **Clone the Repository**:

```bash
git clone https://github.com/yourusername/editorconfig-generator.git
cd editorconfig-generator
```

2. **Install Dependencies**:

It's recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

**Note**: Ensure libmagic is installed on your system.

- **macOS**: 
```bash
brew install libmagic
```

- **Ubuntu/Debian**: 
```bash
brew install libmagic
```

- **Windows**:

Install `python-magic-bin` as specified in requirements.txt or follow instructions [here](https://github.com/ahupp/python-magic).

## Usage

Run the script with optional path(s) or glob patterns:

```bash
python generate_editorconfig.py [paths...]
```

After running, an `.editorconfig` file will be generated in the current directory based on the analyzed files.

## Contributions

Contributions are welcome! Please open issues or submit pull requests for any improvements or bug fixes.


## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

