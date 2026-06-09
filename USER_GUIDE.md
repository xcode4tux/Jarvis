# Jarvis User Guide

Welcome to **Jarvis** (OpenJarvis) — a modular, local-first AI assistant backend with composable intelligence primitives, agents, tools, memory indexing, and GPU-accelerated local inference.

This guide covers installation, local GPU configuration, CLI usage, starting the API server, running the browser UI, and update/diagnostics workflows.

---

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Configuration & Local GPU Acceleration](#3-configuration--local-gpu-acceleration)
4. [Running Jarvis](#4-running-jarvis)
   - [CLI Interface (Ask & Chat)](#cli-interface-ask--chat)
   - [API Server (OpenAI Compatible)](#api-server-openai-compatible)
   - [React Web UI (Browser App)](#react-web-ui-browser-app)
5. [Memory Indexing & RAG](#5-memory-indexing--rag)
6. [Updating Jarvis](#6-updating-jarvis)
7. [System Diagnosis & Troubleshooting](#7-system-diagnosis--troubleshooting)

---

## 1. Prerequisites

Before installing Jarvis, ensure your system has:
* **Python**: Version `3.10` to `3.13`.
* **Rust Toolchain**: Required to compile the Rust-Python bridge (`openjarvis_rust`).
* **Node.js**: Version `22+` (optional, required for ClaudeCodeAgent and WhatsApp bridge).
* **Ollama**: For local model execution. Ensure it is installed and running:
  ```bash
  ollama serve
  ```

---

## 2. Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/xcode4tux/Jarvis.git
   cd Jarvis
   ```

2. **Set Up Python Environment**:
   Initialize and sync virtual environment with `server` and `dev` extras:
   ```bash
   uv sync --extra server --extra dev
   ```

3. **Build the Rust Extension**:
   Compile the mandatory Rust-Python bridge module:
   ```bash
   uv run maturin develop -m rust/crates/openjarvis-python/Cargo.toml
   ```

4. **Verify the Installation**:
   Ensure the CLI is working and the Rust bridge loads:
   ```bash
   uv run jarvis --help
   ```

---

## 3. Configuration & Local GPU Acceleration

On first run, initialize the configuration file. Jarvis will auto-detect your system's CPU, RAM, and GPU capabilities:
```bash
uv run jarvis init
```
This generates a config file at `~/.openjarvis/config.toml`.

### Optimizing for Local GPU (AMD / Vulkan / NVIDIA)
To ensure Jarvis utilizes your local GPU rather than remote engines, set your default engine to `ollama` and select a model that fits in VRAM (e.g. `qwen3.5:4b` or `qwen3.5:9b`).

Edit your `~/.openjarvis/config.toml` file to include:
```toml
[engine]
default = "ollama"

[engine.ollama]
host = "http://localhost:11434"

[intelligence]
default_model = "qwen3.5:4b"        # Local consumer-GPU model
preferred_engine = "ollama"

[updates]
auto_update = true
```

Make sure you have pulled the model locally:
```bash
ollama pull qwen3.5:4b
```

---

## 4. Running Jarvis

### CLI Interface (Ask & Chat)
You can query Jarvis directly from the terminal. 

* **Simple Question**:
  ```bash
  uv run jarvis ask "Explain quantum entanglement in simple terms"
  ```
* **Agentic Execution with Tools** (runs a multi-turn planning loop):
  ```bash
  uv run jarvis ask --agent orchestrator --tools calculator,think "What is the square root of 144 times 42?"
  ```
* **Interactive Chat**:
  ```bash
  uv run jarvis chat --model qwen3.5:4b
  ```

### API Server (OpenAI Compatible)
Jarvis can run as an OpenAI-compatible web API server, enabling you to connect it to external developer interfaces, IDE extensions, or scripts.

* **Start the server**:
  ```bash
  uv run jarvis serve --port 8000
  ```
* **Query the API**:
  ```bash
  curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "qwen3.5:4b",
      "messages": [{"role": "user", "content": "Hello!"}]
    }'
  ```

### React Web UI (Browser App)
To launch the full desktop-grade browser app containing a modern chat UI, tool telemetry, and real-time energy charts:
```bash
./scripts/quickstart.sh
```
This runs the API server on port `8000` and starts the React frontend at [http://localhost:5174](http://localhost:5174).

---

## 5. Memory Indexing & RAG

Jarvis supports local Retrieval-Augmented Generation (RAG). You can index folders or documents into a local SQLite FTS database, and Jarvis will automatically inject matching context chunks into your queries.

* **Index a Folder**:
  ```bash
  uv run jarvis memory index ./docs/
  ```
* **Search Memory Chunks**:
  ```bash
  uv run jarvis memory search "Ollama host configuration"
  ```
* **Disable Context Injection** (runs a clean request without RAG context):
  ```bash
  uv run jarvis ask --no-context "Hello"
  ```

---

## 6. Updating Jarvis

You can check for updates and upgrade your installation using the built-in self-update function:

* **Check for updates** (simulates update detection without executing it):
  ```bash
  uv run jarvis self-update --check
  ```
* **Upgrade the App**:
  ```bash
  uv run jarvis self-update
  ```
  For editable checkouts, this executes a safe git pull and runs `uv sync --extra server --extra dev` to pull the latest changes while preserving your server packages.

---

## 7. System Diagnosis & Troubleshooting

If you run into issues (e.g. missing extensions, unreachable backends), run the doctor utility:
```bash
uv run jarvis doctor
```
This diagnostic tool performs checking on:
* Python and Node.js versions.
* Config file syntax and loading.
* Health/reachability of configured engines.
* Available models.
* Status of background compilation and downloads.
