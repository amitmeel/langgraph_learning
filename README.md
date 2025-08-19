# LangGraph Learning Repository

[![Build Status](https://img.shields.io/github/actions/workflow/status/amitmeel/langgraph_learning/main.yml?branch=main)](https://github.com/amitmeel/langgraph_learning/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## 🚀 Description

This repository provides a comprehensive learning path for LangGraph - a framework for building stateful, multi-agent applications with Large Language Models (LLMs). Each module builds upon the previous one, taking you from basic concepts to advanced implementations including agents, workflows, and LangGraph Studio integration.

## 📋 Table of Contents

1. [Features](#-features)
2. [Tech Stack](#-tech-stack--key-dependencies)
3. [File Structure](#-file-structure-overview)
4. [Prerequisites](#-prerequisites)
5. [Installation](#-installation)
6. [Usage](#-usage--getting-started)
7. [Module Overview](#-module-overview)
8. [Configuration](#-configuration)
9. [LangGraph Studio](#-langgraph-studio)
10. [Troubleshooting](#-troubleshooting)
11. [Contributing](#-contributing)
12. [Resources](#-resources)
13. [License](#-license)
14. [Contact](#-contact)

## ✨ Features

- **Progressive Learning**: Structured modules from beginner to advanced concepts
- **Hands-on Examples**: Practical code examples for each LangGraph feature
- **Environment Setup**: Complete development environment configuration
- **LangGraph Studio Integration**: Visual debugging and workflow design
- **Best Practices**: Industry-standard patterns and practices
- **Production Ready**: Examples suitable for production deployment

## 🛠 Tech Stack / Key Dependencies

- **Python**: 3.11+
- **LangGraph**: Core framework for building agent workflows
- **LangChain**: Integration with various LLM providers
- **uv**: Fast Python package installer and resolver (recommended)
- **Poetry**: Alternative package management (optional)
- **Additional Dependencies**: Listed in `pyproject.toml`

## 📁 File Structure Overview

```text
.
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore patterns
├── .python-version          # Python version specification
├── README.md               # This comprehensive guide
├── hello.py                # Quick start example
├── pyproject.toml          # Project dependencies and metadata
├── requirements.txt        # Pip-compatible requirements
├── uv.lock                 # Lockfile for reproducible installs
├── module_0/               # Introduction to langgraph and Setup
├── module_1/               # LangGraph Concepts: router, chain, agent etc.
├── module_2/               # LangGraph Concepts: State and Memory
├── module_3/               # Langgraph concepts: breakpoints, streaming and human-in-loop
└── module_4/               # Multi-Agent Systems
                            (build your own research assistant with human-in-loop)
```

## 🔧 Prerequisites

- **Python 3.11 or higher**
- **Git** for cloning the repository
- **uv** (recommended) or **Poetry/pip** for dependency management
- **API Keys**: OpenAI, Anthropic, or other LLM provider APIs
- **Optional**: Docker for containerized development

## 📦 Installation

### Method 1: Using uv (Recommended)

1. **Install uv** (if not already installed):
   ```bash
   # macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Alternative: using pip
   pip install uv
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/amitmeel/langgraph_learning.git
   cd langgraph_learning
   ```

3. **Set up the project environment**:
   ```bash
   # Initialize the project (creates .venv and installs dependencies)
   uv sync
   
   # Activate the virtual environment
   source .venv/bin/activate  # Linux/macOS
   # OR
   .venv\Scripts\activate     # Windows
   ```

### Method 2: Using Poetry

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone and setup**:
   ```bash
   git clone https://github.com/amitmeel/langgraph_learning.git
   cd langgraph_learning
   poetry install
   poetry shell
   ```

### Method 3: Using pip

1. **Clone and setup**:
   ```bash
   git clone https://github.com/amitmeel/langgraph_learning.git
   cd langgraph_learning
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # OR
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

## 🚦 Usage / Getting Started

### 1. Environment Configuration

Create your environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Gemini LLM providers 
GOOGLE_API_KEY=your_google_api_key_here

# tavily (for Web search)
TAVILY_API_KEY =  your_tavily_api_key_here

#  if you do not wish to have data traced to LangSmith
LANGSMITH_TRACING = false
```

### 2. Quick Start

Test your setup with the hello world example:
```bash
python hello.py
```

### 3. Running Individual Modules

Each module is self-contained and can be run independently:

```bash
# Navigate to a specific module
cd module_0
python main.py

# Or run from the root directory
python -m module_0.main
```

### 4. Adding New Dependencies

When working with the project, add dependencies using uv:
```bash
# Add a new dependency
uv add package_name

# Add a development dependency
uv add --dev pytest

# Add with version constraint
uv add "requests>=2.28.0"
```

## 📚 Module Overview

### Module 0: Introduction and Setup
- **Purpose**: Environment setup and basic LangGraph introduction
- **Key Concepts**: Installation, configuration, first LangGraph application
- **Files**: Basic setup scripts and environment validation
- **Learning Outcomes**: Understanding LangGraph fundamentals

### Module 1: Basic LangGraph Concepts
- **Purpose**: Core concepts and simple workflows
- **Key Concepts**: Nodes, edges, state, simple chains
- **Files**: Basic graph construction examples
- **Learning Outcomes**: Building your first stateful workflows

### Module 2: State Management and Memory
- **Purpose**: Advanced state management and complex flows
- **Key Concepts**: State persistence, conditional routing, loops, Memory
- **Files**: State management patterns and flow control
- **Learning Outcomes**: Managing complex application state

### Module 3: Streaming, Breakpoints and Human-in-loop
- **Purpose**: How to stream, how to ad breakpoints using human-in-loop in a graph
- **Key Concepts**: streaming, breakpoints, dynamic breakpoints and human-in-loop
- **Files**: streaming and human-in-loop examples and best practices
- **Learning Outcomes**: How to stream the graph states and how to add human-in-loop in complex workflow


### Module 4: Multi-Agent Systems
- **Purpose**: Building systems with multiple AI agents
- **Key Concepts**: Agent coordination, message passing, collaboration
- **Files**: Multi-agent examples and coordination patterns
- **Learning Outcomes**: Creating collaborative AI systems


## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `TAVILY_API_KEY` | Tavily API key | Yes | `sk-...` |
| `GOOGLE_API_KEY` | Google API key | Optional | `sk-ant-...` |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing | Optional | `true` |

### Project Configuration

The `pyproject.toml` file contains all project metadata and dependencies. Key sections:

```toml
[project]
name = "langgraph-learning"
version = "0.1.0"
description = "langgraph learning"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "langchain-community>=0.3.27",
    "langchain-core>=0.3.74",
    "langchain-google-genai>=2.1.9",
    "langchain-openai>=0.3.29",
    "langchain-tavily>=0.2.11",
    "langgraph>=0.6.4",
    "langgraph-checkpoint-sqlite>=2.0.11",
    "langgraph-cli[inmem]>=0.3.6",
    "langgraph-prebuilt>=0.6.4",
    "langgraph-sdk>=0.2.0",
    "langsmith>=0.4.13",
    "mlflow>=3.2.0",
    "notebook>=7.4.5",
    "pydantic>=2.11.7",
    "python-dotenv>=1.1.1",
    "tavily-python>=0.7.10",
    "trustcall>=0.0.39",
    "wikipedia>=1.4.0",
]
```

## 🎨 LangGraph Studio

LangGraph Studio provides a visual interface for designing and debugging workflows.

### Installation and Setup

1. **Install LangGraph CLI**:
   ```bash
   uv add "langgraph-cli[inmem]"
   # or
   pip install --upgrade "langgraph-cli[inmem]"
   ```

2. **Start LangGraph Studio**:
   ```bash
   langgraph dev
   ```

   **NOTE**: Please make sure you create a ```langgrpah.json``` file which contains atleast below mentioned keys
   ```
    {
        "dependencies": ["../"],  # path of .toml file
        "graphs": {"graph": "../simple_graph.py:graph"}, # path of your graph
        "env": "../.env" # path of .env file if any environment variable is required
    }
   ```

3. **Access the Interface**:
   run the below command from the folder where you have your langgrpah.json file:
   ```bash
   langgraph dev
   ```

   or you can follow the official documentation: [langgraph studio](https://docs.langchain.com/langgraph-platform/local-server)


### Features

- **Visual Workflow Designer**: Drag-and-drop interface for building graphs
- **Real-time Debugging**: Step-through execution with state inspection
- **Performance Monitoring**: Track execution time and resource usage
- **Integration Testing**: Test your workflows with different inputs

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Reinstall dependencies
uv sync --reinstall
```

#### 2. API Key Issues

##### Test gemini API connectivity
- goto project root folder and run 
```bash
python hello.py
```

#### 3. Module Import Issues
```bash
# Run from the project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%cd%          # Windows
```

#### 4. Version Conflicts
```bash
# Clean install with uv
rm -rf .venv uv.lock
uv sync
```

### Getting Help

1. Check the [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
2. Review module-specific README files
3. Check the [Issues](https://github.com/amitmeel/langgraph_learning/issues) section
4. Join the [LangChain Discord](https://discord.gg/langchain)

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Set up development environment**:
   ```bash
   uv sync --group dev
   ```
4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Code Standards

- **Format**: Use `black` for code formatting
- **Linting**: Use `ruff` for linting
- **Type Checking**: Use `mypy` for type checking
- **Testing**: Write tests using `pytest`

```bash
# Run quality checks
uv run black .
uv run ruff check .
uv run mypy .
uv run pytest
```

### Pull Request Process

1. Update documentation for any new features
2. Add tests for new functionality
3. Ensure all checks pass
4. Update the relevant module README
5. Submit pull request with clear description

## 📖 Resources

### Official Documentation
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangChain Documentation](https://python.langchain.com/)
- [LangSmith Documentation](https://docs.smith.langchain.com/)

### Learning Resources
- [LangChain Academy](https://academy.langchain.com/)
- [LangGraph Tutorials](https://github.com/langchain-ai/langgraph/tree/main/examples)
- [Community Examples](https://github.com/langchain-ai/langchain/tree/master/templates)

### Tools
- [uv Documentation](https://docs.astral.sh/uv/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [LangGraph Studio](https://docs.langchain.com/langgraph-studio)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **Author**: Amit Meel
- **Project**: [GitHub Repository](https://github.com/amitmeel/langgraph_learning)
- **Issues**: [Report Issues](https://github.com/amitmeel/langgraph_learning/issues)
- **Discussions**: [GitHub Discussions](https://github.com/amitmeel/langgraph_learning/discussions)

---

**Happy Learning! 🚀**

*This repository is part of the growing LangGraph community. Star ⭐ the repo if you find it useful!*