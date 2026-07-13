# tests/fixtures.py
from __future__ import annotations

# A diff with one seeded, genuinely-present bug: `eval()` on
# unsanitized input. A reviewer citing this exact line is citing
# something that really is in the diff.
SEEDED_BUG_DIFF = """--- a/app.py
+++ b/app.py
@@ -8,3 +8,3 @@
 def run(user_input):
-    return safe(user_input)
+    return eval(user_input)
"""

SEEDED_BUG_PATH = "app.py"
SEEDED_BUG_LINE = 9
SEEDED_BUG_EVIDENCE = "return eval(user_input)"

# A clean diff with no seeded bug at all.
CLEAN_DIFF = """--- a/app.py
+++ b/app.py
@@ -20,3 +20,3 @@
 def greet(name):
-    return "hi " + name
+    return f"hi {name}"
"""
