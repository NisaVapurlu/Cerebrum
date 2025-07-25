document.getElementById("add-patient-modal-close").addEventListener("click", () => {
  document.getElementById("add-patient-modal-overlay").style.display = "none";
});

// Example: trigger from a button
document.getElementById("add-patient-btn").addEventListener("click", () => {
  document.getElementById("add-patient-modal-overlay").style.display = "flex";
});

