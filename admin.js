// ======================= Admin Panel JavaScript ======================= //

// API Configuration
// Use localhost for development, with fallback detection
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://127.0.0.1:5001/api' 
    : '/api';

// DOM Elements
const adminNavButtons = document.querySelectorAll('.admin-nav-btn');
const adminSections = document.querySelectorAll('.admin-section');
const addProductForm = document.getElementById('addProductForm');
const addManufacturerForm = document.getElementById('addManufacturerForm');
const addCategoryForm = document.getElementById('addCategoryForm');
const productManufacturerSelect = document.getElementById('productManufacturer');
const statusMessage = document.getElementById('statusMessage');

// Initialize Admin Panel
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminPanel();
});

// ======================= Initialization ======================= //

async function initializeAdminPanel() {
    try {
        // Setup navigation
        setupNavigation();
        
        // Load manufacturers for product form
        await loadManufacturers();
        
        // Load categories for product form
        await loadCategoriesForProductForm();
        
        // Setup form handlers
        setupFormHandlers();
        
        // Load initial stats
        await loadDatabaseStats();
        
        showStatusMessage('Admin panel loaded successfully', 'success');
    } catch (error) {
        console.error('Error initializing admin panel:', error);
        showStatusMessage('Error loading admin panel', 'error');
    }
}

// ======================= Navigation ======================= //

function setupNavigation() {
    adminNavButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            if (sectionId) {
                switchSection(sectionId);
                updateActiveNavButton(this);
            }
        });
    });
}

function switchSection(sectionId) {
    // Hide all sections
    adminSections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Show target section
    const targetSection = document.getElementById(`${sectionId}-section`);
    if (targetSection) {
        targetSection.classList.add('active');
        
        // Load section-specific data
        if (sectionId === 'view-stats') {
            loadDatabaseStats();
        } else if (sectionId === 'manage-items') {
            loadManageItemsData();
        } else if (sectionId === 'manage-categories') {
            loadCategoriesForManagement();
        }
    }
}

function updateActiveNavButton(activeButton) {
    adminNavButtons.forEach(button => {
        button.classList.remove('active');
    });
    activeButton.classList.add('active');
}

// ======================= API Functions ======================= //

async function fetchFromAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// ======================= Data Loading ======================= //

