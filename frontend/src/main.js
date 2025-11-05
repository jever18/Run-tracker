// 📁 frontend/src/main.js

import { createApp } from 'vue';
import App from './App.vue';
// ... impor lainnya (router, store, dll.)

// *KRITIS: PASTIKAN BARIS IMPOR CSS INI ADA!*
import './style.css'; 
// atau mungkin: import './assets/main.css'; 
// Sesuaikan dengan lokasi file CSS yang berisi deklarasi @tailwind Anda.

createApp(App).mount('#app');
