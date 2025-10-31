import subprocess, sys, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
MEMO = REPO / "docs" / "AGENT_MEMORY.md"


def run(cmd):
    return subprocess.check_output(cmd, shell=True, encoding="utf-8", errors="ignore").strip()


def main():
    try:
        files = run("git diff --cached --name-only").splitlines()
        if not files:
            return 0
        num_files = len(files)
        numstat = run("git diff --cached --numstat")
        lines = 0
        for row in numstat.splitlines():
            parts = row.split()
            if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                lines += int(parts[0]) + int(parts[1])

        needs_memory = (num_files > 5) or (lines > 300)

        if needs_memory:
            staged = set(files)
            memo_rel = str(MEMO.relative_to(REPO))
            if memo_rel not in staged:
                sys.stderr.write(
                    "Large change detected (>5 files or >300 total line edits).\n"
                    "Please add a brief entry to docs/AGENT_MEMORY.md and stage it.\n"
                )
                return 1
        return 0
    except subprocess.CalledProcessError:
        return 0


if __name__ == "__main__":
    sys.exit(main())


