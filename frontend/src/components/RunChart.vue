<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    LineElement,
    PointElement
} from 'chart.js';
import { Chart } from 'vue-chartjs';

// Daftarkan komponen Chart.js yang dibutuhkan
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    LineElement,
    PointElement
);

const props = defineProps({
  runs: {
    type: Array,
    required: true
  }
});
const chartType = 'bar'; // Kita menggunakan Bar Chart

// =======================================================                    
// FUNGSI KONVERSI PACE
// =======================================================

const paceToMinutes = (paceString) => {
    // Handling data kotor/N/A
    if (!paceString || paceString === 'N/A' || typeof paceString !== 'string') return null;

    try {
        // Asumsi paceString = "M:SS / km" (atau M:SSs / km)
        // Kita hanya mengambil bagian M:SS
        const [timePart] = paceString.split(' / ');
        // Membersihkan 's' di akhir jika ada (misal: "4:30s")
        const cleanTimePart = timePart.replace('s', ''); 
        
        const parts = cleanTimePart.split(':');
        
        // Cek jika format adalah M:S atau M:SS (jika ada M:SS:ms, kita ambil M:S)
        if (parts.length >= 2) {
            const minutes = Number(parts[0]);
            const seconds = Number(parts[1]);
            
            // Validasi sederhana
            if (isNaN(minutes) || isNaN(seconds)) return null;

            const totalMinutes = minutes + (seconds / 60);
            return parseFloat(totalMinutes.toFixed(2));
        }
        return null;
    } catch (e) {
        console.error("Error converting pace:", paceString, e);
        return null;
    }
};

const minutesToPace = (totalMinutes) => {
    if (totalMinutes === null || isNaN(totalMinutes)) return "N/A";

    // Pastikan totalMinutes adalah angka positif
    const absMinutes = Math.abs(totalMinutes); 

    const minutes = Math.floor(absMinutes);                                     
    const seconds = Math.round((absMinutes - minutes) * 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

// =======================================================
// PROPERTI TERHITUNG UNTUK DATA CHART
// =======================================================

const chartData = computed(() => {
    // 1. Sortir berdasarkan tanggal (dari lama ke baru)
    const sortedRuns = [...props.runs].sort((a, b) => new Date(a.date) - new Date(b.date));

    // 2. Ekstrak data
    const dates = sortedRuns.map(run => run.date);
    const distances = sortedRuns.map(run => run.distance_km);                     
    // Asumsi properti 'pace' sudah ada di objek run (dari backend)
    const paces = sortedRuns.map(run => paceToMinutes(run.pace));

    // 3. Gabungkan dalam format Chart.js
    return {
        labels: dates,
        datasets: [
            {
                type: 'bar', // Dataset Jarak: Bar Chart
                label: 'Jarak (km)',
                backgroundColor: 'rgba(25, 135, 84, 0.8)', // Hijau Tua Bootstrap (Success)
                data: distances,
                yAxisID: 'yDistance',
                borderRadius: 5, // Sudut sedikit melengkung
            },
            {
                type: 'line', // Dataset Pace: Line Chart
                label: 'Pace Rata-rata (menit/km)',
                borderColor: 'rgb(13, 110, 253)', // Biru Tua Bootstrap (Primary)
                backgroundColor: 'rgba(13, 110, 253, 0.3)',
                data: paces,
                yAxisID: 'yPace',
                fill: false,
                tension: 0.3,
                pointRadius: 6, // Tampilkan titik data
                pointBackgroundColor: 'rgb(13, 110, 253)',
            }
        ]
};
});

// =======================================================
// KONFIGURASI CHART (Options)
// =======================================================

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        title: {
            display: false, // Judul sudah ada di App.vue
        },
        tooltip: {
            callbacks: {
                label: function(context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }
                    if (context.dataset.yAxisID === 'yPace') {
                        // Untuk dataset Pace: tampilkan M:SS
                        label += minutesToPace(context.parsed.y) + ' / km';
                    } else {
                        // Untuk dataset Jarak: tampilkan km
                        label += context.parsed.y + ' km';
                    }
                    return label;
                }
            }
        },
        legend: {
            position: 'bottom', // Pindahkan legend ke bawah
            labels: {
                // Gunakan font Bootstrap
                font: { family: 'Helvetica Neue, Arial, sans-serif' } 
            }
        }
    },
    scales: {
        x: {
            title: { display: true, text: 'Tanggal Lari', font: { weight: 'bold' } },
            grid: { display: false }
        },
        yDistance: {
            type: 'linear', display: true, position: 'left',
            title: { display: true, text: 'Jarak (km)', color: 'rgb(25, 135, 84)', font: { weight: 'bold' } },
            min: 0,
            beginAtZero: true
        },
        yPace: {
            type: 'linear', display: true, position: 'right',                             
            title: { display: true, text: 'Pace (menit/km)', color: 'rgb(13, 110, 253)', font: { weight: 'bold' } },
            reverse: true, // Sumbu dibalik: angka kecil (cepat) di atas
            ticks: {
                callback: function(value) {
                    return minutesToPace(value) + ' / km';
                }
            },
            grid: { drawOnChartArea: false }, // Jangan gambar garis grid di area Pace
            // Opsi untuk menetapkan min/max agar grafik lebih stabil
            // min: 4, 
            // max: 12 
        }
    }
}));
</script>

<template>
  <div class="chart-wrapper">
    <div style="height: 400px;">
        <Chart
            :type="chartType"
            :data="chartData"
            :options="chartOptions"                                                   
        />
    </div>
    
    <div class="pace-info mt-4 p-3 bg-light border rounded text-start">
        <p class="mb-0 text-muted small">
            <i class="bi bi-info-circle-fill me-1 text-info"></i> 
        </p>
    </div>
  </div>
</template>
