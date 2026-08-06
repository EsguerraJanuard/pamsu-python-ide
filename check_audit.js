
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on("console", msg => console.log("PAGE LOG:", msg.text()));
  page.on("pageerror", err => console.log("PAGE ERROR:", err.message));
  await page.goto("http://localhost:5173/instructor/audit-logs", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await browser.close();
})();
