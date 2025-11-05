<script setup>
import { ref, defineEmits } from 'vue';
import { calculateDistance } from '../utils/distanceUtils'; // <-- Ganti ke path relatif

const emit = defineEmits(['run-saved']);

// --- STATE GPS ---
const isTracking = ref(false);
const pathCoordinates = ref([]);
const totalSeconds = ref(0);
const recordCount = ref(0);
const buttonDisabled = ref(false);

// --- STATE ALARM & JARAK ---
const totalDistance = ref(0); // Jarak lari saat ini (km)
const targetAlarm = 5; // Target alarm yang dapat disesuaikan (5 km)
const alarmTriggered = ref(false); // Flag untuk mencegah alarm berbunyi berulang

// Variabel non-reaktif untuk interval
let timerInterval = null;
let watchId = null;

// Format waktu menjadi MM:SS
const formattedTime = ref('00:00');

// =======================================================
// FUNGIONALITAS TIMER
// =======================================================

const startTimer = () => {                                                        
    totalSeconds.value = 0;
    formattedTime.value = '00:00';
    timerInterval = setInterval(() => {
        totalSeconds.value++;
        const minutes = Math.floor(totalSeconds.value / 60);
        const seconds = totalSeconds.value % 60;
        formattedTime.value = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
};

const stopTimer = () => {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }                                                                         
};

// =======================================================
// FUNGIONALITAS PELACAKAN GPS (TERMASUK ALARM)
// =======================================================

/**
 * Mengambil, menyimpan lokasi, menghitung jarak, dan mengecek alarm.
 */
const saveLocation = (position) => {
    const { latitude, longitude } = position.coords;

    const newCoord = [latitude, longitude];
    
    // 1. Hitung Jarak Kumulatif
    if (pathCoordinates.value.length > 0) {
        const lastCoord = pathCoordinates.value[pathCoordinates.value.length - 1];
        
        const segmentDistance = calculateDistance(
            lastCoord[0], lastCoord[1],
            latitude, longitude
        );
        totalDistance.value += segmentDistance; // Tambahkan ke total jarak
    }

    pathCoordinates.value.push(newCoord);
    recordCount.value = pathCoordinates.value.length;
    
    // 2. Cek Alarm 5 km
    if (!alarmTriggered.value && totalDistance.value >= targetAlarm) {
        // Tampilkan notifikasi
        alert(`Selamat! Anda telah mencapai ${targetAlarm} km! Terus Semangat!`);
        
        // Set flag agar alarm tidak berbunyi lagi
        alarmTriggered.value = true; 
    }
};

const startTracking = () => {
    if (!navigator.geolocation) {
        alert('Geolocation tidak didukung oleh browser Anda.');
        return;                                                                   
    }

    // Reset state
    resetState();
    buttonDisabled.value = true;

    // Mulai timer
    startTimer();

    // Dapatkan lokasi awal segera
    navigator.geolocation.getCurrentPosition(saveLocation, handleLocationError);

    // Gunakan watchPosition untuk pembaruan berkelanjutan
    watchId = navigator.geolocation.watchPosition(                              
        saveLocation,
        handleLocationError,
        {
            enableHighAccuracy: true,
            timeout: 5000,
            maximumAge: 0 // Tidak menggunakan cache
        }
    );

    isTracking.value = true;
    buttonDisabled.value = false;
};

const handleLocationError = (error) => {
    let message = '';
    switch(error.code) {
        case error.PERMISSION_DENIED:
            message = "Akses lokasi ditolak. Silakan izinkan di pengaturan browser.";
            break;
        case error.POSITION_UNAVAILABLE:
            message = "Informasi lokasi tidak tersedia saat ini.";
            break;
        case error.TIMEOUT:                                                               
            message = "Permintaan lokasi habis waktu (timeout).";
            break;
        default:
            message = "Terjadi kesalahan yang tidak diketahui saat pelacakan.";
            break;
    }
    alert(`Error GPS: ${message}`);
    // Jika ada error fatal, hentikan pelacakan
    stopTracking(true); // Kirim flag untuk tidak mencoba menyimpan
};

const stopTracking = (isCancel = false) => {
    if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;                                                     
    }
    stopTimer();
    isTracking.value = false;
    
    if (isCancel) {
        resetState(); // Reset state jika dibatalkan karena error atau tombol Batal
    }
};

// =======================================================
// SIMPAN DATA KE BACKEND
// =======================================================