async function loadManufacturers() {
    try {
        const manufacturers = await fetchFromAPI('/manufacturers');
        
        if (productManufacturerSelect && manufacturers) {
            // Clear existing options except the first one
            productManufacturerSelect.innerHTML = '<option value="">Select a manufacturer</option>';
            
            // Add manufacturer options
            manufacturers.forEach(manufacturer => {
                const option = document.createElement('option');
                option.value = manufacturer.id;
                option.textContent = manufacturer.name;
                productManufacturerSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading manufacturers:', error);
        showStatusMessage('Error loading manufacturers', 'error');
    }
}

async function loadCategoriesForProductForm() {
    try {
        const categories = await fetchFromAPI('/categories');
        const productCategorySelect = document.getElementById('productCategory');
        
        if (productCategorySelect && categories) {
            // Clear existing options except the first one
            productCategorySelect.innerHTML = '<option value="">Select a category</option>';
            
            // Add category options
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.name;
                option.textContent = category.name;
                productCategorySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading categories for product form:', error);
        showStatusMessage('Error loading categories', 'error');
    }
}

async function loadDatabaseStats() {
    try {
        // Load basic stats
        const [products, manufacturers, categories, categoryStats] = await Promise.all([
            fetchFromAPI('/products'),
            fetchFromAPI('/manufacturers'),
            fetchFromAPI('/categories'),
            fetchFromAPI('/stats')
        ]);
        
        // Update stat numbers
        document.getElementById('totalProducts').textContent = products.length;
        document.getElementById('totalManufacturers').textContent = manufacturers.length;
        document.getElementById('totalCategories').textContent = categories.length;
        
        // Update category breakdown
        updateCategoryBreakdown(categoryStats.category_stats || []);
        
    } catch (error) {
        console.error('Error loading database stats:', error);
        showStatusMessage('Error loading database statistics', 'error');
    }
}

function updateCategoryBreakdown(categoryStats) {
    const breakdownContainer = document.getElementById('categoryBreakdown');
    
    if (!categoryStats || categoryStats.length === 0) {
        breakdownContainer.innerHTML = '<p class="text-muted">No category data available</p>';
        return;
    }
    
    breakdownContainer.innerHTML = categoryStats.map(stat => `
        <div class="breakdown-item">
            <span class="breakdown-category">${stat.category}</span>
            <span class="breakdown-count">${stat.count}</span>
        </div>
    `).join('');
}

// ======================= Form Handlers ======================= //

function setupFormHandlers() {
    // Product form handler
    if (addProductForm) {
        addProductForm.addEventListener('submit', handleAddProduct);
    }
    
    // Manufacturer form handler
    if (addManufacturerForm) {
        addManufacturerForm.addEventListener('submit', handleAddManufacturer);
    }
    
    // Category form handler
    if (addCategoryForm) {
        addCategoryForm.addEventListener('submit', handleAddCategory);
    }
}

async function handleAddProduct(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const imageFile = formData.get('image');
    
    // Validate required fields
    if (!formData.get('name') || !formData.get('category') || !formData.get('manufacturer_id')) {
        showStatusMessage('Please fill in all required fields.', 'error');
        return;
    }
    
    try {
        showStatusMessage('Adding product...', 'info');
        
        // Handle image upload if provided
        let imagePath = '';
        if (imageFile && imageFile.size > 0) {
            imagePath = await uploadProductImage(imageFile, formData.get('name'));
        }
        
        const productData = {
            name: formData.get('name'),
            category: formData.get('category'),
            manufacturer_id: parseInt(formData.get('manufacturer_id')),
            description: formData.get('description') || '',
            image_path: imagePath
        };
        
        const result = await fetchFromAPI('/products', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
        
        showStatusMessage(`Product "${productData.name}" added successfully!`, 'success');
        
        // Reset form
        event.target.reset();
        
        // Refresh stats if on stats page
        const statsSection = document.getElementById('view-stats-section');
        if (statsSection && statsSection.classList.contains('active')) {
            await loadDatabaseStats();
        }
        
        // Refresh manage items if on manage items page
        const manageItemsSection = document.getElementById('manage-items-section');
        if (manageItemsSection && manageItemsSection.classList.contains('active')) {
            await loadManageItemsData();
        }
        
    } catch (error) {
        console.error('Error adding product:', error);
        showStatusMessage('Error adding product. Please try again.', 'error');
    }
}

async function handleAddManufacturer(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const logoFile = formData.get('logo');
    
    // Validate required fields
    if (!formData.get('name')) {
        showStatusMessage('Please enter a manufacturer name.', 'error');
        return;
    }
    
    try {
        showStatusMessage('Adding manufacturer...', 'info');
        
        // Handle logo upload if provided
        let logoPath = '';
        if (logoFile && logoFile.size > 0) {
            logoPath = await uploadManufacturerLogo(logoFile, formData.get('name'));
        }
        
        const manufacturerData = {
            name: formData.get('name'),
            description: formData.get('description') || '',
            logo_path: logoPath,
            business_name: formData.get('business_name') || '',
            business_address: formData.get('business_address') || '',
            business_contact: formData.get('business_contact') || '',
            business_social_network: formData.get('business_social_network') || ''
        };
        
        const result = await fetchFromAPI('/manufacturers', {
            method: 'POST',
            body: JSON.stringify(manufacturerData)
        });
        
        showStatusMessage(`Manufacturer "${manufacturerData.name}" added successfully!`, 'success');
        
        // Reset form
        event.target.reset();
        
        // Reload manufacturers for product form
        await loadManufacturers();
        
        // Refresh stats if on stats page
        const statsSection = document.getElementById('view-stats-section');
        if (statsSection && statsSection.classList.contains('active')) {
            await loadDatabaseStats();
        }
        
        // Refresh manage items if on manage items page
        const manageItemsSection = document.getElementById('manage-items-section');
        if (manageItemsSection && manageItemsSection.classList.contains('active')) {
            await loadManageItemsData();
        }
        
    } catch (error) {
        console.error('Error adding manufacturer:', error);
        showStatusMessage('Error adding manufacturer. Please try again.', 'error');
    }
}

// ======================= File Upload Functions ======================= //

async function uploadProductImage(imageFile, productName) {
    try {
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('product_name', productName);
        
        const response = await fetch(`${API_BASE_URL}/upload/product-image`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
        }
        
        const result = await response.json();
        return result.file_path;
    } catch (error) {
        console.error('Error uploading product image:', error);
        throw new Error('Failed to upload product image: ' + error.message);
    }
}

async function uploadManufacturerLogo(logoFile, manufacturerName) {
    try {
        const formData = new FormData();
        formData.append('logo', logoFile);
        formData.append('manufacturer_name', manufacturerName);
        
        const response = await fetch(`${API_BASE_URL}/upload/manufacturer-logo`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
        }
        
        const result = await response.json();
        return result.file_path;
    } catch (error) {
        console.error('Error uploading manufacturer logo:', error);
        throw new Error('Failed to upload manufacturer logo: ' + error.message);
    }
}

// File upload functions now use the server endpoints directly
// No need for local file simulation

// ======================= Status Messages ======================= //

function showStatusMessage(message, type = 'info') {
    if (!statusMessage) return;
    
    // Clear existing classes and content
    statusMessage.className = 'status-message';
    statusMessage.textContent = message;
    
    // Add type class
    statusMessage.classList.add(type);
    
    // Show message
    statusMessage.classList.remove('hidden');
    statusMessage.classList.add('show');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideStatusMessage();
    }, 5000);
}

function hideStatusMessage() {
    if (!statusMessage) return;
    
    statusMessage.classList.remove('show');
    
    // Hide completely after transition
    setTimeout(() => {
        statusMessage.classList.add('hidden');
    }, 300);
}

// ======================= Utility Functions ======================= //

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Validate form data
function validateProductData(data) {
    const errors = [];
    
    if (!data.name || data.name.trim().length === 0) {
        errors.push('Product name is required');
    }
    
    if (!data.category || data.category.trim().length === 0) {
        errors.push('Category is required');
    }
    
    if (!data.manufacturer_id || isNaN(data.manufacturer_id)) {
        errors.push('Valid manufacturer is required');
    }
    
    return errors;
}

function validateManufacturerData(data) {
    const errors = [];
    
    if (!data.name || data.name.trim().length === 0) {
        errors.push('Manufacturer name is required');
    }
    
    return errors;
}

// ======================= Error Handling ======================= //

// Global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showStatusMessage('An unexpected error occurred', 'error');
});

// Global error handler for JavaScript errors
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    showStatusMessage('An unexpected error occurred', 'error');
});

