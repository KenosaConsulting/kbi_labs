// Diagnostic script - paste this in browser console
console.log('=== Portfolio Diagnostic ===');

// Check if table exists
const table1 = document.getElementById('topCompaniesTable');
console.log('Table by ID:', table1);

// Try querySelector
const table2 = document.querySelector('#topCompaniesTable');
console.log('Table by querySelector:', table2);

// Check all elements with that text
const allElements = document.querySelectorAll('*');
let found = false;
allElements.forEach(el => {
    if (el.id === 'topCompaniesTable' || el.innerHTML?.includes('topCompaniesTable')) {
        console.log('Found element:', el);
        found = true;
    }
});

if (!found) {
    console.log('No element with topCompaniesTable found in DOM');
}

// Check if there are any tbody elements
const tbodies = document.querySelectorAll('tbody');
console.log('All tbody elements:', tbodies.length);
tbodies.forEach((tb, i) => {
    console.log(`tbody ${i}:`, tb.id || 'no id', tb);
});
