from pathlib import Path

for d in [
    "docs/dev_docs/agent_skill",
    "docs/dev_docs/architecture",
    "docs/dev_docs/tasks",
    "docs/site_docs",
    "od-prototype/briefs",
    "od-prototype/preview",
    "raw_data/schema",
]:
    Path(d).mkdir(parents=True, exist_ok=True)
    keep = Path(d) / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")

print("Repository directories are ready.")
