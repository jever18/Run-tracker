<script setup>
import { ref, onMounted } from 'vue';
import MapComponent from './components/MapComponent.vue';
import RunChart from './components/RunChart.vue';
import AuthForm from './components/AuthForm.vue';
import GpsTracker from './components/GpsTracker.vue';
import ThemeToggler from './components/ThemeToggler.vue';

// --- STATE UTAMA APLIKASI ---
const runs = ref([]);
const loading = ref(true);
const error = ref(null);
const successMessage = ref('');

// --- STATE OTENTIKASI ---
const isAuthenticated = ref(false);
const currentUser = ref(null);

// =======================================================
// FUNGSI OTENTIKASI DAN STATUS
// =======================================================

/**
 * Memeriksa status login pengguna dari backend.
 */
const checkAuthStatus = async () => {
    loading.value = true;
    error.value = null;

    try {
        const response = await fetch('/api/auth/status', {
            credentials: 'include'
        });
        const data = await response.json();

        isAuthenticated.value = data.is_authenticated;
        if (data.is_authenticated) {
            currentUser.value = data.user;
            await fetchRuns(); // Ambil data lari hanya jika sudah login
        } else {
            loading.value = false; // Hentikan loading jika TIDAK login
        }
    } catch (err) {
        error.value = 'Gagal memeriksa status server (pastikan backend Flask berjalan!).';
        isAuthenticated.value = false;
        loading.value = false;
    }
};

/**
 * Handler ketika login berhasil dari AuthForm.
 */
const handleAuthSuccess = (user) => {
    isAuthenticated.value = true;
    currentUser.value = user;
    successMessage.value = `Selamat datang, ${user.username}!`;
    fetchRuns();
};

/**
 * Logout dari sistem.
 */
const logout = async () => {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        isAuthenticated.value = false;
        currentUser.value = null;
        runs.value = [];
        successMessage.value = 'Anda berhasil logout.';
    } catch (e) {
        error.value = 'Gagal logout. Coba lagi.';
    }
};
                                                                              
// =======================================================
// FUNGSI API (CRUD)
// =======================================================

/**
 * Mengambil data lari HANYA milik user yang sedang login.
 */
const fetchRuns = async () => {
  loading.value = true;
  error.value = null;

  if (!isAuthenticated.value) {
      loading.value = false;
      return;
  }

  try {
    const response = await fetch('/api/runs', {
        credentials: 'include'
    });

    if (!response.ok) {
        if(response.status === 401) {
            isAuthenticated.value = false;
            currentUser.value = null;
            runs.value = [];
            successMessage.value = 'Sesi Anda telah berakhir. Silakan login kembali.';
            return;
        }
        throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const data = await response.json();
    runs.value = data;
  } catch (err) {
    error.value = 'Gagal mengambil data lari.';
  } finally {
    loading.value = false;
  }                                                                           
};                                                                            

// =======================================================
// HANDLER EVENT DARI KOMPONEN ANAK
// =======================================================

/**
 * Dipanggil dari GpsTracker.vue setelah lari berhasil disimpan ke /api/runs/gps
 */
const handleRunSaved = () => {
    successMessage.value = 'Lari berhasil direkam dan disimpan!';
    fetchRuns(); // Refresh daftar lari
};

/**
 * Dipanggil dari MapComponent.vue setelah lari berhasil dihapus
 */
const handleRunDeleted = (deletedRunId) => {
  runs.value = runs.value.filter(run => run.id !== deletedRunId);
  successMessage.value = `Larian ID ${deletedRunId} berhasil dihapus.`;
};

/**
 * Dipanggil dari MapComponent.vue setelah lari berhasil diupdate
 */
const handleRunUpdated = (updatedRunData) => {
  const index = runs.value.findIndex(run => run.id === updatedRunData.id);
  if (index !== -1) {
    runs.value[index] = { ...runs.value[index], ...updatedRunData };
    successMessage.value = `Larian ID ${updatedRunData.id} berhasil diupdate.`;
  }
};

// Panggil fungsi status/fetch saat komponen dimuat
onMounted(checkAuthStatus);
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-800">

    <div class="container my-5 p-4 p-md-5 shadow-lg rounded-3 min-vh-100 bg-white">

        <header class="text-center mb-4 border-bottom pb-3">
            <h1 class="display-6 fw-bold text-primary">
                <i class="bi bi-activity"></i> Run Tracker Profesional
            </h1>
        </header>

        <div class="d-flex justify-content-between align-items-center p-3 mb-4 bg-light rounded-3 shadow">
            <span v-if="currentUser" class="text-secondary small">Selamat datang,
                <strong class="text-primary">{{ currentUser.username }}</strong>
            </span>
            <span v-else class="text-secondary small">Silakan Login untuk mulai melacak lari.</span>

            <div class="d-flex align-items-center">
                <ThemeToggler class="me-3" />
                <button v-if="isAuthenticated" @click="logout"
                    class="btn btn-danger btn-sm">
                    Logout
                </button>
            </div>
        </div>
        
        <div v-if="!isAuthenticated" class="mt-4">
            <AuthForm @auth-success="handleAuthSuccess" />
        </div>

        <div v-else>
            <div v-if="successMessage" class="alert alert-success" role="alert">{{ successMessage }}</div>
            <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

            <div class="row g-4"> 
                
                <div class="col-12 col-md-6 col-lg-5 d-grid gap-4">
                    
                    <div class="p-4 bg-info-subtle rounded-3 shadow-sm">
                        <GpsTracker @run-saved="handleRunSaved" />
                    </div>

                    <div>
                        <h2 class="h4 fw-bold text-secondary mb-3 text-start">
                            <i class="bi bi-clipboard-data-fill"></i> Analisis Tren Lari Anda
                        </h2>
                        <div class="p-4 bg-light rounded-3 shadow-sm border">
                            <RunChart :runs="runs" v-if="!loading && runs.length > 0" />
                            <p v-else class="text-muted text-center">Tidak cukup data untuk menampilkan grafik.</p>
                        </div>
                    </div>
                </div>

                <div class="col-12 col-md-6 col-lg-7">
                    <h2 class="h4 fw-bold text-secondary mb-3 text-start">
                        <i class="bi bi-card-checklist"></i> Daftar Lari (Total {{ runs.length }} Catatan)
                    </h2>
                    
                    <div v-if="loading" class="alert alert-primary text-center">
                        Memuat data lari Anda...
                    </div>
                    
                    <div v-else>
                        <div v-if="runs.length === 0" class="text-center p-4 bg-light rounded-3 shadow-sm">
                            <p class="text-muted">Anda belum memiliki catatan lari. Mulailah dengan
                                <strong class="text-primary">Mulai Lari Sekarang!</strong></p>
                        </div>

                        <div v-else class="row g-4 mt-2">
                            <div v-for="run in runs" :key="run.id" class="col-12 col-xl-6">
                                <MapComponent
                                    :run="run"
                                    @run-deleted="handleRunDeleted"
                                    @run-updated="handleRunUpdated"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>
