import { ref, watch, onMounted } from 'vue';

// Kunci LocalStorage
const THEME_KEY = 'run-tracker-theme';

// State tema (ref global)
const isDark = ref(false);

export function useTheme() {

    // Fungsi untuk menerapkan tema ke elemen HTML 
    const applyTheme = (dark) => {
        if (dark) {
            document.documentElement.classList.add('theme-dark');
            localStorage.setItem(THEME_KEY, 'dark');
        } else {
            document.documentElement.classList.remove('theme-dark');
            localStorage.setItem(THEME_KEY, 'light');
        }
    };

    // 1. Inisialisasi: Memuat tema dari LocalStorage saat komponen dimuat
    onMounted(() => {
        const savedTheme = localStorage.getItem(THEME_KEY);
        
        // Prioritaskan tema yang disimpan, jika tidak ada, gunakan preferensi sistem
        if (savedTheme) {
            isDark.value = savedTheme === 'dark';
        } else {
            // Cek preferensi sistem (misalnya dark mode OS)
            isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        applyTheme(isDark.value);
    });

    // 2. Watcher: Mengubah tema saat isDark.value diubah
    watch(isDark, (newVal) => {
        applyTheme(newVal);
    });

    // 3. Toggle: Fungsi untuk dipanggil oleh tombol UI
    const toggleTheme = () => {
        isDark.value = !isDark.value;
    };

    return {
        isDark,
        toggleTheme,
    };
}
