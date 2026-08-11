import json, sys
d = json.load(sys.stdin)
models = d.get("data", [])
print(f"Total models: {len(models)}")
for m in models[:15]:
    print(f"  {m['id']}")
