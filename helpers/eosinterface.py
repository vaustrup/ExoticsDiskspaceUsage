import pathlib
import subprocess

def eos_du(path: pathlib.Path) -> int:
    cmd = ["eos", "du", "-s", path]

    try:
        result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"EOS command {' '.join(cmd)} failed: {e.stderr.strip()}")

    output = result.stdout.strip()

    try:
        size = int(output.split()[0])
    except (IndexError, ValueError):
        raise ValueError(f"Could not parse eos du output {output}")

    return size
    
