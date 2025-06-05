<template>
  <div class="container">
    <!-- Logo that links to home page on all screens -->
    <div class="header-logo" @click="resetToHome">
      <img src="@/assets/logo.png" alt="Logo" />
    </div>
    
    <!-- Search page -->
    <div v-if="currentView === 'search'" class="content-wrapper search-view">
      <h1 class="main-title">Search for any moment in the game</h1>
      
      <form @submit.prevent="handleSubmit" class="search-form">
        <div class="search-container">
          <div class="logo-container">
            <img src="@/assets/logo.png" alt="Logo" class="logo" />
          </div>
          
          <label>
            <input type="checkbox" v-model="useDemo" class="hidden-checkbox" />
            <span class="sr-only">Use demo video</span>
          </label>
          
          <input 
            type="file" 
            @change="handleFileChange" 
            :disabled="useDemo" 
            class="file-input"
            id="file-input"
          />
          
          <input 
            v-model="query" 
            placeholder="e.g. show me an example of a goal" 
            required 
            class="search-input"
          />
          
          <button 
            type="submit" 
            :disabled="loading" 
            class="search-button"
          >
            {{ loading ? 'Processing...' : 'Search' }}
          </button>
        </div>
      </form>
    </div>
    
    <!-- Results page -->
    <div v-else-if="currentView === 'results'" class="content-wrapper results-view">
      <div class="search-info" v-if="searchQuery">
        <h2 class="search-query">Results for: "{{ searchQuery }}"</h2>
        <p class="results-count">{{ results.thumbnails.length }} matches found</p>
      </div>
      
      <div class="thumbnails-grid">
        <div 
          v-for="(thumbnail, index) in results.thumbnails" 
          :key="`thumbnail-${index}`"
          class="thumbnail-card"
          @mouseenter="startPreview(index)"
          @mouseleave="stopPreview()"
          @click="playFullVideo(index)"
        >
          <!-- Show preview on hover, otherwise show thumbnail -->
          <video 
            v-if="hoveredIndex === index" 
            :src="getAssetUrl(results.previews[index], 'previews')" 
            autoplay 
            loop 
            muted 
            class="preview-video"
          ></video>
          <img 
            v-else 
            :src="getAssetUrl(thumbnail, 'thumbnails')" 
            :alt="`Result ${index + 1}`" 
            class="thumbnail-img" 
          />
          
          <!-- Video info overlay -->
          <div class="video-info" v-if="results.search_results && results.search_results[index]">
            <span class="video-name">{{ results.search_results[index].video_name }}</span>
            <span class="similarity-score">{{ Math.round(results.search_results[index].similarity * 100) }}% match</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Video player page -->
    <div v-else-if="currentView === 'player'" class="content-wrapper player-view">
      <div class="video-container">
        <video 
          :src="getAssetUrl(selectedVideo, 'videos')" 
          controls 
          autoplay
          class="video-player"
          @error="handleVideoError" 
        ></video>
        
        <!-- Video metadata -->
        <div class="video-metadata" v-if="selectedVideoInfo">
          <h3>{{ selectedVideoInfo.video_name }}</h3>
          <p>Frame: {{ selectedVideoInfo.frame_number }} | Match: {{ Math.round(selectedVideoInfo.similarity * 100) }}%</p>
        </div>
      </div>
      
      <button @click="backToResults" class="back-button">
        Back to Results
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// Base URL for backend
const BACKEND_URL = 'http://127.0.0.1:8000';

// Helper function to get asset URLs from backend
const getAssetUrl = (filename, assetType) => {
  if (!filename) return '';
  
  // Return URL pointing to backend static files
  return `${BACKEND_URL}/static/${assetType}/${filename}`;
};

// State variables
const query = ref('');
const searchQuery = ref(''); // Store the search query for display
const file = ref(null);
const loading = ref(false);
const useDemo = ref(true); // Default to demo for testing
const currentView = ref('search');
const results = ref({
  thumbnails: [],
  previews: [],
  videos: [],
  search_results: []
});
const hoveredIndex = ref(null);
const selectedVideo = ref(null);
const selectedVideoInfo = ref(null);

// Handle file selection
const handleFileChange = (e) => {
  file.value = e.target.files[0];
};

// Start preview on hover
const startPreview = (index) => {
  hoveredIndex.value = index;
};

// Stop preview
const stopPreview = () => {
  hoveredIndex.value = null;
};

// Play full video
const playFullVideo = (index) => {
  selectedVideo.value = results.value.videos[index];
  selectedVideoInfo.value = results.value.search_results ? results.value.search_results[index] : null;
  currentView.value = 'player';
};

// Back to results
const backToResults = () => {
  currentView.value = 'results';
};

// Reset to home page
const resetToHome = () => {
  currentView.value = 'search';
  query.value = '';
  searchQuery.value = '';
  file.value = null;
  results.value = {
    thumbnails: [],
    previews: [],
    videos: [],
    search_results: []
  };
  hoveredIndex.value = null;
  selectedVideo.value = null;
  selectedVideoInfo.value = null;
};

// Handle video loading errors
const handleVideoError = (event) => {
  console.error('Video loading error:', event);
  alert('Error loading video. Please try again.');
};

