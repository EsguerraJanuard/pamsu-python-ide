const fs = require('fs');
const filepath = 'frontend/src/main.jsx';
let content = fs.readFileSync(filepath, 'utf8');

if (!content.includes('virtual:pwa-register')) {
    const importStr = "import { registerSW } from 'virtual:pwa-register';\n";
    content = importStr + content;
    content += "\n\nif ('serviceWorker' in navigator) {\n  registerSW({ immediate: true });\n}\n";
    fs.writeFileSync(filepath, content);
    console.log("Registered PWA in main.jsx");
}
