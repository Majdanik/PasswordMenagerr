<template>
  <div class="app-container">
    <!-- 🔐 LOGIN/REGISTER SCREEN -->
    <div v-if="!isLoggedIn" class="auth-screen">
      <h1>Menadżer Haseł</h1>
      
      <div v-if="isRegisterMode">
        <h2>Rejestracja</h2>
        <input v-model="authForm.email" type="email" placeholder="Email" />
        <input v-model="authForm.password" type="password" placeholder="Hasło" />
        <button @click="register">Zarejestruj się</button>
        <p><small><a href="#" @click.prevent="isRegisterMode = false">Mam już konto</a></small></p>
      </div>

      <div v-else>
        <h2>Logowanie</h2>
        <input v-model="authForm.email" type="email" placeholder="Email" />
        <input v-model="authForm.password" type="password" placeholder="Hasło" />
        <button @click="login">Zaloguj się</button>
        <p><small><a href="#" @click.prevent="isRegisterMode = true">Utwórz konto</a></small></p>
      </div>

      <p v-if="authError" class="error">{{ authError }}</p>
    </div>

    <!-- 🔑 MAIN APP (after login) -->
    <div v-else>
      <div class="header">
        <h1>Menadżer Haseł</h1>
        <button @click="logout" class="logout-btn">Wyloguj</button>
      </div>

      <!-- Formularz dodawania -->
      <div class="form-section">
        <input v-model="newPassword.service" type="text" placeholder="Serwis" />
        <input v-model="newPassword.login" type="text" placeholder="Login" />
        <input v-model="newPassword.password" type="password" placeholder="Hasło" />
        <button @click="addPassword">Dodaj</button>
      </div>

      <!-- Lista haseł -->
      <ul>
        <li v-for="item in passwords" :key="item.id">
          <strong>{{ item.service }}</strong> – {{ item.login }} – 
          <span>{{ decrypted[item.id] || "***" }}</span>

          <button @click="decryptPassword(item.id, item.password)">Pokaż</button>
          <button @click="deletePassword(item.id)" class="delete-btn">Usuń</button>
        </li>
      </ul>

      <p v-if="passwords.length === 0" class="no-passwords">Brak zapisanych haseł</p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

// Backend na tym samym hoście
const API_URL = window.location.origin;

export default {
  data() {
    return {
      isLoggedIn: false,
      isRegisterMode: false,
      authForm: { email: "", password: "" },
      authError: "",
      token: localStorage.getItem("token"),
      passwords: [],
      decrypted: {},
      newPassword: { service: "", login: "", password: "" },
    };
  },
  methods: {
    async register() {
      try {
        const res = await axios.post(`${API_URL}/auth/register`, {
          email: this.authForm.email,
          password: this.authForm.password,
        });
        this.authError = "";
        this.isRegisterMode = false;
        alert("Rejestracja udana! Zaloguj się.");
      } catch (err) {
        this.authError = err.response?.data?.detail || "Błąd rejestracji";
      }
    },
    async login() {
      try {
        const res = await axios.post(`${API_URL}/auth/login`, {
          email: this.authForm.email,
          password: this.authForm.password,
        });
        this.token = res.data.access_token;
        localStorage.setItem("token", this.token);
        this.isLoggedIn = true;
        this.authError = "";
        this.authForm = { email: "", password: "" };
        this.fetchPasswords();
      } catch (err) {
        this.authError = err.response?.data?.detail || "Błędne dane logowania";
      }
    },
    logout() {
      this.isLoggedIn = false;
      this.token = "";
      localStorage.removeItem("token");
      this.passwords = [];
      this.decrypted = {};
    },
    async fetchPasswords() {
      try {
        const res = await axios.get(`${API_URL}/passwords`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        this.passwords = res.data;
      } catch (err) {
        console.error("Błąd pobierania haseł:", err);
      }
    },
    async addPassword() {
      try {
        await axios.post(`${API_URL}/passwords`, this.newPassword, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        this.newPassword = { service: "", login: "", password: "" };
        this.fetchPasswords();
      } catch (err) {
        alert("Błąd dodawania hasła");
      }
    },
    async deletePassword(id) {
      if (confirm("Na pewno usunąć hasło?")) {
        try {
          await axios.delete(`${API_URL}/passwords/${id}`, {
            headers: { Authorization: `Bearer ${this.token}` },
          });
          this.fetchPasswords();
        } catch (err) {
          alert("Błąd usuwania");
        }
      }
    },
    async decryptPassword(id, encrypted) {
      try {
        const res = await axios.post(
          `${API_URL}/passwords/decrypt`,
          { key: "", password: encrypted },
          { headers: { Authorization: `Bearer ${this.token}` } }
        );
        this.$set(this.decrypted, id, res.data.decrypted);
      } catch (err) {
        alert("Błąd odszyfrowania");
      }
    },
  },
  mounted() {
    if (this.token) {
      this.isLoggedIn = true;
      this.fetchPasswords();
    }
  },
};
</script>

<style>
body {
  background-color: #f5f5f5;
  color: #333;
  font-family: Arial, sans-serif;
  margin: 0;
}

.app-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.auth-screen {
  text-align: center;
}

.auth-screen h1 {
  color: #0066cc;
}

.auth-screen h2 {
  color: #333;
  margin: 20px 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.logout-btn {
  background: #ff4444;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.logout-btn:hover {
  background: #cc0000;
}

input, button {
  display: block;
  width: 100%;
  margin: 10px 0;
  padding: 12px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
}

input {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  color: #000;
}

input:focus {
  outline: none;
  border-color: #0066cc;
}

button {
  background: #0066cc;
  color: white;
  border: none;
  cursor: pointer;
  font-weight: bold;
}

button:hover {
  background: #0052a3;
}

.form-section {
  margin: 20px 0;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
}

.form-section input {
  margin: 8px 0;
}

.form-section button {
  margin-top: 10px;
}

ul {
  list-style: none;
  padding: 0;
}

li {
  background: #f5f5f5;
  padding: 12px;
  margin: 8px 0;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

li strong {
  color: #0066cc;
}

li button {
  display: inline-block;
  width: auto;
  padding: 6px 12px;
  margin: 0 4px;
  font-size: 12px;
}

.delete-btn {
  background: #ff6666;
}

.delete-btn:hover {
  background: #ff4444;
}

.error {
  color: #ff0000;
  margin: 10px 0;
}

.no-passwords {
  text-align: center;
  color: #999;
  padding: 20px;
}

a {
  color: #0066cc;
  text-decoration: none;
  cursor: pointer;
}

a:hover {
  text-decoration: underline;
}
</style>
