document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Initialize theme from localStorage or system preference
    const savedTheme = localStorage.getItem('theme');
    const initialTheme = savedTheme || (prefersDark.matches ? 'dark' : 'light');
    document.body.className = `${initialTheme}-theme`;

    // Update theme toggle button
    const updateThemeToggle = (isDark) => {
        themeToggle.setAttribute('aria-pressed', isDark);
        themeToggle.querySelector('.icon').textContent = isDark ? '🌞' : '🌓';
    };

    // Initialize button state
    updateThemeToggle(initialTheme === 'dark');

    // Handle theme toggle click
    themeToggle.addEventListener('click', () => {
        const isDark = document.body.className === 'light-theme';
        const newTheme = isDark ? 'dark' : 'light';
        document.body.className = `${newTheme}-theme`;
        localStorage.setItem('theme', newTheme);
        updateThemeToggle(isDark);
    });

    // Handle system theme changes
    prefersDark.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.body.className = `${newTheme}-theme`;
            updateThemeToggle(e.matches);
        }
    });
}); 