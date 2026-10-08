import os

filepath = "frontend/src/App.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix RootRoute
root_route_orig = """const RootRoute = () => {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={role === 'instructor' ? '/instructor/dashboard' : '/student/dashboard'} replace />;
};"""

root_route_fixed = """const RootRoute = () => {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (role === 'admin') return <Navigate to="/admin/dashboard" replace />;
  return <Navigate to={role === 'instructor' ? '/instructor/dashboard' : '/student/dashboard'} replace />;
};"""
content = content.replace(root_route_orig, root_route_fixed)

# Fix GuestRoute
guest_route_orig = """const GuestRoute = () => {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Outlet />;
  return <Navigate to={role === 'instructor' ? '/instructor/dashboard' : '/student/dashboard'} replace />;
};"""

guest_route_fixed = """const GuestRoute = () => {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Outlet />;
  if (role === 'admin') return <Navigate to="/admin/dashboard" replace />;
  return <Navigate to={role === 'instructor' ? '/instructor/dashboard' : '/student/dashboard'} replace />;
};"""
content = content.replace(guest_route_orig, guest_route_fixed)

# Add Admin Route
admin_route_insertion = """            {/* Administrator Layout */}
            <Route element={<RoleRoute allowedRole="admin" />}>
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
            </Route>

            {/* Student Layout */}"""
content = content.replace("{/* Student Layout */}", admin_route_insertion)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed App.jsx for Admin routing")
