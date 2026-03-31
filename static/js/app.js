// Main Application JS

document.addEventListener('DOMContentLoaded', () => {
    // Initialize things if needed
});

// Utility functions
async function apiGet(endpoint) {
    const response = await fetch(endpoint);
    return await response.json();
}

async function apiPost(endpoint, data) {
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}

async function apiPut(endpoint, data) {
    const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}