// Handle search submission
const handleSubmit = async () => {
  if (!query.value.trim()) {
    alert('Please enter a search query');
    return;
  }

  loading.value = true;
  searchQuery.value = query.value; // Store search query for display
  
  const formData = new FormData();
  formData.append('query', query.value);
  formData.append('use_demo', useDemo.value);
  
  if (!useDemo.value && file.value) {
    formData.append('file', file.value);
  }

  try {
    // Simulate a delay for the "Processing..." state
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Send request to backend
    const response = await axios.post(`${BACKEND_URL}/process`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    // Store results
    results.value = response.data;
    
    console.log('Search results:', response.data);
    
    // Change view to results
    currentView.value = 'results';
    
  } catch (error) {
    console.error('Error processing request:', error);
    
    let errorMessage = 'An error occurred while processing your request.';
    if (error.response) {
      errorMessage += ` Server responded with: ${error.response.status} ${error.response.statusText}`;
    } else if (error.request) {
      errorMessage += ' Please check if the backend server is running.';
    }
    
    alert(errorMessage);
  } finally {
    loading.value = false;
  }
};

// Test backend connection on component mount
onMounted(async () => {
  try {
    await axios.get(`${BACKEND_URL}/videos`);
    console.log('✅ Backend connection successful');
  } catch (error) {
    console.warn('❌ Backend connection failed:', error.message);
  }
});


</script>

<style scoped>
/* Style remains the same */
:root {
  --primary-orange: #FD9935;
}

/* Base container styling */
.container {
  width: 100vw;
  height: 100vh;
  background-color: white;
  position: fixed;
  top: 0;
  left: 0;
  padding: 0;
  margin: 0;
  overflow-y: auto;
}

/* Header logo styling - appears on all pages */
.header-logo {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 100;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.header-logo:hover {
  transform: scale(1.1);
}

.header-logo img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

/* Common content wrapper styling */
.content-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}

/* Search view specific styling */
.search-view {
  height: 100%;
  justify-content: center;
}

/* Results view specific styling */
.results-view {
  padding-top: 80px;
}

/* Player view specific styling */
.player-view {
  height: 100%;
  justify-content: center;
  padding-top: 80px;
}

/* Search info styling */
.search-info {
  text-align: center;
  margin-bottom: 2rem;
}

.search-query {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.results-count {
  color: #666;
  font-size: 1rem;
}

/* Main title styling */
.main-title {
  font-size: 2.5rem;
  font-weight: 700;
  text-align: center;
  color: #000;
  margin-bottom: 3rem;
  line-height: 1.2;
}

/* Search form styling */
.search-form {
  width: 100%;
  max-width: 700px;
}

.search-container {
  display: flex;
  align-items: center;
  border: 2px solid #FD9935;
  border-radius: 50px;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(253, 153, 53, 0.3);
  background-color: white;
  transition: box-shadow 0.3s ease;
}

.search-container:focus-within {
  box-shadow: 0 0 20px rgba(253, 153, 53, 0.5);
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  margin-left: 8px;
}

.logo {
  height: 30px;
  width: auto;
  border-radius: 50%;
}

.search-input {
  flex: 1;
  border: none;
  padding: 15px;
  font-size: 16px;
  outline: none;
  font-family: 'Inter', 'Avenir', sans-serif;
}

.search-button {
  background-color: #FD9935;
  color: white;
  border: none;
  padding: 15px 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 0 50px 50px 0;
  transition: background-color 0.3s ease, transform 0.1s ease;
  font-family: 'Inter', 'Avenir', sans-serif;
}

.search-button:hover:not(:disabled) {
  background-color: #e58726;
}

.search-button:active:not(:disabled) {
  transform: scale(0.97);
}

.search-button:disabled {
  background-color: #ffb367;
  cursor: not-allowed;
}

/* Utility classes for hidden elements */
.hidden-checkbox, .file-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Thumbnails grid styling */
.thumbnails-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  width: 100%;
  max-width: 1200px;
  padding: 20px;
}

.thumbnail-card {
  position: relative;
  border: 2px solid #FD9935;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  cursor: pointer;
  box-shadow: 0 0 15px rgba(253, 153, 53, 0.3);
  transition: all 0.3s ease;
}

.thumbnail-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 10px 25px rgba(253, 153, 53, 0.5);
}

.thumbnail-img, .preview-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Video info overlay */
.video-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  color: white;
  padding: 15px 10px 10px;
  display: flex;
  justify-content: space-between;
  align-items: end;
  font-size: 0.8rem;
}

.video-name {
  font-weight: 600;
  text-transform: capitalize;
}

.similarity-score {
  background-color: #FD9935;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Video container styling */
.video-container {
  width: 100%;
  max-width: 1000px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Video player styling */
.video-player {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  margin-bottom: 20px;
  aspect-ratio: 16 / 9;
}

/* Video metadata styling */
.video-metadata {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.video-metadata h3 {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 5px;
  text-transform: capitalize;
}

.video-metadata p {
  color: #666;
  font-size: 0.9rem;
}

/* Back button styling */
.back-button {
  margin-top: 20px;
  background-color: #FD9935;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Inter', 'Avenir', sans-serif;
}

.back-button:hover {
  background-color: #e58726;
  transform: scale(1.05);
}

.back-button:active {
  transform: scale(0.98);
}

/* Ensure font consistency throughout the application */
* {
  box-sizing: border-box;
  font-family: 'Inter', 'Avenir', sans-serif;
  margin: 0;
  padding: 0;
}

/* Global styles */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}
</style>


