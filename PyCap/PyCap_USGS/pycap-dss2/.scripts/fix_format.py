import subprocess

for cdir in ["../pycap/", "../docs/", "./"]:
    cmd = ("ruff", "format", f"{cdir}")
    proc = subprocess.run(cmd)
    assert proc.returncode == 0, f"Error running command: {' '.join(cmd)}"

    cmd = ("ruff", "check", "--fix", f"{cdir}")
    proc = subprocess.run(cmd)
    assert proc.returncode == 0, f"Error running command: {' '.join(cmd)}"
