# PRP Runner (`prp-runner`)

A standalone Python CLI tool whose sole responsibility is to execute a pre-existing `.md` PRP file using a specified backend agent CLI. It is completely agnostic to how the PRP was created and functions as a secure, reliable "last-mile" execution engine.

## Core Principles

- **Simple:** The tool has one job: execute a PRP file.
- **Secure:** It avoids shell injection by not using a shell to construct commands.
- **Agnostic:** It does not know or care how the PRP was generated.
- **Zero-Dependency:** It relies only on the Python standard library.

## Usage

```bash
prp-runner --prp <path_to_prp_file.md> --runner <runner_name>
```
