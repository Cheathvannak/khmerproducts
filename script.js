// ---------------------------
// API Configuration
// ---------------------------
// Use localhost for development, with fallback detection
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://127.0.0.1:5000/api' 
    : '/api';

// Data will be loaded from API
let sampleProducts = [];
let manufacturers = [];
let categories = [];

// API Helper Functions
async function fetchFromAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching from ${endpoint}:`, error);
        throw error;
    }
}

// Load all data from API
async function loadAllData() {
    try {
        console.log('Loading data from database API...');
        
        // Load products
        const productsData = await fetchFromAPI('/products');
        sampleProducts = productsData.map(product => ({
            id: product.id,
            name: product.name,
            category: product.category,
            description: product.description || product.manufacturer_name,
            manufacturer: product.manufacturer_name,
            imagePath: product.image_path
        }));
        
        // Load manufacturers
        const manufacturersData = await fetchFromAPI('/manufacturers');
        manufacturers = manufacturersData.map(manufacturer => ({
            id: manufacturer.id,
            name: manufacturer.name,
            description: manufacturer.description || manufacturer.name,
            logoPath: manufacturer.logo_path,
            businessName: manufacturer.business_name || '',
            businessAddress: manufacturer.business_address || '',
            businessContact: manufacturer.business_contact || '',
            businessSocialNetwork: manufacturer.business_social_network || ''
        }));
        
        // Load categories
        categories = await fetchFromAPI('/categories');
        
        console.log(`Loaded ${sampleProducts.length} products, ${manufacturers.length} manufacturers, ${categories.length} categories from database`);
        
        // Re-render the page with new data
        renderProducts();
        updateAllBadges();
        
    } catch (error) {
        console.error('Failed to load data from API:', error);
        // Fallback to empty arrays if API fails
        sampleProducts = [];
        manufacturers = [];
        categories = [];
        alert('Failed to load data from database. Please make sure the API server is running.');
    }
}

// ---------------------------
// Global state
// ---------------------------
let currentCategory = 'Home';
let searchTerm = '';
let currentManufacturer = null; // When set, filter by this manufacturer

// ---------------------------
// Cached DOM references
// ---------------------------
const searchInput = document.getElementById('searchInput');
const productsContainer = document.getElementById('productsContainer');
const productsTitle = document.getElementById('productsTitle');
const homeBadge = document.getElementById('homeBadge');

// ---------------------------
// App initialization
// ---------------------------
// Initialize the application once the DOM is ready
// - sets up event listeners
// - loads data from API
// - renders initial products
// - updates the home badge (counter disabled by design)
document.addEventListener('DOMContentLoaded', async function() {
    initializeEventListeners();
    await loadAllData();
    renderProducts();
    updateHomeBadge();
});

// =========================================================
// Event Listeners & Navigation
// =========================================================
function initializeEventListeners() {
    // Search input: re-render products on each change
    searchInput.addEventListener('input', function(e) {
        searchTerm = e.target.value.toLowerCase();
        renderProducts();
    });

    // Search input: handle Enter key press in mobile view
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && window.innerWidth <= 768) {
            // Close mobile menu and scroll to products section
            closeMobileMenu();
            
            // Scroll to products section after a short delay to ensure menu closes first
            setTimeout(() => {
                const productsSection = document.querySelector('.products-section');
                if (productsSection) {
                    productsSection.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start' 
                    });
                }
            }, 300);
        }
    });

    // Category buttons: set active category
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            selectCategory(category);
        });
    });
}

// ---------------------------
// Category selection handler
// ---------------------------
function selectCategory(category) {
    currentCategory = category;
    currentManufacturer = null; // Clear manufacturer filter on category change
    searchTerm = '';
    searchInput.value = '';
    
    // Update active state in the sidebar
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => btn.classList.remove('active'));
    
    const activeButton = document.querySelector(`[data-category="${category}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Show/hide search container based on category
    const searchContainer = document.getElementById('searchContainer');
    if (searchContainer) {
        if (category === 'Home') {
            searchContainer.style.display = 'none';
        } else {
            searchContainer.style.display = 'block';
        }
    }
    
    // Adjust products section layout based on category
    const productsSection = document.querySelector('.products-section');
    const productsContainer = document.getElementById('productsContainer');
    
    if (productsSection && productsContainer) {
        if (category === 'Home') {
            // Home page: smaller products section, single column
            productsSection.style.width = '384px';
            productsContainer.style.display = 'flex';
            productsContainer.style.flexDirection = 'column';
            productsContainer.style.gridTemplateColumns = '';
            productsContainer.style.gap = '1rem';
        } else {
            // Other pages: wider products section, 2-column grid
            productsSection.style.width = '600px';
            productsContainer.style.display = 'grid';
            productsContainer.style.flexDirection = '';
            productsContainer.style.gridTemplateColumns = '1fr 1fr';
            productsContainer.style.gap = '1.5rem';
        }
    }
    
    // Show/hide company image based on category
    const companyImageContainer = document.querySelector('.company-image-container');
    
    if (companyImageContainer) {
        companyImageContainer.style.display = 'flex';
    }
    
    // Update products display
    renderProducts();
}

