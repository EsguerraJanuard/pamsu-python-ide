import os

filepath = "frontend/src/App.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

admin_routes = """
              {/* Admin Role Tree */}
              <Route element={<RoleRoute allowedRole="admin" />}>
                <Route path="/admin/dashboard" element={<AdminDashboard />} />
              </Route>

"""

if "Admin Role Tree" not in content:
    content = content.replace(
        '              <Route element={<RoleRoute allowedRole="instructor" />}>',
        admin_routes + '              <Route element={<RoleRoute allowedRole="instructor" />}>'
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Added admin route to App.jsx")
