const aboutLink = document.getElementById('about-link');
const aboutModal = document.getElementById('about-modal');
const closeModal = document.getElementById('close-modal');

aboutLink.addEventListener('click', () => {
    aboutModal.style.display = 'flex';
});

closeModal.addEventListener('click', () => {
    aboutModal.style.display = 'none';
});