// ---------------------------
// Manufacturer filtering
// ---------------------------
function selectManufacturer(manufacturer) {
    currentManufacturer = manufacturer;
    renderProducts();
    
    // Close mobile menu if open (for better UX on mobile)
    if (window.innerWidth <= 768) {
        closeMobileMenu();
        
        // Scroll to products section after a short delay to ensure menu closes first
        setTimeout(() => {
            const productsSection = document.querySelector('.products-section');
            if (productsSection) {
                productsSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }
        }, 300);
    }
}

function clearManufacturerFilter() {
    currentManufacturer = null;
    renderProducts();
}

// Make functions globally accessible for inline onclick handlers
window.selectManufacturer = selectManufacturer;
window.clearManufacturerFilter = clearManufacturerFilter;

// ---------------------------
// Data helpers
// ---------------------------
// Compute products after applying category, manufacturer, and search filters
function getFilteredProducts() {
    let filteredProducts = sampleProducts.filter(product => {
        const matchesCategory = currentCategory === 'Home' || currentCategory === 'All Products' || product.category === currentCategory;
        const matchesManufacturer = currentManufacturer === null || product.manufacturer === currentManufacturer;
        const matchesSearch = searchTerm === '' || 
            product.name.toLowerCase().includes(searchTerm) ||
            product.description.toLowerCase().includes(searchTerm) ||
            product.category.toLowerCase().includes(searchTerm);
        
        return matchesCategory && matchesManufacturer && matchesSearch;
    });
    
    // Sort alphabetically when in 'All Products' and no manufacturer is selected
    if (currentCategory === 'All Products' && currentManufacturer === null) {
        filteredProducts.sort((a, b) => a.name.localeCompare(b.name));
    }
    
    return filteredProducts;
}

