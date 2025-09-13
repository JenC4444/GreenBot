const API = "http://127.0.0.1:5001";

const plantCategories = [
  "desert_cactus","succulent","tropical_fern","tropical_foliage",
  "mediterranean_herb","soft_herb","orchid","shade_loving",
  "bright_flowering","temperate_tree","fruit_veg","bonsai"
];

const plantListEl = document.getElementById("plantList");
const selectedName = document.getElementById("selectedName");
const connectBtn = document.getElementById("connectBtn");
const dashboard = document.getElementById("dashboard");
const searchInput = document.getElementById("searchInput");

let currentPlant = plantCategories[0];
let connectedPlant = null;

function renderPlantList(filter="") {
  plantListEl.innerHTML = "";
  plantCategories.filter(p=>p.includes(filter.toLowerCase()))
    .forEach(p=>{
      const li = document.createElement("li");
      li.className = "plant-item";
      if(p===currentPlant) li.classList.add("active");
      const name = p.split("_").map(w=>w[0].toUpperCase()+w.slice(1)).join(" ");
      const status = (p===connectedPlant) ? "🟢" : "🔴";
      li.textContent = `${name} ${status}`;
      li.addEventListener("click", ()=>{
        currentPlant=p;
        selectedName.textContent=name;
        updateDashboard();
        renderPlantList(searchInput.value);
      });
      plantListEl.appendChild(li);
    });
}

async function fetchUIState() {
  try {
    const res = await fetch(`${API}/ui_state`);
    const data = await res.json();
    dashboard.innerHTML = `
      <div class="card-container ${getCardClass(data.soil?.label||'')}">
        <div class="card-label">Humidité</div>
        <div class="card-emoji">${data.soil?.label||"❔"}</div>
      </div>
      <div class="card-container ${getCardClass(data.temp?.label||'')}">
        <div class="card-label">Température</div>
        <div class="card-emoji">${data.temp?.label||"❔"}</div>
      </div>
      <div class="card-container ${getCardClass(data.light?.label||'')}">
        <div class="card-label">Luminosité</div>
        <div class="card-emoji">${data.light?.label||"❔"}</div>
      </div>
      <div class="card-container">
        <div class="card-label">Mood</div>
        <div class="card-emoji">${data.mood?.emoji||"⌛"} ${data.mood?.text||"waiting"}</div>
      </div>
    `;
  } catch(err){ console.error("Erreur fetch UI:", err); }
}

async function setPlantOnServer(pid){
  try{
    await fetch(`${API}/set_plant`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ plant_id: pid })
    });
  }catch(e){ console.error("set_plant failed", e); }
}

connectBtn.addEventListener("click", async ()=>{
  connectedPlant = (connectedPlant===currentPlant) ? null : currentPlant;
  if (connectedPlant) {
    await setPlantOnServer(connectedPlant); // informs backend
  }
  updateDashboard();
  renderPlantList(searchInput.value);
});

function updateDashboard(){ 
  fetchUIState(); 
  connectBtn.textContent = (connectedPlant===currentPlant) ? "Disconnect" : "Connect"; 
}

function getCardClass(label){
  if(label.includes("🥵") || label.includes("🧨")) return "card-hot";
  if(label.includes("🥶")) return "card-cold";
  if(label.includes("💦")) return "card-wet";
  if(label.includes("dry")) return "card-dry";
  if(label.includes("🔆")) return "card-bright";
  if(label.includes("🌑")) return "card-dark";
  return "card-normal";
}

searchInput.addEventListener("input", ()=>{ renderPlantList(searchInput.value); });

selectedName.textContent = currentPlant.split("_").map(w=>w[0].toUpperCase()+w.slice(1)).join(" ");
renderPlantList();
fetchUIState();
setInterval(fetchUIState, 5000);