
const fs = require("fs");
const file = "frontend/src/pages/AuditLogsPage.jsx";
let content = fs.readFileSync(file, "utf8");

content = content.replace(/log\.action\.toLowerCase/g, "(log.action || log.action_type || \"\").toLowerCase");
content = content.replace(/log\.resource\.toLowerCase/g, "(log.resource || log.resource_type || log.resource_id || \"\").toLowerCase");
content = content.replace(/log\.ip_address\.toLowerCase/g, "(log.ip_address || log.audit_data?.ip_address || \"127.0.0.1\").toLowerCase");

content = content.replace(/{log\.action}/g, "{log.action || log.action_type}");
content = content.replace(/{log\.resource \|\| \"N\/A\"}/g, "{log.resource || log.resource_type || log.resource_id || \"N/A\"}");
content = content.replace(/{log\.ip_address \|\| \"127\.0\.0\.1\"}/g, "{log.ip_address || log.audit_data?.ip_address || \"127.0.0.1\"}");
content = content.replace(/{new Date\(log\.timestamp \|\| Date\.now\(\)\)\.toLocaleString\(\)}/g, "{new Date(log.timestamp || log.occurred_at || log.created_at || Date.now()).toLocaleString()}");
content = content.replace(/{log\.status \|\| \"SUCCESS\"}/g, "{log.status || log.outcome || \"SUCCESS\"}");
content = content.replace(/log\.status === \"SUCCESS\"/g, "(log.status === \"SUCCESS\" || log.outcome === \"succeeded\")");

fs.writeFileSync(file, content);
console.log("Updated AuditLogsPage.jsx!");
