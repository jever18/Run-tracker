<script setup>
import { ref, defineEmits } from 'vue';

const emit = defineEmits(['auth-success']);

const username = ref('');
const password = ref('');
const isRegister = ref(false); // Menggantikan isRegistering

const message = ref(''); // Menggantikan successMessage dan error
const isError = ref(false);
const isLoading = ref(false); // Tambahkan state loading

const submitAuth = async () => {
    const endpoint = isRegister.value ? '/api/auth/register' : '/api/auth/login';

    message.value = 'Loading...';
    isError.value = false;
    isLoading.value = true;

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username.value, password: password.value }),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            
            if (!isRegister.value) {
                // Login berhasil
                emit('auth-success', data.user);
                message.value = 'Login berhasil!';
                isError.value = false;

            } else {
                // Registrasi berhasil
                message.value = 'Registrasi berhasil! Silakan Login.';
                isError.value = false;
                isRegister.value = false; // Alihkan ke form Login
                username.value = '';
                password.value = '';
            }

        } else {
            // Gagal Login atau Register
            message.value = data.message || `Error saat otentikasi.`;
            isError.value = true;
        }
    } catch (e) {
        message.value = 'Kesalahan jaringan atau server tidak terjangkau.';
        isError.value = true;
    } finally {
        isLoading.value = false;
    }
};

// Fungsi toggle mode sudah ada di template (@click.prevent="isRegister = !isRegister")
</script>

<template>
    <div class="card shadow-lg mx-auto" style="max-width: 400px;">
        
        <div class="card-header bg-dark text-white text-center">
            <h5 class="mb-0">
                <i class="bi bi-person-circle me-2"></i> 
                {{ isRegister ? 'Registrasi Pengguna Baru' : 'Login ke Run Tracker' }}
            </h5>
        </div>

        <div class="card-body">
            
            <div v-if="message && message !== 'Loading...'" 
                 :class="['alert p-2 small', isError ? 'alert-danger' : 'alert-success']" 
                 role="alert">
                <i class="bi me-1" :class="isError ? 'bi-exclamation-triangle-fill' : 'bi-check-circle-fill'"></i> 
                {{ message }}
            </div>
            
            <div v-if="message === 'Loading...'" class="alert alert-info p-2 small" role="alert">
                 <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span> Loading...
            </div>

            <form @submit.prevent="submitAuth">
                
                <div class="mb-3">
                    <label for="auth-username" class="form-label d-flex align-items-center">
                        <i class="bi bi-person-fill me-2 text-secondary"></i> Username
                    </label>
                    <input 
                        type="text" 
                        id="auth-username" 
                        class="form-control" 
                        v-model="username" 
                        required 
                        :disabled="isLoading"
                    >
                </div>
                
                <div class="mb-4">
                    <label for="auth-password" class="form-label d-flex align-items-center">
                        <i class="bi bi-lock-fill me-2 text-secondary"></i> Password
                    </label>
                    <input 
                        type="password" 
                        id="auth-password" 
                        class="form-control" 
                        v-model="password" 
                        required 
                        :disabled="isLoading"
                    >
                </div>

                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading">
                        <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        <span v-else>
                            <i class="bi me-2" :class="isRegister ? 'bi-person-plus-fill' : 'bi-box-arrow-in-right'"></i>
                            {{ isRegister ? 'Registrasi' : 'Login' }}
                        </span>
                    </button>
                </div>
            </form>
        </div>

        <div class="card-footer text-center small text-muted">
            <p class="toggle-mode mb-0">
                {{ isRegister ? 'Sudah punya akun?' : 'Belum punya akun?' }}                  
                <a href="#" @click.prevent="isRegister = !isRegister" class="text-decoration-none">
                    {{ isRegister ? 'Login di sini' : 'Register di sini' }}
                </a>
            </p>
        </div>
    </div>
</template>

