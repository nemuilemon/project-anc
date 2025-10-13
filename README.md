# Project A.N.C. (Alice Nexus Core)

🧠 **AI-Powered Note-Taking and Content Analysis System**

[![Version](https://img.shields.io/badge/version-3.1.1-blue.svg)](https://github.com/project-anc)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![Flet](https://img.shields.io/badge/flet-0.28.3-green.svg)](https://flet.dev)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎉 What's New in v3.1.1

- 🏷️ **Tag Editing UI**: Full tag management with add/remove functionality in file context menu
- ⚙️ **Enhanced Settings**: Numeric text fields replace sliders for better control (accepts 0 and positive integers)
- 🔧 **Configuration Migration**: All settings now stored in `.env` file for easier management
- 📝 **Environment Variables**: Dynamic configuration with `ALICE_HISTORY_CHAR_LIMIT`, `COMPASS_API_*` variables

See [CHANGELOG.md](CHANGELOG.md) for complete release notes.

## ✨ Features

### 📝 Advanced Note Management
- **Multi-tab Editor** with syntax highlighting and auto-save
- **Instant Search** across all notes with real-time filtering
- **Archive System** for organizing completed or inactive notes
- **File Ordering** with move-to-top/bottom functionality
- **Smart File Operations** (create, edit, save, delete, rename)

### 🧠 AI-Powered Analysis (NEW!)
- **🏷️ Smart Tagging** - AI extracts relevant keywords and tags
- **📄 Intelligent Summarization** - Generate brief, detailed, or bullet-point summaries
- **😊 Sentiment Analysis** - Analyze emotional tone and intensity
- **🔌 Plugin Architecture** - Easily add new AI analysis types

### 🛡️ Enterprise-Grade Security
- **Input Validation** preventing XSS and injection attacks
- **Path Security** with directory traversal protection  
- **Transaction Safety** with automatic rollback on failures
- **Comprehensive Logging** across 6 specialized log categories

### ⚡ Performance & UX
- **Asynchronous Operations** - Non-blocking UI with progress tracking
- **Responsive Design** - Handles 1000+ files with minimal lag
- **Real-time Progress** - Visual feedback for all long-running operations
- **Error Recovery** - Graceful error handling with user guidance

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+** 
- **Ollama** (for AI features) - [Download here](https://ollama.com/download)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/project-anc.git
cd project-anc

# 2. Create and activate virtual environment
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS/Linux  
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install development dependencies
pip install -r requirements-dev.txt

# 5. Configure API keys
# Create .env file or set environment variable:
# GEMINI_API_KEY=your_api_key_here

# 6. Set up AI models (optional, for analysis plugins)
ollama pull gemma3:4b

# 7. Run the application
python main.py
```

### First Launch
1. The application will create a `notes` directory for your files
2. Start by clicking the **"+"** button to create your first note
3. Try the AI analysis features by selecting text and choosing an analysis type
4. Use the search bar to quickly find notes as your collection grows

## 🧠 AI Analysis System

Project A.N.C. features a modular AI analysis system powered by **Ollama**:

### Available Analysis Types

| Plugin | Description | Use Cases |
|--------|-------------|-----------|
| 🏷️ **Tagging** | Extract relevant keywords and tags | Content organization, SEO keywords |
| 📄 **Summarization** | Generate concise summaries | Quick reviews, executive summaries |
| 😊 **Sentiment** | Analyze emotional tone | Content mood, user feedback analysis |

### Usage Example

```python
# The AI system works seamlessly through the UI:
# 1. Select text in the editor
# 2. Choose analysis type from dropdown  
# 3. Click "AI Analysis" button
# 4. View results in formatted dialog

# Or use programmatically:
from ai_analysis import AIAnalysisManager

manager = AIAnalysisManager()
result = manager.analyze("Your content here", "tagging")
print(result.data["tags"])  # ['AI', 'automation', 'analysis']
```

## 📁 Project Structure

```
project-anc/
├── main.py                 # Application entry point
├── ui.py                   # User interface components  
├── handlers.py             # Event handling logic
├── logic.py                # Business logic and data management
├── security.py             # Security utilities and validation
├── async_operations.py     # Background processing
├── logger.py               # Comprehensive logging system
├── config.py               # Configuration settings
├── ai_analysis/            # AI analysis system
│   ├── __init__.py
│   ├── base_plugin.py      # Plugin interface
│   ├── manager.py          # AI manager
│   └── plugins/            # Analysis plugins
│       ├── tagging_plugin.py
│       ├── summarization_plugin.py
│       └── sentiment_plugin.py
├── docs/                   # Documentation
│   ├── AI_ANALYSIS_SYSTEM.md
│   ├── PLUGIN_DEVELOPMENT_GUIDE.md
│   ├── TESTING_GUIDE.md
│   └── SYSTEM_OVERVIEW.md
├── tests/                  # Test suite
└── requirements.txt        # Dependencies
```

## 🔧 Configuration

### Basic Configuration (`config.py`)
```python
# File Management
NOTES_DIR = "notes"              # Notes directory
ARCHIVE_DIR = "notes/.archive"   # Archive directory

# AI Configuration  
OLLAMA_MODEL = "llama3.1:8b"     # AI model for analysis

# Security Settings
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB max file size
ALLOWED_EXTENSIONS = [".md", ".txt"]
```

### Ollama Setup
```bash
# Install Ollama from https://ollama.com/download

# Pull recommended models
ollama pull llama3.1:8b    # Primary recommendation (4GB)
ollama pull gemma2:9b      # Alternative option (5GB)

# Start Ollama service
ollama serve

# Verify installation
ollama list
```

## 🧪 Testing

The project includes comprehensive testing:

```bash
# Run integration tests
python test_basic_integration.py

# Run component tests  
python test_working_components.py

# Run full test suite in virtual environment
./test_in_venv.bat            # Windows
bash test_in_venv.bat         # macOS/Linux
```

### Test Coverage
- ✅ **Basic Integration**: Core imports, AI manager, AppLogic integration
- ✅ **Component Tests**: Plugin interface, manager functionality, UI structure
- ✅ **Virtual Environment**: Clean dependency validation
- ✅ **Error Scenarios**: Comprehensive error handling validation

## 🔌 Plugin Development

Create custom AI analysis plugins easily:

```python
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult

class MyCustomPlugin(BaseAnalysisPlugin):
    def __init__(self):
        super().__init__(
            name="my_custom",
            description="My custom analysis",
            version="1.0.0"
        )
    
    def analyze(self, content: str, **kwargs) -> AnalysisResult:
        # Your analysis logic here
        return self._create_success_result(
            data={"result": "analysis_output"},
            message="Analysis completed"
        )
```

See the [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT_GUIDE.md) for detailed instructions.

## 📊 Performance

| Operation | Performance |
|-----------|-------------|
| **Startup Time** | 2-3 seconds (cold start) |
| **File Loading** | 1000+ files with minimal lag |
| **Search/Filter** | Instant results |
| **AI Analysis** | 2-8 seconds (depends on content) |
| **Memory Usage** | 50-100MB baseline |

## 🛡️ Security Features

- **🔒 Input Validation** - Comprehensive validation for all user inputs
- **🚫 Path Traversal Protection** - Prevents directory traversal attacks
- **💾 Transaction Safety** - Atomic operations with rollback capability
- **📋 Audit Logging** - Complete security event logging
- **🔐 Local-First** - No external data transmission (except Ollama)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [System Overview](docs/SYSTEM_OVERVIEW.md) | Complete system architecture |
| [AI Analysis System](docs/AI_ANALYSIS_SYSTEM.md) | AI plugin system details |
| [Plugin Development](docs/PLUGIN_DEVELOPMENT_GUIDE.md) | Create custom plugins |
| [Testing Guide](docs/TESTING_GUIDE.md) | Testing procedures |
| [API Reference](docs/API_REFERENCE.md) | Complete API documentation |

## 🎯 Use Cases

### 📝 Personal Note-Taking
- **Daily Journaling** with sentiment tracking
- **Research Notes** with automatic tagging
- **Meeting Minutes** with AI summarization

### 💼 Professional Documentation  
- **Technical Documentation** with readability analysis
- **Project Notes** with intelligent organization
- **Content Creation** with SEO tag generation

### 🎓 Academic Research
- **Literature Reviews** with automatic summarization
- **Research Papers** with sentiment analysis
- **Study Notes** with smart categorization

## 🗺️ Roadmap

### ✅ Completed (v3.1.1 - October 2025)
- Tag editing UI with full CRUD operations
- Text input fields for settings (replaced sliders)
- Complete .env file migration for all dynamic settings
- Environment variable support in config.py
- Multi-conversation tab management with persistence
- OpenAI integration alongside Google Gemini

### ✅ Completed (v3.0.0 - September 2025)
- Modular AI analysis system with real Ollama integration
- Plugin-based architecture with auto-discovery
- Centralized state management
- Comprehensive security and error handling
- Full virtual environment testing validation

### 🔄 In Progress (v3.2.0 - Q4 2025)
- **Additional AI Plugins**: Language detection, readability analysis
- **UI Enhancements**: Dark mode, customizable themes
- **Export Features**: PDF export, HTML conversion
- **Advanced Search**: Operators, saved searches

### 🔮 Future (v3.0.0 - 2026)
- **Cloud Integration**: Optional backup and sync
- **Collaboration**: Multi-user support
- **Mobile Apps**: iOS and Android versions
- **API Development**: REST API for integrations

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Follow the plugin development guide** for AI features
4. **Add comprehensive tests** for your changes
5. **Update documentation** as needed
6. **Submit a pull request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests before contributing
python -m pytest tests/

# Follow code style guidelines
black .
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Flet](https://flet.dev)** - Beautiful Python UI framework
- **[Ollama](https://ollama.com)** - Local AI model management
- **[TinyDB](https://tinydb.readthedocs.io)** - Simple document database
- **Open Source Community** - For inspiration and best practices

## 📞 Support

- **📖 Documentation**: Check the [docs](docs/) directory
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/your-username/project-anc/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/your-username/project-anc/discussions)
- **💬 Community**: [Discord Server](https://discord.gg/project-anc)

---

**Built with ❤️ for productive note-taking and intelligent content analysis**

⭐ **Star this repository if you find it helpful!**