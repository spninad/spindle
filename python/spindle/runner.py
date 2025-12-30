"""Script runner for spindle."""

import shlex
import subprocess
import sys
from typing import List


def run_script(script: str, extra_args: List[str]) -> int:
    """Run a script command with additional arguments.
    
    Returns the exit code of the command.
    """
    # Build the full command
    if extra_args:
        # Quote args that need it
        quoted_args = " ".join(shlex.quote(arg) for arg in extra_args)
        command = f"{script} {quoted_args}"
    else:
        command = script

    # Run using bash -lc for consistency with the Swift version
    result = subprocess.run(
        ["/bin/bash", "-lc", command],
        cwd=None,  # Use current directory
    )
    return result.returncode
