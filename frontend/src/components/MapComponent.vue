<script setup>
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const props = defineProps({
  run: Object, // Menerima objek lari
});

const emit = defineEmits(['run-deleted', 'run-updated']);

const mapContainer = ref(null);
let map = null;
let polyline = null;
let startMarker = null;
let endMarker = null;

// State untuk mode edit
const isEditing = ref(false);
const editedDistance = ref(props.run.distance_km);
const editedDuration = ref(props.run.duration_min);
const editedDate = ref(props.run.date);

// =======================================================
// FUNGSI UTILITY & MAP
// =======================================================

/**
 * Menghitung kecepatan rata-rata (pace) dalam menit per kilometer.
 */
const calculatePace = (distanceKm, durationMin) => {
  if (distanceKm > 0) {
    const paceMinPerKm = durationMin / distanceKm;
    const minutes = Math.floor(paceMinPerKm);
    const seconds = Math.round((paceMinPerKm - minutes) * 60);
    return `${minutes}m ${seconds.toString().padStart(2, '0')}s /km`;
  }
  return 'N/A';
};

/**
 * Menggambar peta dan rute lari.
 */
const drawMap = () => {
    // Pastikan tidak ada peta yang tersisa
    if (map) {
        map.remove();
        map = null;
    }

    if (!props.run.path_coordinates) {
        // Jangan gambar peta jika tidak ada koordinat
        return;
    }

    // Ubah string JSON koordinat menjadi array objek/array Leaflet
    let pathCoords;
    try {
        // Koordinat disimpan sebagai string JSON, parse ke array
        pathCoords = JSON.parse(props.run.path_coordinates);
    } catch (e) {
        console.error("Gagal parse path_coordinates:", e);
        return;
    }

    if (!pathCoords || pathCoords.length === 0) {
        return;
    }

    // Inisialisasi peta
    const mapId = `map-${props.run.id}`;
    map = L.map(mapId).setView(pathCoords[0], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Gambarkan Polyline (Rute)
    polyline = L.polyline(pathCoords, {
        color: 'blue',
        weight: 4,
        opacity: 0.7
    }).addTo(map);

    // Marker (Start & End)
    if (pathCoords.length > 0) {
        // Custom icon untuk pelari
        const runnerIcon = L.divIcon({
            className: 'custom-icon',
            html: '<i class="bi bi-person-walking text-primary fs-4"></i>', // Ikon dari Bootstrap Icons
            iconSize: [24, 24]
        });

        // Marker Awal
        startMarker = L.marker(pathCoords[0], { 
            icon: runnerIcon,
            title: 'Mulai Lari' 
        }).addTo(map);

        // Marker Akhir
        endMarker = L.marker(pathCoords[pathCoords.length - 1], {
            icon: runnerIcon,
            title: 'Selesai Lari'
        }).addTo(map);
    }

    // Zoom peta agar rute terlihat penuh
    map.fitBounds(polyline.getBounds());

    // Fix: Perbaiki rendering peta yang terpotong
    // Harus dipanggil setelah div peta terlihat (misalnya setelah tab dibuka)
    // Untuk MapComponent yang tidak berada di tab, panggil segera setelah inisialisasi
    setTimeout(() => {
        if (map) {
             map.invalidateSize();
        }
    }, 100);
};

// =======================================================
// FUNGSI API (HAPUS & UPDATE)
// =======================================================

/**
 * Menghapus catatan lari.
 */
const deleteRun = async () => {
  if (confirm(`Apakah Anda yakin ingin menghapus larian pada ${props.run.date}?`)) {
    try {
      const response = await fetch(`/api/runs/${props.run.id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        emit('run-deleted', props.run.id); // Beri tahu parent component
      } else {
        alert('Gagal menghapus lari.');
      }
    } catch (error) {
      alert('Error saat menghubungi server: ' + error.message);
    }
  }
};

/**
 * Mengirim perubahan data lari ke backend.
 */
const saveRun = async () => {
    // Validasi sederhana
    if (!editedDistance.value || !editedDuration.value || !editedDate.value) {
        alert('Semua bidang harus diisi.');
        return;
    }

    // Format data yang akan dikirim
    const updatedData = {
        date: editedDate.value,
        distance_km: parseFloat(editedDistance.value),
        duration_min: parseFloat(editedDuration.value),
    };

    try {
        const response = await fetch(`/api/runs/${props.run.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(updatedData),
        });

        if (response.ok) {
            // Gabungkan data lari asli dengan data yang diperbarui dan kirim ke parent
            const newRunData = { ...props.run, ...updatedData };
            emit('run-updated', newRunData);
            isEditing.value = false; // Keluar dari mode edit
        } else {
            const errorData = await response.json();
            alert('Gagal mengupdate lari: ' + (errorData.message || response.statusText));
        }
    } catch (error) {
        alert('Error saat menghubungi server: ' + error.message);
    }
};

/**
 * Memulai mode edit.
 */
const startEditing = () => {
    // Isi field edit dengan data saat ini
    editedDistance.value = props.run.distance_km;
    editedDuration.value = props.run.duration_min;
    editedDate.value = props.run.date;
    isEditing.value = true;
};

/**
 * Batalkan mode edit.
 */
const cancelEditing = () => {
    isEditing.value = false;
};

// =======================================================
// LIFECYCLE HOOKS & WATCHERS
// =======================================================

// Pastikan peta digambar ulang saat data props berubah atau komponen dimount
onMounted(() => {
    drawMap();
});

// Watcher untuk menggambar ulang peta jika data run berubah
watch(() => props.run, () => {
    drawMap();
}, { deep: true });

// Wajib: Perlu ada style scoped minimal untuk Map div
</script>

<template>
    <div class="card shadow-sm h-100">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <span v-if="!isEditing" class="h5 mb-0">
                <i class="bi bi-calendar-check me-2"></i> Lari pada {{ run.date }}
            </span>
            <span v-else class="h5 mb-0">
                <i class="bi bi-pencil-square me-2"></i> Edit Lari (ID: {{ run.id }})
            </span>

            <div class="btn-group" role="group">
                <button v-if="!isEditing" @click="startEditing" class="btn btn-warning btn-sm" title="Edit">
                    <i class="bi bi-pencil"></i>
                </button>
                <button v-if="!isEditing" @click="deleteRun" class="btn btn-danger btn-sm" title="Hapus">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>

        <div class="card-body">
            
            <div :id="`map-${run.id}`" ref="mapContainer" class="map-container mb-3 border rounded"></div>
            
            <div v-if="!isEditing" class="row text-start">
                <div class="col-12 col-sm-6 mb-2">
                    <p class="mb-1"><i class="bi bi-geo-alt-fill text-success me-2"></i> 
                        <span class="fw-semibold">Jarak:</span> {{ run.distance_km }} km</p>
                </div>
                <div class="col-12 col-sm-6 mb-2">
                    <p class="mb-1"><i class="bi bi-clock-fill text-info me-2"></i> 
                        <span class="fw-semibold">Durasi:</span> {{ run.duration_min }} menit</p>
                </div>
                <div class="col-12 col-sm-6 mb-2">
                    <p class="mb-1"><i class="bi bi-speedometer2 text-primary me-2"></i> 
                        <span class="fw-semibold">Pace Rata-rata:</span> {{ calculatePace(run.distance_km, run.duration_min) }}</p>
                </div>
                <div class="col-12 col-sm-6 mb-2">
                    <p class="mb-1"><i class="bi bi-calendar-event text-secondary me-2"></i> 
                        <span class="fw-semibold">Tanggal:</span> {{ run.date }}</p>
                </div>
            </div>

            <div v-else class="row g-3 text-start">
                <div class="col-md-6">
                    <label :for="'distance-' + run.id" class="form-label">Jarak (km)</label>
                    <input type="number" step="0.1" :id="'distance-' + run.id" class="form-control" v-model="editedDistance">
                </div>
                <div class="col-md-6">
                    <label :for="'duration-' + run.id" class="form-label">Durasi (menit)</label>
                    <input type="number" :id="'duration-' + run.id" class="form-control" v-model="editedDuration">
                </div>
                <div class="col-md-12">
                    <label :for="'date-' + run.id" class="form-label">Tanggal</label>
                    <input type="date" :id="'date-' + run.id" class="form-control" v-model="editedDate">
                </div>

                <div class="col-12 d-flex justify-content-end mt-3">
                    <button @click="cancelEditing" class="btn btn-secondary me-2">
                        <i class="bi bi-x-circle me-1"></i> Batal
                    </button>
                    <button @click="saveRun" class="btn btn-success">
                        <i class="bi bi-check-circle me-1"></i> Simpan
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Ini adalah CSS minimal yang dibutuhkan Leaflet */
.map-container {
    width: 100%;
    height: 200px; /* Tinggi peta harus ditentukan */
}
</style>
