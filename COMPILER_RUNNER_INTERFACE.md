# `prp_compiler` and `prp_runner`: System Architecture and Interface

This document outlines the architecture of the PRP (Prompt-Response-Plan) execution system, which is composed of two distinct projects: `prp_compiler` and `prp_runner`. It details the responsibilities of each component and defines the interface point between them.

## Overview

The system is designed with a clear separation of concerns:

1.  **`prp_compiler`**: An AI-assisted authoring tool for creating and refining high-quality, machine-executable plans (PRPs).
2.  **`prp_runner`**: A simple, secure execution engine that runs a finalized PRP using a specified backend AI agent.

This separation allows for independent development and enhances modularity. The compiler can evolve with more sophisticated AI authoring features without affecting the stability and security of the runner.

---

## The `prp_compiler` Project

### Purpose

The primary role of the `prp_compiler` is to help a user transform a high-level goal into a detailed, step-by-step plan that an AI agent can execute reliably. It acts as an interactive development environment (IDE) for prompts.

### Core Functionality

- **Interactive Authoring**: Provides a CLI or interactive environment for users to draft and edit plans.
- **AI-Assisted Refinement**: Leverages an AI model (like Claude) to help break down goals, suggest steps, and format the plan correctly.
- **Validation & Formatting**: Ensures the final output is a well-structured Markdown file, ready for execution.

### Output

The sole output of the `prp_compiler` is a finalized PRP file, which is a Markdown file with a `.prp.md` or `.md` extension. This file contains the complete set of instructions for the AI agent.

---

## The `prp_runner` Project

### Purpose

The `prp_runner` is responsible for one thing: executing a finalized PRP file. It is designed to be a minimal, secure, and reliable engine that is completely agnostic to how the PRP was created.

### Core Functionality

- **PRP Execution**: Reads the content of a `.prp.md` file.
- **Runner Selection**: Uses a configurable backend (e.g., `claude-cli`) to execute the prompt.
- **Prompt Augmentation**: Wraps the PRP content within a configurable "system prompt" to provide high-level instructions and context to the AI agent before execution.
- **Secure Subprocess Execution**: Invokes the backend runner as a secure, non-blocking subprocess without using a shell.

### Input

The `prp_runner` takes a single `.prp.md` file as its primary input.

---

## Interface Point: The `.prp.md` File

The interface between the `prp_compiler` and `prp_runner` is the **PRP file itself**. This file serves as a simple, durable contract between the two systems.

- **Format**: The file is plain Markdown (`.md`). This makes it human-readable, easy to edit, and version-controllable.
- **Contract**:
    - The `prp_compiler`'s responsibility is to produce a UTF-8 encoded Markdown file containing the full prompt.
    - The `prp_runner`'s responsibility is to read this file's content and pass it to the chosen backend agent.

### Example Workflow

A typical workflow looks like this:

```
1. User defines a goal.
   |
   v
2. User interacts with `prp_compiler` to produce `my_plan.prp.md`.
   (AI-assisted authoring and refinement)
   |
   v
3. `prp_compiler` saves the finalized `my_plan.prp.md`.
   |
   v
4. User invokes `prp_runner --prp my_plan.prp.md --runner claude-cli`.
   |
   v
5. `prp_runner` reads the file, wraps it in a system prompt, and executes it with the `claude-cli` tool.
   |
   v
6. The AI agent performs the task.
```

This decoupled architecture ensures that as long as both components adhere to the simple contract of the `.prp.md` file, they can be developed and improved independently.