// ======================= Manage Items Functions ======================= //

// Load and display products for management
async function loadProductsForManagement() {
    const productsList = document.getElementById('productsList');
    
    try {
        productsList.innerHTML = '<div class="loading-message">Loading products...</div>';
        
        const products = await fetchFromAPI('/products');
        
        if (products.length === 0) {
            productsList.innerHTML = '<div class="empty-message">No products found</div>';
            return;
        }
        
        productsList.innerHTML = products.map(product => `
            <div class="item-card" data-id="${product.id}">
                <div class="item-info">
                    <div class="item-name">${product.name}</div>
                    <div class="item-details">
                        Category: ${product.category} | Manufacturer: ${product.manufacturer_name}
                    </div>
                </div>
                <div class="item-actions">
                    <button class="edit-btn" onclick="editProduct(${product.id})" 
                            title="Edit ${product.name}">
                        <i class="fas fa-edit" aria-hidden="true"></i>
                        Edit
                    </button>
                    <button class="delete-btn" onclick="deleteProduct(${product.id}, '${product.name.replace(/'/g, "\\'")}')" 
                            title="Delete ${product.name}">
                        <i class="fas fa-trash" aria-hidden="true"></i>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading products:', error);
        productsList.innerHTML = '<div class="empty-message">Error loading products</div>';
    }
}

// Load and display manufacturers for management
async function loadManufacturersForManagement() {
    const manufacturersList = document.getElementById('manufacturersList');
    
    try {
        manufacturersList.innerHTML = '<div class="loading-message">Loading manufacturers...</div>';
        
        const manufacturers = await fetchFromAPI('/manufacturers');
        
        if (manufacturers.length === 0) {
            manufacturersList.innerHTML = '<div class="empty-message">No manufacturers found</div>';
            return;
        }
        
        manufacturersList.innerHTML = manufacturers.map(manufacturer => `
            <div class="item-card" data-id="${manufacturer.id}">
                <div class="item-info">
                    <div class="item-name">${manufacturer.name}</div>
                    <div class="item-details">
                        ${manufacturer.description || 'No description available'}
                    </div>
                </div>
                <div class="item-actions">
                    <button class="edit-btn" onclick="editManufacturer(${manufacturer.id})" 
                            title="Edit ${manufacturer.name}">
                        <i class="fas fa-edit" aria-hidden="true"></i>
                        Edit
                    </button>
                    <button class="delete-btn" onclick="deleteManufacturer(${manufacturer.id}, '${manufacturer.name.replace(/'/g, "\\'")}')" 
                            title="Delete ${manufacturer.name}">
                        <i class="fas fa-trash" aria-hidden="true"></i>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading manufacturers:', error);
        manufacturersList.innerHTML = '<div class="empty-message">Error loading manufacturers</div>';
    }
}

