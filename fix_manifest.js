const fs = require('fs');

const configPath = 'frontend/vite.config.js';
let config = fs.readFileSync(configPath, 'utf8');

config = config.replace(/\/pamsu_logo\.png/g, '/school_logo.png');
fs.writeFileSync(configPath, config);
console.log("Fixed icon path");
