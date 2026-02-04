<template>
  <div class="app-container">
    <router-view />
  </div>
</template>

<script setup>
// Modern composition API setup
</script>

<style>
.app-container {
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Global container class */
.container {
  width: 100%;
  padding: 20px;
  box-sizing: border-box;
}

/* Ensure smooth transitions for theme switching */
* {
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
</style>
