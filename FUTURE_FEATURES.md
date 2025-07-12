# Future Features for `prp_runner`

This document lists features that were present in the original inspiration runner script but have not yet been implemented in this project. They are candidates for future development.

### 1. Interactive Mode

- **Description:** The original script included an `--interactive` flag. When used, it would launch the agent in a chat mode, allowing the user to have a continuous, back-and-forth conversation with the AI. Our current implementation only supports a one-shot, non-interactive execution.

### 2. Advanced Output Formatting

- **Description:** The original script supported structured output formats via the `--output-format` flag with `json` and `stream-json` options. This included logic to parse the JSON from the agent, print summaries to stderr, and forward the structured data to stdout. Our tool currently only streams the raw text output.

### 3. Prompt Augmentation with Meta-Header

- **Description:** The original script prepended a detailed `META_HEADER` to every PRP. A basic version of this has been implemented via the configurable `system_prompt_template` in `default_runners.json`. This could be enhanced in the future to match the original's more detailed, structured guidance for the AI.

### 4. Working Directory Management

- **Description:** Before executing the agent, the original script would change the current working directory to the project's root. This is a critical feature that ensures any relative paths mentioned in the PRP (e.g., file paths to be edited) are resolved correctly. Our runner does not currently do this.

### 5. Enhanced CLI Arguments

- **PRP Shorthand:** The original script had a `--prp <name>` argument that would automatically look for `PRPs/<name>.md`, which is more convenient than providing the full path every time.
- **Tool Permissions:** The original script explicitly passed a list of allowed tools to the agent via a command-line argument (e.g., `--allowedTools Edit,Bash,...`). Our `default_runners.json` could be extended to support this for more fine-grained control.
