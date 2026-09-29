## Description
Please include a summary of the changes and the related issue/feature. Mention any relevant motivation, design trade-offs, and context.

Fixes #(issue number)

## Type of Change
Please mark options that apply:
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Performance optimization (DSP or UI rendering speedup)
- [ ] Refactoring (code improvements without functional changes)
- [ ] Documentation update
- [ ] CI / Build tooling update

## Component Affected
- [ ] C++ Core DSP Engine (`core-engine/`)
- [ ] UDP Telemetry & Network Receiver (`src/mechpulse/core/receiver.py`)
- [ ] ISO 10816 Evaluator & Diagnostics (`src/mechpulse/core/iso_evaluator.py`)
- [ ] Digital Twin Simulator (`src/mechpulse/core/simulator.py`)
- [ ] PySide6 Industrial Dashboard & Widgets (`src/mechpulse/ui/`)
- [ ] Unit & Integration Tests (`tests/`)

## Testing Done
Please describe the tests that you ran to verify your changes:
- [ ] Pytest test suite executed successfully (`pytest tests/`)
- [ ] Ruff linting passed (`ruff check src/ tests/`)
- [ ] Static type check passed (`mypy src/`)
- [ ] Verified live data stream rendering at 20 FPS without UI freezes
- [ ] Tested roundtrip binary packet serialization / deserialization

## Checklist
- [ ] My code adheres to the project's style guidelines.
- [ ] I have performed a self-review of my own code.
- [ ] I have commented my code, particularly in complex mathematical/DSP sections.
- [ ] I have made corresponding changes to the documentation.
- [ ] My changes generate no new compiler warnings or linter errors.
- [ ] I have added tests that prove my fix is effective or that my feature works.
- [ ] New and existing unit tests pass locally with my changes.