// ---------------------------
// Rendering
// ---------------------------
function renderProducts() {
    // Title reflects current category and manufacturer filter (if any)
    let titleText = currentCategory === 'Home' ? 'About Us' : currentCategory;
    if (currentManufacturer) {
        titleText = `${currentManufacturer} - ${titleText}`;
    }
    productsTitle.textContent = titleText;
    
    // Clear existing items
    productsContainer.innerHTML = '';
    
    // Handle company section display based on category
    const companySection = document.querySelector('.company-section');
    if (companySection) {
        if (currentCategory === 'Home' && !currentManufacturer) {
            // Show Made in Cambodia poster only on Home page
            if (!companySection.querySelector('.company-image-container')) {
                companySection.innerHTML = `
                    <div class="company-image-container">
                        <img src="made-in-cambodia-poster.jpg" alt="Made in Cambodia" class="company-image">
                    </div>
                `;
            }
        } else if (!currentManufacturer) {
            // For other categories, show manufacturer card if there's a dominant manufacturer
            const categoryProducts = getFilteredProducts();
            const manufacturerCounts = {};
            
            categoryProducts.forEach(product => {
                manufacturerCounts[product.manufacturer] = (manufacturerCounts[product.manufacturer] || 0) + 1;
            });
            
            const dominantManufacturer = Object.keys(manufacturerCounts).reduce((a, b) => 
                manufacturerCounts[a] > manufacturerCounts[b] ? a : b, null
            );
            
            if (dominantManufacturer && categoryProducts.length > 0) {
                const manufacturer = manufacturers.find(m => m.name === dominantManufacturer);
                if (manufacturer) {
                    companySection.innerHTML = `
                        <article class="company-card" style="cursor: pointer;">
                            <div class="company-content">
                                <img src="${manufacturer.logoPath}" alt="${manufacturer.name} Logo" class="company-logo">
                                <h1 class="company-title">${manufacturer.name}</h1>
                                <h2 class="company-subtitle">Premium ${currentCategory}</h2>
                                <p class="company-description">Quality products from ${manufacturer.name}.</p>
                            </div>
                        </article>
                    `;
                    
                    // Add click handler for manufacturer card
                    const manufacturerCard = companySection.querySelector('.company-card');
                    if (manufacturerCard) {
                        manufacturerCard.addEventListener('click', function() {
                            selectManufacturer(dominantManufacturer);
                        });
                    }
                }
            } else {
                // Clear company section if no dominant manufacturer
                companySection.innerHTML = '';
            }
        }
    }
    
    // Home page: show About Us content and partner logos
    if (currentCategory === 'Home' && !currentManufacturer) {
        const aboutUsSection = document.createElement('div');
        aboutUsSection.className = 'about-us-section';
        
        const logos = [
            { name: 'CBS', filename: 'cbslogo.png', url: 'https://www.cbscambodia.com.kh/' },
            { name: 'CTN', filename: 'CTN-New-Logo-677x329.png', url: 'https://ctn.com.kh/' },
            { name: 'MYTV', filename: 'MYTVLOGO.png', url: 'https://mytv.com.kh/' },
            { name: 'CNC', filename: 'CNCLOGO.jpg', url: 'https://cnc.com.kh/' },
            { name: 'CNC Sports', filename: 'CNCSPORTSLOGO.png', url: 'https://cbssport.com.kh/' }
        ];
        
        aboutUsSection.innerHTML = `
             <div class="about-us-content">
                 <div class="logos-container">
                     ${logos.map(logo => `
                         <div class="logo-card">
                             <a href="${logo.url}" target="_blank" rel="noopener noreferrer">
                                 <img src="CBSLOGO/${logo.filename}" alt="${logo.name}" class="logo-image">
                             </a>
                         </div>
                     `).join('')}
                 </div>
             </div>
         `;
        productsContainer.appendChild(aboutUsSection);
        return;
    }
    
    // Show manufacturers in middle section for all categories (unless a specific manufacturer is selected)
    if (!currentManufacturer) {
        const companySection = document.querySelector('.company-section');
        if (companySection) {
            // Unique manufacturer list for current category (alphabetical)
            const uniqueManufacturers = [...new Set(sampleProducts
                .filter(product => product.manufacturer && (currentCategory === 'All Products' || product.category === currentCategory))
                .map(product => product.manufacturer))]
                .sort();
            
            companySection.innerHTML = `
                <div class="manufacturers-section">
                    <div class="manufacturers-content">
                        <h3>Manufacturers</h3>
                        <div class="manufacturers-grid">
                            ${uniqueManufacturers.map(manufacturer => {
                                const manufacturerData = manufacturers.find(m => m.name === manufacturer);
                                return `
                                    <div class="manufacturer-card" onclick="selectManufacturer('${manufacturer}')">
                                        ${manufacturerData && manufacturerData.logoPath ? 
                                            `<img src="${manufacturerData.logoPath}" alt="${manufacturer}" class="manufacturer-logo">
                                            <div class="manufacturer-line"></div>` : 
                                            `<div class="manufacturer-name">${manufacturer}</div>`
                                        }
                                        <div class="manufacturer-info">
                                            <h3 class="manufacturer-title">${manufacturerData && manufacturerData.businessName ? manufacturerData.businessName : manufacturer}</h3>
                                            ${manufacturerData && manufacturerData.businessAddress ? 
                                                `<p class="manufacturer-address"><i class="fa fa-home" aria-hidden="true"></i> <strong>Address:</strong> ${manufacturerData.businessAddress}</p>` : ''
                                            }
                                            ${manufacturerData && manufacturerData.businessContact ? 
                                                `<p class="manufacturer-contact"><i class="fa fa-phone" aria-hidden="true"></i> <strong>Contact:</strong> ${manufacturerData.businessContact}</p>` : ''
                                            }
                                            ${manufacturerData && manufacturerData.businessSocialNetwork ? 
                                                `<p class="manufacturer-social"><i class="fa-brands fa-facebook" aria-hidden="true"></i> <strong>Social Network:</strong> ${manufacturerData.businessSocialNetwork}</p>` : ''
                                            }
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        // For All Products, continue to show all products; other categories show filtered products
        // No early return here - let it fall through to show products
    }
    
    const filteredProducts = getFilteredProducts();
    
    // Removed clear manufacturer filter button as requested
    
    // No matching products state
    if (filteredProducts.length === 0) {
        productsContainer.innerHTML = `
            <div class="no-products">
                <p>No products found matching your criteria.</p>
            </div>
        `;
        return;
    }
    
    // Render each product as a card
    filteredProducts.forEach(product => {
        const productCard = createProductCard(product);
        productsContainer.appendChild(productCard);
    });
}

// Create product card element
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    // Use provided image or a minimal placeholder
    const imagePath = product.imagePath ? product.imagePath : '';
    const imageContent = imagePath ? 
        `<img src="${imagePath}" alt="${product.name}" class="product-img">` : 
        `<span>Product Image</span>`;
    
    card.innerHTML = `
        <div class="product-header">
            <div class="product-image">
                ${imageContent}
            </div>
            <h3 class="product-name">${product.name}</h3>
            <p class="product-description">${product.description}</p>
            <span class="product-category">${product.category}</span>
        </div>
    `;
    
    return card;
}

