let currentCategory = 'washington';
let photoToDownload = '';
let globalData = null;

document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    currentCategory = urlParams.get('cat') || 'washington';
    
    try {
        const response = await fetch('/api/data');
        globalData = await response.json();
    } catch (e) { 
        console.log("Python server offline. Please run py app.py"); 
        return;
    }

    const pageData = globalData.pages[currentCategory];
    const images = globalData.images[currentCategory] || [];

    if (pageData) {
        if (currentCategory === 'washington') {
            document.getElementById('dynamic-title').textContent = 'MY GALLERY 0721120228';
        } else {
            document.getElementById('dynamic-title').textContent = pageData.title;
        }
        
        document.getElementById('dynamic-description').textContent = pageData.description;

        const lovedCategories = JSON.parse(localStorage.getItem('lovedCategories') || '[]');
        if (lovedCategories.includes(currentCategory)) {
            document.getElementById('heart-icon').classList.add('active');
            document.getElementById('heart-icon').innerHTML = '&#9829;'; 
        }

        const gridContainer = document.getElementById('gallery-grid');
        gridContainer.innerHTML = ''; 

        if (images.length > 0) {
            images.forEach(imgSrc => {
                const img = document.createElement('img');
                img.src = `/static/images/${imgSrc}`; 
                img.onclick = function() { 
                    photoToDownload = this.src; 
                    attemptDownload(); 
                };
                gridContainer.appendChild(img);
            });
        } else {
            gridContainer.innerHTML = '<p style="text-align:center; width:100%; grid-column: 1/-1; color:#888; padding: 60px 0; font-size: 1.1rem;">No photos uploaded to this gallery yet.</p>';
        }

        const navLinks = document.querySelectorAll('.nav-links > a');
        navLinks.forEach(link => {
            if (link.dataset.cat === currentCategory) {
                link.classList.add('active');
            }
        });
    }
});

function goToNextCategory() {
    if (!globalData) return;
    
    const categoryOrder = Object.keys(globalData.pages);
    let currentIndex = categoryOrder.indexOf(currentCategory);

    if (currentIndex !== -1 && currentIndex < categoryOrder.length - 1) {
        let nextCategory = categoryOrder[currentIndex + 1];
        window.location.href = `/gallery?cat=${nextCategory}`;
    } else {
        window.location.href = `/gallery?cat=${categoryOrder[0]}`;
    }
}

function toggleDropdown(event) {
    event.preventDefault();
    event.stopPropagation();
    document.querySelector('.dropdown').classList.toggle('active');
}

function toggleDotsMenu(event) {
    event.stopPropagation();
    document.getElementById('dots-menu').classList.toggle('active');
}

window.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('active'));
    }
    if (!e.target.closest('.action-icons')) {
        document.getElementById('dots-menu').classList.remove('active');
    }
});

function toggleFavorite() {
    const icon = document.getElementById('heart-icon');
    let lovedCategories = JSON.parse(localStorage.getItem('lovedCategories') || '[]');
    
    if (lovedCategories.includes(currentCategory)) {
        lovedCategories = lovedCategories.filter(cat => cat !== currentCategory);
        icon.classList.remove('active');
        icon.innerHTML = '&#9825;'; 
    } else {
        lovedCategories.push(currentCategory);
        icon.classList.add('active');
        icon.innerHTML = '&#9829;'; 
    }
    localStorage.setItem('lovedCategories', JSON.stringify(lovedCategories));
}

function attemptDownload() {
    if (!photoToDownload) {
        const firstImg = document.querySelector('#gallery-grid img');
        if (firstImg) {
            photoToDownload = firstImg.src;
        } else {
            alert("There are no photos to download in this gallery.");
            return;
        }
    }
    document.getElementById('email-modal').style.display = 'flex';
}

function processEmailNext() {
    const email = document.getElementById('download-email').value;
    if (!email || !email.includes('@')) {
        alert("Please enter a valid email address.");
        return;
    }
    localStorage.setItem('userEmail', email);
    
    closeModal('email-modal');
    document.getElementById('checkout-modal').style.display = 'flex';
}

function selectDownloadOption(element) {
    document.querySelectorAll('.download-option').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
}

function executeFinalDownload() {
    const selectedOption = document.querySelector('.download-option.selected span').innerText;
    
    if (selectedOption.includes("Google") || selectedOption.includes("Dropbox")) {
        alert("Simulated: Connecting to cloud storage API...");
    } else {
        const a = document.createElement('a');
        a.href = photoToDownload;
        a.download = 'Washington_Photography.jpg';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
    
    closeModal('checkout-modal');
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        event.target.style.display = 'none';
    }
}