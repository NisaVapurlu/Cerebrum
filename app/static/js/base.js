async function getDoctorInfo() {
    try {
        const response = await fetch("http://127.0.0.1:8000/doctor-info", {
            method: "GET",
            credentials: "include"  // ✅ Send cookies (session_token)
        });

        if (!response.ok) {
            throw new Error("Failed to fetch doctor info");
        }

        const data = await response.json();
        console.log("Doctor info:", data.data);

        // Example: Update HTML dynamically
        document.getElementById("patient-count").textContent = data.data.patient_count;
        document.getElementById("doctor-name").textContent = data.data.name + " " + data.data.surname;
        document.getElementById("doctor-institution").textContent = data.data.institution;
        document.getElementById("doctor-title").textContent = data.data.title;
        document.getElementById("doctor-created-on").textContent = data.data.created_on;

    } catch (error) {
        console.error("Error:", error);
        alert("Could not fetch doctor info");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Doctor Info Modal Elements
    const doctorCircle = document.getElementById('doctor-circle');
    const doctorInfoModal = document.getElementById('doctor-info-modal');
    const closeDoctorModal = document.getElementById('close-doctor-modal');
    const changePasswordButton = document.getElementById('change-password-btn'); 

    // Change Password Modal Elements
    const changePasswordModal = document.getElementById('change-password-modal'); 
    const closePasswordModal = document.getElementById('close-password-modal');
    const changePasswordForm = document.getElementById('change-password-form'); 

    // Doctor Info Modal Logic
    doctorCircle.addEventListener('click', async (event) => {
        event.preventDefault();
        await getDoctorInfo();

        doctorInfoModal.style.display = 'flex';
    });

    closeDoctorModal.addEventListener('click', () => {
        doctorInfoModal.style.display = 'none';
    });

    // Open Change Password Modal from Doctor Info Modal
    changePasswordButton.addEventListener('click', () => {
        if (doctorInfoModal) { 
            doctorInfoModal.style.display = 'none'; // Doktor profil modalını gizle
        }
        if (changePasswordModal) { 
            changePasswordModal.style.display = 'flex'; // Şifre değiştirme modalını göster
        }
    });

    // Close Change Password Modal
    closePasswordModal.addEventListener('click', () => {
        changePasswordModal.style.display = 'none';
    });

    // Handle Change Password Form Submission (Optional: Add actual password change logic here)
    changePasswordForm.addEventListener('submit', (event) => {
        event.preventDefault(); // Sayfanın yenilenmesini engelle
        // Burada şifre değiştirme mantığını ekleyebilirsiniz (örneğin, AJAX isteği gönderme)
        alert('Password change request submitted!'); // Basit bir örnek
        changePasswordModal.style.display = 'none'; // Modalı kapat
        // Formu sıfırlamak isterseniz: event.target.reset();
    });
});