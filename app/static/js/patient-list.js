
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("add-patient-modal-close").addEventListener("click", () => {
    document.getElementById("add-patient-modal-overlay").style.display = "none";
  });

  // Example: trigger from a button
  document.getElementById("add-patient-btn").addEventListener("click", () => {
    document.getElementById("add-patient-modal-overlay").style.display = "flex";
  });

  // Handle add patient form submission
  document.querySelector(".add-patient-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    
    // Input'ları placeholder ile bul
    formData.append("name", document.getElementById('patient-name').value);
    formData.append("surname", document.getElementById('patient-surname').value);
    formData.append("height", document.getElementById('patient-height').value);
    formData.append("weight", document.getElementById('patient-weight').value);
    formData.append("age", document.getElementById('patient-age').value);
    formData.append("gender", document.querySelector('input[name="gender"]:checked').value);

    try {
      const response = await fetch("/create-patient", {
        method: "POST",
        body: formData
      });
      
      const result = await response.json();
      
      if (response.ok) {
        alert(result.message);
        document.getElementById("add-patient-modal-overlay").style.display = "none";
        // Sayfayı yenile
        location.reload();
      } else {
        alert(result.error || "Hasta eklenemedi.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Bir hata oluştu.");
    }
  });

});