// Delete a product
async function deleteProduct(productId, productName) {
    if (!confirm(`Are you sure you want to delete "${productName}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetchFromAPI(`/products/${productId}`, {
            method: 'DELETE'
        });
        
        showStatusMessage(`Product "${productName}" deleted successfully`, 'success');
        
        // Reload the products list
        await loadProductsForManagement();
        
        // Refresh stats if on stats page
        if (document.getElementById('view-stats-section').classList.contains('active')) {
            await loadDatabaseStats();
        }
        
    } catch (error) {
        console.error('Error deleting product:', error);
        showStatusMessage(`Failed to delete product "${productName}"`, 'error');
    }
}

// Delete a manufacturer
async function deleteManufacturer(manufacturerId, manufacturerName) {
    if (!confirm(`Are you sure you want to delete "${manufacturerName}"? This will also affect any products from this manufacturer. This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetchFromAPI(`/manufacturers/${manufacturerId}`, {
            method: 'DELETE'
        });
        
        showStatusMessage(`Manufacturer "${manufacturerName}" deleted successfully`, 'success');
        
        // Reload both lists
        await loadManufacturersForManagement();
        await loadProductsForManagement();
        
        // Refresh manufacturer dropdown in add product form
        await loadManufacturers();
        
        // Refresh stats if on stats page
        if (document.getElementById('view-stats-section').classList.contains('active')) {
            await loadDatabaseStats();
        }
        
    } catch (error) {
        console.error('Error deleting manufacturer:', error);
        showStatusMessage(`Failed to delete manufacturer "${manufacturerName}"`, 'error');
    }
}

// Load manage items data when section is activated
function loadManageItemsData() {
    loadProductsForManagement();
    loadManufacturersForManagement();
}

// ======================= Category Management Functions ======================= //

async function loadCategoriesForManagement() {
    try {
        const categories = await fetchFromAPI('/categories');
        const categoriesList = document.getElementById('categoriesList');
        
        if (!categoriesList) {
            console.error('Categories list container not found');
            return;
        }
        
        if (!categories || categories.length === 0) {
            categoriesList.innerHTML = '<p class="no-items">No categories found.</p>';
            return;
        }
        
        categoriesList.innerHTML = categories.map(category => `
            <div class="item-card">
                <div class="item-info">
                    <h4 class="item-name">${category.name}</h4>
                    <p class="item-details">ID: ${category.id}</p>
                </div>
                <button class="delete-btn" onclick="deleteCategory(${category.id}, '${category.name.replace(/'/g, "\\'")}')"
                        title="Delete ${category.name}">
                    <i class="fas fa-trash" aria-hidden="true"></i>
                    Delete
                </button>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading categories:', error);
        const categoriesList = document.getElementById('categoriesList');
        if (categoriesList) {
            categoriesList.innerHTML = '<p class="error-message">Error loading categories. Please try again.</p>';
        }
    }
}

async function deleteCategory(categoryId, categoryName) {
    if (!confirm(`Are you sure you want to delete the category "${categoryName}"?\n\nNote: Categories with existing products cannot be deleted.`)) {
        return;
    }
    
    try {
        const result = await fetchFromAPI(`/categories/${categoryId}`, {
            method: 'DELETE'
        });
        
        if (result.error) {
            showStatusMessage(result.error, 'error');
        } else {
            showStatusMessage(result.message || `Category "${categoryName}" deleted successfully`, 'success');
            // Reload the categories list
            loadCategoriesForManagement();
        }
        
    } catch (error) {
        console.error('Error deleting category:', error);
        showStatusMessage('Error deleting category. Please try again.', 'error');
    }
}

async function handleAddCategory(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const categoryData = {
        name: formData.get('categoryName')?.trim()
    };
    
    // Validate category data
    if (!categoryData.name) {
        showStatusMessage('Category name is required', 'error');
        return;
    }
    
    if (categoryData.name.length < 2) {
        showStatusMessage('Category name must be at least 2 characters long', 'error');
        return;
    }
    
    try {
        const result = await fetchFromAPI('/categories', {
            method: 'POST',
            body: JSON.stringify(categoryData)
        });
        
        if (result.error) {
            showStatusMessage(result.error, 'error');
        } else {
            showStatusMessage(result.message || `Category "${categoryData.name}" added successfully`, 'success');
            event.target.reset();
            
            // Reload categories if we're on the manage categories section
            const manageCategoriesSection = document.getElementById('manage-categories-section');
            if (manageCategoriesSection && manageCategoriesSection.classList.contains('active')) {
                loadCategoriesForManagement();
            }
        }
        
    } catch (error) {
        console.error('Error adding category:', error);
        showStatusMessage('Error adding category. Please try again.', 'error');
    }
}

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Clear session storage
        sessionStorage.removeItem('adminLoggedIn');
        sessionStorage.removeItem('adminUsername');
        
        // Redirect to login page
        window.location.href = 'login.html';
    }
}

// ======================= Edit Product Functions ======================= //

async function editProduct(productId) {
    try {
        // Fetch product details
        const product = await fetchFromAPI(`/products/${productId}`);
        
        // Populate the edit form
        document.getElementById('editProductId').value = product.id;
        document.getElementById('editProductName').value = product.name;
        document.getElementById('editProductCategory').value = product.category;
        document.getElementById('editProductManufacturer').value = product.manufacturer_id;
        document.getElementById('editProductDescription').value = product.description || '';
        
        // Show current image if exists
        const imagePreview = document.getElementById('currentImagePreview');
        if (product.image_path) {
            imagePreview.innerHTML = `
                <p>Current Image:</p>
                <img src="${product.image_path}" alt="${product.name}" />
            `;
        } else {
            imagePreview.innerHTML = '<p>No current image</p>';
        }
        
        // Load categories and manufacturers for the edit form
        await loadCategoriesForEditForm();
        await loadManufacturersForEditForm();
        
        // Set the selected values after loading options
        document.getElementById('editProductCategory').value = product.category;
        document.getElementById('editProductManufacturer').value = product.manufacturer_id;
        
        // Show the modal
        document.getElementById('editProductModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading product for edit:', error);
        showStatusMessage('Error loading product details', 'error');
    }
}

function closeEditModal() {
    document.getElementById('editProductModal').classList.remove('show');
    document.getElementById('editProductForm').reset();
    document.getElementById('currentImagePreview').innerHTML = '';
}

async function loadCategoriesForEditForm() {
    const categorySelect = document.getElementById('editProductCategory');
    
    try {
        const categories = await fetchFromAPI('/categories');
        
        // Clear existing options except the first one
        categorySelect.innerHTML = '<option value="">Select Category</option>';
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.name;
            option.textContent = category.name;
            categorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categories for edit form:', error);
    }
}

async function loadManufacturersForEditForm() {
    const manufacturerSelect = document.getElementById('editProductManufacturer');
    
    try {
        const manufacturers = await fetchFromAPI('/manufacturers');
        
        // Clear existing options except the first one
        manufacturerSelect.innerHTML = '<option value="">Select Manufacturer</option>';
        
        manufacturers.forEach(manufacturer => {
            const option = document.createElement('option');
            option.value = manufacturer.id;
            option.textContent = manufacturer.name;
            manufacturerSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading manufacturers for edit form:', error);
    }
}

async function handleEditProduct(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const productId = formData.get('id');
    
    try {
        const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
            method: 'PUT',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showStatusMessage(result.message, 'success');
            closeEditModal();
            // Reload the products list to show updated data
            await loadProductsForManagement();
        } else {
            showStatusMessage(result.error || 'Error updating product', 'error');
        }
    } catch (error) {
        console.error('Error updating product:', error);
        showStatusMessage('Error updating product', 'error');
    }
}

// Add event listener for edit form
document.addEventListener('DOMContentLoaded', function() {
    const editProductForm = document.getElementById('editProductForm');
    if (editProductForm) {
        editProductForm.addEventListener('submit', handleEditProduct);
    }
});

// Close modal when clicking outside of it
document.addEventListener('click', function(event) {
    const modal = document.getElementById('editProductModal');
    if (event.target === modal) {
        closeEditModal();
    }
});

// Edit Manufacturer Functions
async function editManufacturer(manufacturerId) {
    try {
        // Fetch manufacturer details
        const manufacturer = await fetchFromAPI(`/manufacturers/${manufacturerId}`);
        
        // Populate the edit form
        document.getElementById('editManufacturerId').value = manufacturer.id;
        document.getElementById('editManufacturerName').value = manufacturer.name;
        document.getElementById('editManufacturerDescription').value = manufacturer.description || '';
        document.getElementById('editManufacturerBusinessName').value = manufacturer.business_name || '';
        document.getElementById('editManufacturerBusinessAddress').value = manufacturer.business_address || '';
        document.getElementById('editManufacturerBusinessContact').value = manufacturer.business_contact || '';
        document.getElementById('editManufacturerBusinessSocial').value = manufacturer.business_social_network || '';
        
        // Show current logo if exists
        const logoPreview = document.getElementById('currentLogoPreview');
        if (manufacturer.logo_path) {
            logoPreview.innerHTML = `
                <p>Current Logo:</p>
                <img src="${manufacturer.logo_path}" alt="${manufacturer.name}" />
            `;
        } else {
            logoPreview.innerHTML = '<p>No current logo</p>';
        }
        
        // Show the modal
        document.getElementById('editManufacturerModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading manufacturer for edit:', error);
        showStatusMessage('Error loading manufacturer details', 'error');
    }
}

function closeEditManufacturerModal() {
    document.getElementById('editManufacturerModal').classList.remove('show');
    document.getElementById('editManufacturerForm').reset();
    document.getElementById('currentLogoPreview').innerHTML = '';
}

async function handleEditManufacturer(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const manufacturerId = formData.get('id');
    
    try {
        showStatusMessage('Updating manufacturer...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/manufacturers/${manufacturerId}`, {
            method: 'PUT',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showStatusMessage(result.message, 'success');
            closeEditManufacturerModal();
            await loadManufacturersForManagement();
        } else {
            showStatusMessage(result.error || 'Failed to update manufacturer', 'error');
        }
    } catch (error) {
        console.error('Error updating manufacturer:', error);
        showStatusMessage('Error updating manufacturer', 'error');
    }
}

// Setup edit manufacturer form handler
document.addEventListener('DOMContentLoaded', function() {
    const editManufacturerForm = document.getElementById('editManufacturerForm');
    if (editManufacturerForm) {
        editManufacturerForm.addEventListener('submit', handleEditManufacturer);
    }
});

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('editManufacturerModal');
    if (event.target === modal) {
        closeEditManufacturerModal();
    }
});

console.log('Admin panel JavaScript loaded successfully');