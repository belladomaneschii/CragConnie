document.addEventListener("DOMContentLoaded", function () {
   const cragName = document.body.dataset.crag;
    // ========== Calling to the API ==========
      function updateFromAPI() {
      fetch(`/latest?crag=${encodeURIComponent(cragName)}`)
        .then(res => res.json())
        .then(data => {
          console.log("Fetched data from API:", data);
          if (data.temp !== null && data.humidity !== null) {
            tempGauge.refresh(data.temp);
            humidityGauge.refresh(data.humidity);
          } else {
            console.log("Data was null");
          }
        })
        .catch(err => console.error("API fetch error:", err));
    }

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

  // ========== Setting up Visul Gauges  ==========
  const tempGaugeEl = document.getElementById("tempGauge");
  const humidityGaugeEl = document.getElementById("humidityGauge");

  let tempGauge, humidityGauge;

  if (tempGaugeEl && humidityGaugeEl) {
    tempGauge = new JustGage({
      id: "tempGauge",
      value: 20,
      min: -5,
      max: 35,
      title: "Temperature (°C)",
      levelColors: ["#91c9f7", "#f9c802", "#f26c6c"]
    });

    humidityGauge = new JustGage({
      id: "humidityGauge",
      value: 65,
      min: 0,
      max: 100,
      title: "Humidity (%)",
      levelColors: ["#bde0fe", "#a2d2ff", "#ffb3c6"]
    });
1

  // ========== Funtioality for the stars ==========
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
  });

  // Fetch and display Connie score
async function fetchScore() {
  try {
    const res = await fetch(`/score?crag=${encodeURIComponent(cragName)}`);
;
    const data = await res.json();

    if (data.score !== undefined) {
      document.getElementById("scoreDisplay").textContent = ` ${data.score.toFixed(1)} / 100`;
    } else {
      document.getElementById("scoreDisplay").textContent = "No score available.";
    }
  } catch (err) {
    document.getElementById("scoreDisplay").textContent = "Error loading score.";
  }
}

// Call it once on load
fetchScore();

// ========== Displaying the history chart ==========
// ========== currenty has false test data inserted  ==========
// const ctx = document.getElementById("historyChart");
// if (ctx) {
//   const historyChart = new Chart(ctx, {
//     type: "line",
//     data: {
//       labels: ["8 AM", "10 AM", "12 PM", "2 PM", "4 PM", "6 PM"],
//       datasets: [
//         {
  //         label: "Temperature (°C)",
  //         data: [15, 16.5, 19, 20, 18, 17],
  //         borderColor: "#ff6384",
  //         backgroundColor: "rgba(255, 99, 132, 0.1)",
  //         tension: 0.4
  //       },
  //       {
  //         label: "Humidity (%)",
  //         data: [75, 70, 65, 60, 63, 68],
  //         borderColor: "#36a2eb",
  //         backgroundColor: "rgba(54, 162, 235, 0.1)",
  //         tension: 0.4
  //       }
  //     ]
  //   },
  //   options: {
  //     responsive: true,
  //     plugins: {
  //       legend: {
  //         position: "top"
  //       },
  //       title: {
  //         display: true,
  //         text: "Mock Crag History – Today"
  //       }
  //     }
  //   }
  // });
// }

}


    updateFromAPI();
    setInterval(updateFromAPI, 30000);
  }
});
