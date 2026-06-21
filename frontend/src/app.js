const app = (() => {
  let currentJobId = null;
  const API_BASE = "http://localhost:8000"; // Adjust if hosted differently

  // Elements
  const analyzeBtn = document.getElementById("analyze-btn");
  const loadingOverlay = document.getElementById("loading-overlay");
  const resultsContainer = document.getElementById("results-container");

  /**
   * Handles folder upload containing multiple feature files
   */
  async function handleFolderUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const folderDropzone = document.getElementById("folder-dropzone");
    folderDropzone.classList.remove("dragover");
    
    const formData = new FormData();
    let numValidFiles = 0;
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file.name.toLowerCase().endsWith(".tif") || file.name.toLowerCase().endsWith(".tiff")) {
        formData.append("files", file);
        numValidFiles++;
      }
    }

    if (numValidFiles === 0) {
      alert("No valid .tif or .tiff files found in the folder.");
      return;
    }

    document.getElementById("folder-name").textContent = `${numValidFiles} GeoTIFF(s) uploading...`;
    folderDropzone.classList.add("uploaded");

    let uploadUrl = `${API_BASE}/upload_folder`;
    if (currentJobId) {
      formData.append("job_id", currentJobId);
    }

    try {
      const response = await fetch(uploadUrl, {
        method: "POST",
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(await response.text());
      }
      
      const data = await response.json();
      
      currentJobId = data.job_id;
      document.getElementById("job-id-text").textContent = currentJobId;
      document.getElementById("job-id-display").style.display = "block";
      analyzeBtn.disabled = false;
      
      document.getElementById("folder-name").textContent = `${numValidFiles} GeoTIFF(s) uploaded`;

      const featuresList = document.getElementById("mapped-features-list");
      if (data.mapped_features && data.mapped_features.length > 0) {
        featuresList.innerHTML = "<strong>Mapped:</strong> " + data.mapped_features.map(f => `<span class="risk-badge" style="background:rgba(59,130,246,0.2);color:#93C5FD;margin:2px;display:inline-block;">${f}</span>`).join(" ");
      }

    } catch (err) {
      console.error("Upload error:", err);
      alert("Failed to upload folder: " + err.message);
      folderDropzone.classList.remove("uploaded");
      document.getElementById("folder-name").textContent = "";
    }
  }

  /**
   * Run the analysis pipeline
   */
  async function runAnalysis() {
    if (!currentJobId) return;

    const zoneMethod = document.getElementById("zone-method").value;
    const nClusters = parseInt(document.getElementById("n-clusters").value, 10);
    const fillDepressions = document.getElementById("fill-depressions").checked;

    const requestBody = {
      job_id: currentJobId,
      zone_method: zoneMethod,
      n_clusters: nClusters,
      fill_depressions: fillDepressions,
      model_type: "random_forest",
      target_crs: "EPSG:32644"
    };

    loadingOverlay.classList.add("active");

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      renderResults(data);

    } catch (err) {
      console.error("Analysis error:", err);
      alert("Analysis failed: " + err.message);
    } finally {
      loadingOverlay.classList.remove("active");
    }
  }

  /**
   * Render the analysis results
   */
  function renderResults(data) {
    if (!data || !data.predictions || data.predictions.length === 0) {
      resultsContainer.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-triangle-exclamation" style="color: var(--warning);"></i>
          <h2>No Zones Found</h2>
          <p>The analysis did not identify any viable zones.</p>
        </div>
      `;
      return;
    }

    const { zones, predictions } = data;

    let html = `<div class="dashboard-grid">`;

    // Map zones to predictions
    predictions.forEach(pred => {
      const zoneStats = zones.find(z => z.zone_id === pred.zone_id);
      if (!zoneStats) return;

      let riskClass = "risk-low";
      if (pred.risk_score > 0.6) riskClass = "risk-high";
      else if (pred.risk_score > 0.3) riskClass = "risk-medium";

      html += `
        <div class="glass-panel zone-card ${riskClass}">
          <div class="zone-header">
            <div class="zone-id">Zone ${pred.zone_id}</div>
            <div class="risk-badge">${pred.waterlogging_risk || 'Unknown'} Risk</div>
          </div>
          
          <div class="stat-grid">
            <div class="stat-item">
              <span class="stat-label">Elevation (m)</span>
              <span class="stat-value">${zoneStats.mean_elevation.toFixed(1)}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Slope (deg)</span>
              <span class="stat-value">${zoneStats.mean_slope.toFixed(1)}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">TWI</span>
              <span class="stat-value">${zoneStats.mean_twi.toFixed(2)}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Depression (m)</span>
              <span class="stat-value">${zoneStats.mean_depression_depth.toFixed(2)}</span>
            </div>
          </div>

          <div class="recommendations">
            <p class="drainage">
              <i class="fa-solid fa-water"></i> <strong>Drainage:</strong> ${pred.drainage_priority}
            </p>
            <p class="irrigation">
              <i class="fa-solid fa-droplet"></i> <strong>Irrigation:</strong> ${pred.irrigation_recommendation}
            </p>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    
    // Add a map placeholder note at the bottom
    html += `
      <div class="glass-panel" style="margin-top: 1.5rem; text-align: center; padding: 3rem;">
        <i class="fa-solid fa-map-location-dot" style="font-size: 3rem; color: var(--accent-blue); margin-bottom: 1rem;"></i>
        <h3>Geospatial Data Generated</h3>
        <p style="color: var(--text-secondary);">
          The GeoJSON data for these zones has been saved to the server and can be rendered dynamically in a map engine like Leaflet or Mapbox.
        </p>
      </div>
    `;

    resultsContainer.innerHTML = html;
  }

  // Setup drag and drop visual cues
  const dropzones = document.querySelectorAll('.upload-zone');
  dropzones.forEach(dz => {
    dz.addEventListener('dragover', (e) => {
      e.preventDefault();
      dz.classList.add('dragover');
    });
    dz.addEventListener('dragleave', (e) => {
      e.preventDefault();
      dz.classList.remove('dragover');
    });
    dz.addEventListener('drop', (e) => {
      e.preventDefault();
      dz.classList.remove('dragover');
      
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        // Find the associated file input
        const fileInput = dz.nextElementSibling;
        fileInput.files = files;
        // Manually trigger the onchange event
        const event = new Event('change');
        fileInput.dispatchEvent(event);
      }
    });
  });

  return {
    handleFolderUpload,
    runAnalysis
  };
})();
