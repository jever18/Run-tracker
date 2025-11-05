/**
 * Menghitung jarak antara dua titik koordinat (latitude dan longitude) 
 * menggunakan rumus Haversine. Hasil dalam Kilometer (km).
 * * @param {number} lat1 Latitude titik pertama
 * @param {number} lon1 Longitude titik pertama
 * @param {number} lat2 Latitude titik kedua
 * @param {number} lon2 Longitude titik kedua
 * @returns {number} Jarak dalam kilometer (km)
 */
export function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius bumi dalam kilometer

    const dLat = deg2rad(lat2 - lat1);
    const dLon = deg2rad(lon2 - lon1);

    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
        
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c; // Jarak dalam km

    return distance;
}

/**
 * Mengubah derajat menjadi radian
 */
function deg2rad(deg) {
    return deg * (Math.PI / 180);
}
