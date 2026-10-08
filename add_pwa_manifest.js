const fs = require('fs');

const configPath = 'frontend/vite.config.js';
let config = fs.readFileSync(configPath, 'utf8');

const manifestCode = `
      manifest: {
        name: 'PAMSU Python IDE',
        short_name: 'PAMSU IDE',
        description: 'Advanced Agentic Coding Environment for Pampanga State University',
        theme_color: '#800000',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/pamsu_logo.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/pamsu_logo.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
`;

config = config.replace("registerType: 'autoUpdate',", "registerType: 'autoUpdate',\n" + manifestCode);
fs.writeFileSync(configPath, config);
console.log("Added manifest to vite.config.js");
