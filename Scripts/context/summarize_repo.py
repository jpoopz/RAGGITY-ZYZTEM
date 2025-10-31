import os, json, re, pathlib

ROOTS = ["app", "ui", "core", "modules"]
MAX_PER_FILE = 280


def summarize_text(text: str) -> str:
    head = []
    m = re.search(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', text)
    if m and len(m.group(0)) < 400:
        head.append(m.group(0).strip().replace("\n", " ")[:200])
    for line in text.splitlines():
        if line.startswith(("def ", "class ")):
            head.append(line.strip())
        if len(" ".join(head)) > MAX_PER_FILE:
            break
    s = " | ".join(head)[:MAX_PER_FILE]
    return s or "No summary. Likely a view/component/style/asset."


def walk():
    idx = {}
    for root in ROOTS:
        p = pathlib.Path(root)
        if not p.exists():
            continue
        for f in p.rglob("*.*"):
            if any(x in f.parts for x in ["__pycache__", "node_modules", ".chromadb", "Lib", "site-packages"]):
                continue
            if f.suffix.lower() in [".py", ".ts", ".tsx", ".js"]:
                try:
                    txt = f.read_text(encoding="utf-8", errors="ignore")
                    idx[str(f)] = summarize_text(txt)
                except Exception:
                    pass
    return idx


if __name__ == "__main__":
    idx = walk()
    os.makedirs("docs", exist_ok=True)
    with open("docs/CONTEXT_INDEX.json", "w", encoding="utf-8") as out:
        json.dump(idx, out, indent=2)
    print(f"Wrote docs/CONTEXT_INDEX.json with {len(idx)} entries")


