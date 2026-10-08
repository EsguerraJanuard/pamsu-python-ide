import os
import re

test_dir = "backend/tests"

# 1. Fix User(name=...) -> first_name=..., last_name=...
# We will look for User( and then inside it replace name= with first_name=..., last_name=...
for root, _, files in os.walk(test_dir):
    for filename in files:
        if filename.endswith(".py"):
            filepath = os.path.join(root, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find User( instantiations
            # It's usually:
            # user = User(
            #     name=name,
            #     school_id=...
            # )
            
            new_content = re.sub(
                r'(\bUser\([^)]*?)name=(.*?),',
                r'\1first_name=(\2).split()[0] if isinstance(\2, str) else "Test",\n        last_name=" ".join((\2).split()[1:]) if isinstance(\2, str) and " " in \2 else "User",',
                content,
                flags=re.DOTALL
            )
            
            # 2. Fix assertions: response.json()["name"] -> response.json()["first_name"] + " " + response.json()["last_name"]
            # Wait, the tests might expect just "name". If I replace ["name"] with ["first_name"] it might break if the test checks the full name.
            # Usually they do `assert data["name"] == "Test Instructor"`.
            # If I replace `data["name"]` with `f'{data["first_name"]} {data["last_name"]}'` it will pass!
            # Let's do that for `["name"]`.
            
            # e.g. payload["name"] -> f'{payload["first_name"]} {payload["last_name"]}'
            # e.g. classroom_data["name"] -> classroom_data["name"] (WAIT! Classroom has a name! Only replace if it's user or payload or student!)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

print("Pass 1: User instantiations fixed.")
