# Contributing to MechPulse

Thank you for your interest in contributing to **MechPulse** — the real-time industrial vibration monitoring and predictive maintenance system. We welcome contributions from developers, reliability engineers, and vibration analysts.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Fork and Clone](#fork-and-clone)
  - [Environment Setup](#environment-setup)
- [Development Workflow](#development-workflow)
  - [Branching Strategy](#branching-strategy)
  - [Running the Application](#running-the-application)
- [Code Style and Quality Standards](#code-style-and-quality-standards)
  - [Python Guidelines](#python-guidelines)
  - [C++ Guidelines](#c-guidelines)
- [Testing Requirements](#testing-requirements)
  - [Running Unit Tests](#running-unit-tests)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to `security@mechpulse.internal`.

---

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub: `https://github.com/mechpulse/mechpulse`
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/mechpulse.git
   cd mechpulse
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/mechpulse/mechpulse.git
   ```

### Environment Setup

#### Python Environment (Python 3.10+)

Create a virtual environment and install dependencies in editable mode with development tools:

```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Or on Linux / macOS
source .venv/bin/activate

# Install development dependencies
pip install --upgrade pip
pip install -e ".[dev]"
```

#### C++ Toolchain (C++17)

To build the native C++ DSP core engine:
- CMake 3.20+
- Modern C++ compiler supporting C++17 (`MSVC 2019+`, `GCC 9+`, or `Clang 10+`)

Build steps:
```bash
cmake -B build -S core-engine -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

---

## Development Workflow

### Branching Strategy

- Always create a new branch from `main`:
  ```bash
  git checkout main
  git pull upstream main
  git checkout -b feature/your-feature-name
  # or
  git checkout -b fix/issue-description
  ```
- Use descriptive branch prefixes:
  - `feature/` for new features or enhancements
  - `fix/` for bug fixes
  - `refactor/` for code refactoring
  - `docs/` for documentation updates
  - `test/` for testing additions

### Running the Application

To run the full stack with the built-in Python digital twin simulator:
```bash
python -m mechpulse --simulate
```

Or on Windows:
```cmd
run_demo.bat
```

---

## Code Style and Quality Standards

### Python Guidelines

- **Python Version**: Python 3.10+ compatibility is strictly required.
- **Type Hints**: Full PEP 484 type annotations for all function parameters and return values.
- **Docstrings**: Google or NumPy style docstrings for all public modules, classes, and methods.
- **Linter & Formatter**: Use **Ruff** for linting and formatting:
  ```bash
  ruff check src/ tests/
  ruff format --check src/ tests/
  ```
- **Type Checking**: Static analysis with **mypy**:
  ```bash
  mypy src/
  ```

### C++ Guidelines

- **Standard**: C++17 compliant.
- **Binary Struct Packing**: Any telemetry packet definitions must adhere to fixed alignment (`#pragma pack(push, 1)`) and exact byte limits (e.g. 1572 bytes for `VibrationPacket`).
- **Memory Management**: Zero memory leaks; prefer modern RAII, standard algorithms, and fixed-size buffers for edge DSP loops.
- **Naming Conventions**:
  - Types / Classes / Structs: `PascalCase`
  - Methods / Functions: `camelCase` or `snake_case` (consistent with existing module)
  - Constants: `SCREAMING_SNAKE_CASE`

---

## Testing Requirements

We enforce high test reliability, especially for DSP calculations, packet parsing, and ISO 10816 standards compliance.

### Running Unit Tests

Run test suites and generate coverage reports using `pytest`:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=mechpulse --cov-report=term-missing
```

When contributing:
- All existing tests must pass.
- New features or bug fixes must include corresponding tests under `tests/`.
- Never submit PRs with failing tests or untested edge cases.

---

## Commit Message Guidelines

MechPulse adheres to the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

Format:
```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process, CI configuration, or dependencies

### Examples

```
feat(dsp): implement Cooley-Tukey radix-2 FFT algorithm
fix(iso): correct Zone B threshold boundary comparison
docs(arch): update UDP packet memory layout diagram
test(packet): add roundtrip serialization pytest test
```

---

## Pull Request Process

1. **Keep PRs Focused**: One logical change per pull request.
2. **Self-Review**: Review your own diff before marking PR as ready for review.
3. **CI Checks**: Ensure CI tests, Ruff linting, and mypy pass locally before pushing.
4. **Fill PR Template**: Provide clear descriptions of the problem, solution, and testing performed.
5. **Review Feedback**: Address reviewer feedback promptly. Maintain a polite and professional tone.

---

## Reporting Issues

- **Bug Reports**: Use our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- **Feature Requests**: Use our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
- **Security Vulnerabilities**: Refer to [SECURITY.md](SECURITY.md) to report privately.
