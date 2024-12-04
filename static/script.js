// script.js

async function fetchPlantFact() {
  try {
      const response = await fetch('/api/plants');
      const data = await response.json();

      const plants = data.data;
      const randomPlant = plants[Math.floor(Math.random() * plants.length)];
      const plantFact = `Did you know about the ${randomPlant.common_name}? Its scientific name is ${randomPlant.scientific_name}.`;

      document.getElementById('fact').innerText = plantFact;
  } catch (error) {
      console.error('Error fetching plant data:', error);
      document.getElementById('fact').innerText = 'Could not load a plant fact. Please try again later.';
  }
}

// Attach event listener to the button
document.getElementById('fetchFactButton').addEventListener('click', fetchPlantFact);
