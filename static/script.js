document.addEventListener("DOMContentLoaded", function () {
  const cragName = document.body.dataset.crag;
  
  // ========== Nav bar Drop Down ==========
  const crags = [
    { name: "The Cave", link: "/crag/The%20Cave" },
    { name: "Little Babylon", link: "/crag/Little%20Babylon" }
  ];

  const dropdown = document.getElementById("locationDropdown");
  if (dropdown) {
    crags.forEach(crag => {
      const a = document.createElement("a");
      a.href = crag.link;
      a.textContent = `${crag.name}`;
      dropdown.appendChild(a);
    });
  }

  // ========== Setting up Visual Gauges ==========
  const tempGaugeEl = document.getElementById("tempGauge");
  const humidityGaugeEl = document.getElementById("humidityGauge");

  let tempGauge, humidityGauge;

  if (tempGaugeEl && humidityGaugeEl) {
    tempGauge = new JustGage({
      id: "tempGauge",
      value: 15,
      min: -5,
      max: 35,
      title: "",
      levelColors: ["#3498db", "#2ecc71", "#f39c12", "#e74c3c"],
      gaugeWidthScale: 0.6,
      counter: true,
      decimals: 1,
      customSectors: [{
        color: "#3498db",
        lo: -5,
        hi: 10
      }, {
        color: "#2ecc71",
        lo: 10,
        hi: 18
      }, {
        color: "#f39c12",
        lo: 18,
        hi: 25
      }, {
        color: "#e74c3c",
        lo: 25,
        hi: 35
      }]
    });

    humidityGauge = new JustGage({
      id: "humidityGauge",
      value: 60,
      min: 0,
      max: 100,
      title: "",
      levelColors: ["#e74c3c", "#2ecc71", "#3498db"],
      gaugeWidthScale: 0.6,
      counter: true,
      decimals: 0,
      customSectors: [{
        color: "#e74c3c",
        lo: 0,
        hi: 30
      }, {
        color: "#2ecc71",
        lo: 30,
        hi: 70
      }, {
        color: "#3498db",
        lo: 70,
        hi: 100
      }]
    });

    // ========== Fetch Latest Data from API ==========
    function updateFromAPI() {
      fetch(`/latest?crag=${encodeURIComponent(cragName)}`)
        .then(res => res.json())
        .then(data => {
          if (data.temp !== null && data.humidity !== null) {
            tempGauge.refresh(data.temp);
            humidityGauge.refresh(data.humidity);
            
            // Update last updated time
            const lastUpdateEl = document.getElementById("lastUpdateTime");
            if (lastUpdateEl && data.timestamp) {
              const updateTime = new Date(data.timestamp);
              lastUpdateEl.textContent = updateTime.toLocaleString();
            }
          }
        })
        .catch(err => console.error("API fetch error:", err));
    }

    // Update immediately and then every 30 seconds
    updateFromAPI();
    setInterval(updateFromAPI, 30000);
  }

  // ========== Check Wind Surfer Status ==========
  async function checkWindSurferStatus() {
    try {
      // Get recent ratings (last 4 hours) to see if wind surfers were reported
      const res = await fetch(`/ratings?crag=${encodeURIComponent(cragName)}`);
      const ratings = await res.json();
      
      const statusEl = document.getElementById("windSurferStatus");
      if (!statusEl) return;
      
      // Check ratings from last 4 hours
      const fourHoursAgo = new Date();
      fourHoursAgo.setHours(fourHoursAgo.getHours() - 4);
      
      const recentRatings = ratings.filter(r => {
        const ratingTime = new Date(r.visited_at || r.timestamp);
        return ratingTime > fourHoursAgo;
      });
      
      const windSurfersPresent = recentRatings.some(r => r.wind_surfers === 1);
      
      if (recentRatings.length === 0) {
        statusEl.innerHTML = '<span class="status-unknown">No recent reports</span>';
        statusEl.className = "indicator-status status-unknown";
      } else if (windSurfersPresent) {
        statusEl.innerHTML = '<span class="status-yes">⚠️ YES - Wind surfers reported</span>';
        statusEl.className = "indicator-status status-yes";
      } else {
        statusEl.innerHTML = '<span class="status-no">✓ NO - Clear conditions</span>';
        statusEl.className = "indicator-status status-no";
      }
    } catch (err) {
      console.error("Error checking wind surfer status:", err);
    }
  }

  // ========== Display Recent Ratings ==========
  async function displayRecentRatings() {
    try {
      const res = await fetch(`/ratings?crag=${encodeURIComponent(cragName)}`);
      const ratings = await res.json();
      
      const logEl = document.getElementById("ratingsLog");
      if (!logEl) return;
      
      if (ratings.length === 0) {
        logEl.innerHTML = '<p class="no-ratings">No ratings yet. Be the first to rate!</p>';
        return;
      }
      
      // Show last 10 ratings
      const recentRatings = ratings.slice(0, 10);
      
      let html = '<div class="ratings-list">';
      recentRatings.forEach(rating => {
        const visitTime = new Date(rating.visited_at || rating.timestamp);
        const timeAgo = getTimeAgo(visitTime);
        const stars = '★'.repeat(rating.rating) + '☆'.repeat(5 - rating.rating);
        const windSurferBadge = rating.wind_surfers === 1 
          ? '<span class="wind-badge">🌊 Wind surfers</span>' 
          : '';
        
        html += `
          <div class="rating-item">
            <div class="rating-stars">${stars}</div>
            <div class="rating-info">
              <span class="rating-time">${timeAgo}</span>
              ${windSurferBadge}
            </div>
          </div>
        `;
      });
      html += '</div>';
      
      logEl.innerHTML = html;
    } catch (err) {
      console.error("Error loading ratings:", err);
      const logEl = document.getElementById("ratingsLog");
      if (logEl) {
        logEl.innerHTML = '<p class="error">Error loading ratings</p>';
      }
    }
  }

  // Helper function to format time ago
  function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    
    return date.toLocaleDateString();
  }

  // Call these functions on page load
  if (cragName) {
    checkWindSurferStatus();
    displayRecentRatings();
    
    // Refresh every minute
    setInterval(() => {
      checkWindSurferStatus();
      displayRecentRatings();
    }, 60000);
  }

  // ========== Functionality for the Stars ==========
  const stars = document.querySelectorAll(".star-rating .star");
  const ratingInput = document.getElementById("ratingInput");

  if (stars.length && ratingInput) {
    stars.forEach(star => {
      star.addEventListener("click", () => {
        const value = parseInt(star.getAttribute("data-value"));
        ratingInput.value = value;

        stars.forEach(s => {
          const sValue = parseInt(s.getAttribute("data-value"));
          s.classList.toggle("filled", sValue <= value);
        });
      });

      // Add hover effect
      star.addEventListener("mouseenter", () => {
        const value = parseInt(star.getAttribute("data-value"));
        stars.forEach(s => {
          const sValue = parseInt(s.getAttribute("data-value"));
          s.classList.toggle("hovered", sValue <= value);
        });
      });

      star.addEventListener("mouseleave", () => {
        stars.forEach(s => s.classList.remove("hovered"));
      });
    });
  }

  // ========== Rating Form Submission ==========
  const ratingForm = document.getElementById("rating-form");
  if (ratingForm) {
    ratingForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const rating = parseInt(ratingInput.value);
      const windSurfers = document.getElementById("windSurfers").checked ? 1 : 0;
      const visitTime = document.getElementById("visitTime").value;

      if (!rating) {
        showMessage("Please select a rating", "error");
        return;
      }

      // Calculate visited_at timestamp based on selection
      let visitedAt = new Date();
      if (visitTime === "1h") {
        visitedAt.setHours(visitedAt.getHours() - 1);
      } else if (visitTime === "2h") {
        visitedAt.setHours(visitedAt.getHours() - 2);
      } else if (visitTime === "4h") {
        visitedAt.setHours(visitedAt.getHours() - 4);
      } else if (visitTime === "today") {
        visitedAt.setHours(9, 0, 0); // Set to 9 AM today
      }

      const payload = {
        crag: cragName,
        rating: rating,
        wind_surfers: windSurfers,
        visited_at: visitedAt.toISOString().slice(0, 19).replace('T', ' ')
      };

      try {
        const res = await fetch("/ratings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          showMessage("✓ Thanks for your rating!", "success");
          
          // Reset form
          ratingInput.value = "";
          stars.forEach(s => s.classList.remove("filled"));
          document.getElementById("windSurfers").checked = false;
          document.getElementById("visitTime").value = "now";
          
          // Refresh displays
          fetchScore();
          checkWindSurferStatus();
          displayRecentRatings();
        } else {
          showMessage("Failed to submit rating", "error");
        }
      } catch (err) {
        showMessage("Error submitting rating", "error");
        console.error(err);
      }
    });
  }

  function showMessage(text, type) {
    const messageEl = document.getElementById("submitMessage");
    if (messageEl) {
      messageEl.textContent = text;
      messageEl.className = `submit-message ${type}`;
      messageEl.style.display = "block";
      
      setTimeout(() => {
        messageEl.style.display = "none";
      }, 3000);
    }
  }

  // ========== Fetch and Display Connie Score ==========
  async function fetchScore() {
    try {
      const res = await fetch(`/score?crag=${encodeURIComponent(cragName)}`);
      const data = await res.json();

      const scoreDisplay = document.getElementById("scoreDisplay");
      if (data.score !== undefined) {
        const score = data.score.toFixed(1);
        scoreDisplay.textContent = `${score} / 100`;
        
        // Add color based on score
        scoreDisplay.className = "score-box";
        if (score >= 80) {
          scoreDisplay.classList.add("score-excellent");
        } else if (score >= 60) {
          scoreDisplay.classList.add("score-good");
        } else if (score >= 40) {
          scoreDisplay.classList.add("score-fair");
        } else {
          scoreDisplay.classList.add("score-poor");
        }
      } else {
        scoreDisplay.textContent = "No score available";
      }
    } catch (err) {
      document.getElementById("scoreDisplay").textContent = "Error loading score";
      console.error(err);
    }
  }

  fetchScore();

  // ========== Rainfall Chart ==========