// Cart functionality removed

// =========================================================
// Badges
// =========================================================
// Update all category badges with real-time product counts
function updateAllBadges() {
    // Update home badge with total product count (intentionally disabled)
    // homeBadge.textContent = sampleProducts.length;
    
    // Count products for each category
    const categoryCounts = {};
    
    // Initialize categories with 0
    categories.forEach(category => {
        categoryCounts[category] = 0;
    });
    
    // Count products per category
    sampleProducts.forEach(product => {
        if (categoryCounts.hasOwnProperty(product.category)) {
            categoryCounts[product.category]++;
        }
    });
    
    // Update badge text for each category button
    categories.forEach(category => {
        const categoryButton = document.querySelector(`[data-category="${category}"]`);
        if (categoryButton) {
            const badge = categoryButton.querySelector('.badge');
            if (badge) {
                badge.textContent = categoryCounts[category];
            }
        }
    });
}

// Keep the old function name for backward compatibility
function updateHomeBadge() {
    // Removed home badge counter - no longer updating badge content
}

// =========================================================
// UX Enhancements
// =========================================================
// Smooth scrolling for product container
function smoothScrollToTop() {
    productsContainer.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add smooth scroll when changing categories
const originalSelectCategory = selectCategory;
selectCategory = function(category) {
    originalSelectCategory(category);
    smoothScrollToTop();
};

// Keyboard shortcuts: Escape clears search, '/' focuses it
document.addEventListener('keydown', function(e) {
    // Escape key clears search
    if (e.key === 'Escape') {
        searchInput.value = '';
        searchTerm = '';
        renderProducts();
        searchInput.blur();
    }
    
    // '/' focuses search unless cursor is already in the input
    if (e.key === '/' && e.target !== searchInput) {
        e.preventDefault();
        searchInput.focus();
    }
    
    // Close mobile menu with Escape key
    if (e.key === 'Escape') {
        closeMobileMenu();
    }
});

// Provide a small hint for users
searchInput.setAttribute('title', 'Press / to focus search, Escape to clear');

// ---------------------------
// Mobile Hamburger Menu Functionality
// ---------------------------
function initializeMobileMenu() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');
    
    if (!hamburgerBtn || !sidebar || !mobileOverlay) {
        return; // Elements not found, skip mobile menu initialization
    }
    
    // Toggle mobile menu
    hamburgerBtn.addEventListener('click', function() {
        toggleMobileMenu();
    });
    
    // Close menu when clicking overlay
    mobileOverlay.addEventListener('click', function() {
        closeMobileMenu();
    });
    
    // Close menu when clicking on navigation items (mobile only)
    const navButtons = sidebar.querySelectorAll('.nav-btn');
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Only close on mobile (when hamburger is visible)
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
        });
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeMobileMenu();
        }
    });
}

function toggleMobileMenu() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');
    
    const isActive = sidebar.classList.contains('active');
    
    if (isActive) {
        closeMobileMenu();
    } else {
        openMobileMenu();
    }
}

function openMobileMenu() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');
    
    hamburgerBtn.classList.add('active');
    sidebar.classList.add('active');
    mobileOverlay.classList.add('active');
    
    // Prevent body scroll when menu is open
    document.body.style.overflow = 'hidden';
}

function closeMobileMenu() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');
    
    if (hamburgerBtn) hamburgerBtn.classList.remove('active');
    if (sidebar) sidebar.classList.remove('active');
    if (mobileOverlay) mobileOverlay.classList.remove('active');
    
    // Restore body scroll
    document.body.style.overflow = '';
}

// Initialize mobile menu when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeMobileMenu();
});

