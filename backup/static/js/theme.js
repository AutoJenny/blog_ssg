document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const icon = themeToggle.querySelector('.material-icons');
    
    // Initialize theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateIcon(savedTheme);
    
    // Toggle theme on button click
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateIcon(newTheme);
    });
    
    function updateIcon(theme) {
        icon.textContent = theme === 'light' ? 'dark_mode' : 'light_mode';
    }
}); 