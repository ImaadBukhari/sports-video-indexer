<template>
  <div class="container">
    <h1>⚽ Soccer Video Query</h1>
    <form @submit.prevent="handleSubmit">
      <input type="file" @change="handleFileChange" :disabled="useDemo" />
      <label>
        <input type="checkbox" v-model="useDemo" />
        Use demo video
      </label>
      <input v-model="query" placeholder="e.g. show me the first goal" required />
      <button :disabled="loading">{{ loading ? 'Processing...' : 'Submit' }}</button>
    </form>

    <video v-if="videoUrl" controls width="600" :src="videoUrl"></video>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const query = ref('');
const file = ref(null);
const videoUrl = ref(null);
const loading = ref(false);
const useDemo = ref(false);

const handleFileChange = (e) => {
  file.value = e.target.files[0];
};

const handleSubmit = async () => {
  loading.value = true;
  const formData = new FormData();
  formData.append('query', query.value);
  formData.append('use_demo', useDemo.value);
  if (!useDemo.value && file.value) {
    formData.append('file', file.value);
  }

  try {
    const res = await axios.post('http://127.0.0.1:8000/process', formData, {
      responseType: 'blob'
    });
    const blob = new Blob([res.data], { type: 'video/mp4' });
    videoUrl.value = URL.createObjectURL(blob);
  } catch (err) {
    alert('Error processing video');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: auto;
  padding: 2rem;
  font-family: sans-serif;
}
input[type="text"], input[type="file"] {
  display: block;
  margin: 1rem 0;
}
button {
  padding: 0.5rem 1rem;
}
</style>