// ========== Rainfall Chart ==========
const rainfallCanvas = document.getElementById("rainfallChart");
if (rainfallCanvas) {
  const lat = rainfallCanvas.dataset.lat;
  const lon = rainfallCanvas.dataset.lon;

  if (!lat || !lon) {
    console.error("Missing data-lat or data-lon on rainfall canvas element");
    const parent = rainfallCanvas.parentElement;
    if (parent) parent.innerHTML = '<p class="error">Rainfall data unavailable (missing coordinates)</p>';
  } else {
    fetch(`/api/rainfall?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`)
      .then(res => {
        if (!res.ok) return res.json().then(j => Promise.reject(j));
        return res.json();
      })
      .then(data => {
        // If API returned error structure
        if (!Array.isArray(data) || data.length === 0) {
          rainfallCanvas.parentElement.innerHTML = '<p class="no-data">No rainfall data available for the past 7 days.</p>';
          return;
        }

        const labels = data.map(item => item[0]);
        const rainfall = data.map(item => item[1]);

        new Chart(rainfallCanvas, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [{
              label: "Rainfall (mm)",
              data: rainfall,
              borderWidth: 1,
              borderRadius: 5,
            }]
          },
          options: { responsive: true, maintainAspectRatio: true /* ... keep your options ... */ }
        });
      })
      .catch(err => {
        console.error("Error loading rainfall:", err);
        let msg = 'Error loading rainfall data.';
        if (err && err.error) msg += ' ' + (err.error);
        rainfallCanvas.parentElement.innerHTML = `<p class="error">${msg}</p>`;
      });
  }
}

  // ========== Conditions Chart ==========
  const conditionsCanvas = document.getElementById('conditionsChart');
  if (conditionsCanvas) {
    const ctx = conditionsCanvas.getContext('2d');
    const conditionsChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Temperature (°C)',
            data: [],
            borderColor: 'rgba(255, 99, 132, 1)',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5,
          },
          {
            label: 'Humidity (%)',
            data: [],
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Value',
            }
          },
          x: {
            title: {
              display: true,
              text: 'Time',
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            mode: 'index',
            intersect: false,
          }
        }
      }
    });

    function updateChart(range) {
      fetch(`/api/conditions?crag=${encodeURIComponent(cragName)}&range=${range}`)
        .then(res => res.json())
        .then(data => {
          conditionsChart.data.labels = data.labels;
          conditionsChart.data.datasets[0].data = data.temperature;
          conditionsChart.data.datasets[1].data = data.humidity;
          conditionsChart.update();
        })
        .catch(console.error);
    }

    const btn12h = document.getElementById("btn-12h");
    const btn7d = document.getElementById("btn-7d");

    if (btn12h && btn7d) {
      btn12h.addEventListener("click", () => {
        btn12h.classList.add("active");
        btn7d.classList.remove("active");
        updateChart("12h");
      });

      btn7d.addEventListener("click", () => {
        btn7d.classList.add("active");
        btn12h.classList.remove("active");
        updateChart("7d");
      });
    }

    // Initial load
    updateChart("12h");
    
    // Refresh chart every 2 minutes
    setInterval(() => {
      const activeRange = btn12h.classList.contains("active") ? "12h" : "7d";
      updateChart(activeRange);
    }, 120000);
  }
});