const saveRun = async () => {
    stopTracking(); // Pastikan pelacakan berhenti

    if (pathCoordinates.value.length < 2) {
        alert("Tidak ada cukup titik koordinat untuk merekam lari (minimal 2 titik diperlukan).");
        resetState();
        return;
    }
    
    // Periksa jika total jarak lebih dari 0
    if (totalDistance.value < 0.01) {
        alert("Jarak yang ditempuh terlalu kecil (< 10 meter). Tidak disimpan.");
        resetState();
        return;
    }

    if (totalSeconds.value < 60) {
        if (!confirm(`Durasi lari hanya ${totalSeconds.value} detik. Tetap simpan?`)) {
            resetState();
            return;                                                                   
        }
    }
    buttonDisabled.value = true;

    // Payload yang dikirim ke /api/runs/gps
    const payload = {
        date: new Date().toISOString().slice(0, 10),
        path_coordinates: JSON.stringify(pathCoordinates.value),
        distance_km: parseFloat(totalDistance.value.toFixed(2)), // Kirim jarak aktual
        duration_min: (totalSeconds.value / 60) // Ubah detik ke menit
    };

    try {                                                                             
        const response = await fetch('/api/runs/gps', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        });

        if (response.ok) {
            emit('run-saved'); // Beri tahu App.vue untuk refresh
            resetState();
        } else {
            const errorData = await response.json();
            alert(`Gagal menyimpan lari. Pesan Server: ${errorData.error || response.statusText}`);
            buttonDisabled.value = false;
        }
    } catch (e) {
        alert('Gagal berkomunikasi dengan server backend.');
        buttonDisabled.value = false;
    }
};

const resetState = () => {
    pathCoordinates.value = [];                                                   
    totalSeconds.value = 0;
    recordCount.value = 0;
    totalDistance.value = 0; // RESET JARAK
    alarmTriggered.value = false; // RESET ALARM
    formattedTime.value = '00:00';
    buttonDisabled.value = false;
};
</script>


<template>
    <div class="card shadow-sm p-4 text-center">
        <h3 class="card-title fw-bold text-primary mb-4">
            <i class="bi bi-compass me-2"></i> GPS Run Tracker
        </h3>

        <div class="mb-4">
            <p class="text-muted mb-1">Waktu Lari:</p>
            <span class="display-3 fw-bolder text-dark">{{ formattedTime }}</span>
        </div>

        <div class="alert alert-warning py-2 small mb-4 fw-bold">
            <i class="bi bi-ruler me-2"></i> Jarak Ditempuh: 
            <span class="text-primary fs-5">{{ totalDistance.toFixed(2) }} km</span>
            <span v-if="isTracking && totalDistance < targetAlarm" class="ms-3 text-secondary">
                 (<i class="bi bi-dash-circle"></i> {{ (targetAlarm - totalDistance).toFixed(2) }} km lagi menuju {{ targetAlarm }} km!)
            </span>
            <span v-else-if="alarmTriggered" class="ms-3 text-success">
                 (<i class="bi bi-check-circle-fill"></i> Target {{ targetAlarm }} km Tercapai!)
            </span>
        </div>

        <div class="alert alert-info py-2 small mb-4">
            <i class="bi bi-geo-alt me-2"></i> Titik koordinat direkam: 
            <strong>{{ recordCount }}</strong> total.
        </div>

        <div class="d-grid gap-2 d-md-block action-buttons">
            
            <button
                v-if="!isTracking"
                @click="startTracking"
                :disabled="buttonDisabled"
                class="btn btn-success btn-lg shadow-lg">
                <i class="bi bi-play-circle-fill me-2"></i> Mulai Lari Sekarang!
            </button>

            <button
                v-if="isTracking"
                @click="saveRun"
                :disabled="buttonDisabled"
                class="btn btn-primary btn-lg me-2">
                <i class="bi bi-stop-circle-fill me-2"></i> Selesai Lari (Simpan)
            </button>
            
            <button
                v-if="isTracking"                                                             
                @click="stopTracking(true)"
                :disabled="buttonDisabled"
                class="btn btn-secondary btn-lg">
                <i class="bi bi-x-circle-fill me-2"></i> Batal
            </button>
        </div>

        <p class="text-muted small mt-3">
            <i class="bi bi-exclamation-octagon me-1"></i> Izinkan akses lokasi di browser Anda agar pelacakan berfungsi.
        </p>
    </div>
</template>

<style scoped>
/* Apapun isinya, hapus semuanya! */
</style>
