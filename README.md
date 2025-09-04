# Auto Email

## How to Run

- Python 3.12
- GLM api key
- Gmail API

### Using uv (Recommended)

```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
uv pip install -r requirements.txt

# Initialize vector database
python create_index.py

# Run the application
python main.py
```

### Using pip

```bash
pip install -r requirements.txt
python create_index.py
python main.py
```
