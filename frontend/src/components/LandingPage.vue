<template>
  <div class="landing-container">
    <div class="content-section">
      <div class="left-section">
        <h1>Welcome to Montada</h1>
        <p class="description">
          Montada is an innovative NLP-based sports video indexer that revolutionizes how you analyze and navigate through sports content. Our advanced AI technology understands the context and action in your sports videos, making them searchable and accessible like never before.
        </p>
        <button @click="$emit('try-it')" class="try-button">Try it out</button>
      </div>
      
      <div class="right-section">
        <div class="comparison-container">
          <div class="comparison-image">
            <img src="../assets/comparison/before.jpg" alt="Before analysis" class="comparison-img">
            <span class="image-label">Before Analysis</span>
          </div>
          <div class="comparison-image">
            <img src="../assets/comparison/after.jpg" alt="After analysis" class="comparison-img">
            <span class="image-label">With Montada Analysis</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LandingPage'
}
</script>

<style scoped>
.landing-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.content-section {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 4rem;
  padding: 2rem;
}

.left-section {
  flex: 1;
  padding-right: 2rem;
}

.right-section {
  flex: 1;
}

h1 {
  font-size: 3rem;
  margin-bottom: 1.5rem;
  color: #2c3e50;
  font-weight: bold;
}

.description {
  font-size: 1.2rem;
  line-height: 1.6;
  color: #34495e;
  margin-bottom: 2rem;
}

.try-button {
  display: inline-block;
  padding: 1rem 2rem;
  font-size: 1.2rem;
  background-color: #3498db;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.try-button:hover {
  background-color: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}

.comparison-container {
  display: flex;
  gap: 1.5rem;
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.comparison-image {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.comparison-img {
  width: 100%;
  height: auto;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.image-label {
  font-size: 1rem;
  color: #2c3e50;
  font-weight: 500;
}
</style> 