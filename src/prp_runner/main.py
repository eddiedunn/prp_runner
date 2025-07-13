import argparse
import json
import subprocess
import sys
from pathlib import Path
import importlib.resources  # [+] Import the standard library for package data


def get_runner_manifest_path() -> Path:
    """
    Return the path to the default_runners.json file using standard package resource logic.
    """
    # [+] Use importlib.resources to safely locate data files within the package.
    # This is the modern, standard way and is more robust than relative pathing.
    try:
        return importlib.resources.files('prp_runner.data').joinpath('default_runners.json')
    except (ModuleNotFoundError, FileNotFoundError):
        # Fallback for when the package might not be installed correctly, though unlikely.
        # This also helps keep the original logic for edge cases.
        print("Warning: Could not find package data. Falling back to project structure path.", file=sys.stderr)
        return Path(__file__).parent / "data" / "default_runners.json"


def load_runners(manifest_path: Path) -> dict:
    """Load the runner configurations from the JSON manifest."""
    if not manifest_path.exists():
        # This should be handled by the caller, but for now, we'll exit.
        print(f"Error: Runner manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)
    # [+] Use .open('r') which is the standard way to open a Path-like object from importlib
    with manifest_path.open("r") as f:
        try:
            runners_list = json.load(f)
            runners_dict = {}
            for item in runners_list:
                runners_dict[item["runner_name"]] = {
                    "command_template": item["command_template"],
                    "system_prompt_template": item.get("system_prompt_template")
                }
            return runners_dict
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error: Invalid format in {manifest_path}: {e}", file=sys.stderr)
            sys.exit(1)


def run_from_args(argv: list[str] | None = None, manifest_path: Path | None = None) -> int:
    """
    Main entry point for the prp-runner CLI tool, but takes arguments as a list.
    Returns an exit code.
    """
    parser = argparse.ArgumentParser(
        description="Execute a PRP file using a specified backend agent."
    )
    parser.add_argument(
        "--prp",
        type=Path,
        required=True,
        help="The path to the .md PRP file to execute.",
    )
    parser.add_argument(
        "--runner",
        type=str,
        required=True,
        help="The name of the runner to use (e.g., 'claude-cli').",
    )
    args = parser.parse_args(argv)

    # Load runner configuration
    if manifest_path is None:
        manifest_path = get_runner_manifest_path()
    runners = load_runners(manifest_path)

    # Validate runner
    if args.runner not in runners:
        print(
            f"Error: Runner '{args.runner}' not found in {manifest_path}.",
            file=sys.stderr,
        )
        return 1

    # Validate and load PRP file
    if not args.prp.exists():
        print(f"Error: PRP file not found at {args.prp}", file=sys.stderr)
        return 1
    prp_content = args.prp.read_text()
    working_dir = args.prp.parent

    # Construct the final prompt
    runner_config = runners[args.runner]
    system_prompt_template = runner_config.get("system_prompt_template")

    if system_prompt_template:
        # [+] Use str.format() for safer, non-sequential placeholder replacement.
        # This prevents bugs if the prp_content itself contains a placeholder string.
        final_prompt = system_prompt_template.format(
            prp_content=prp_content,
            working_dir=str(working_dir)
        )
    else:
        final_prompt = prp_content

    # Construct the command
    command_template = runner_config["command_template"]
    command = [
        part.replace("{prompt}", final_prompt) for part in command_template
    ]

    # Execute the command
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir,
            bufsize=1,  # Line-buffered
            universal_newlines=True
        )

        # Stream stdout in real-time
        if process.stdout:
            for line in process.stdout:
                print(line, end='', flush=True)

        # Wait for the process to complete and capture remaining output
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"\n--- Runner exited with code {process.returncode} ---", file=sys.stderr)
            if stderr:
                print(f"Error output:\n{stderr.strip()}", file=sys.stderr) # [+] Use strip() for cleaner output

        return process.returncode

    except FileNotFoundError:
        print(
            f"Error: Command '{command[0]}' not found.",
            f"Please ensure the '{args.runner}' CLI tool is installed and in your PATH.",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1


def run() -> int:
    """
    Main entry point for the prp-runner CLI tool.
    Parses command-line arguments and calls the core logic.
    """
    return run_from_args(argv=sys.argv[1:])


if __name__ == "__main__":
    sys.exit(run())
