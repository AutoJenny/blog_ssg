document.addEventListener('DOMContentLoaded', () => {
    const showDeletedToggle = document.getElementById('showDeletedToggle');
    const showDraftsToggle = document.getElementById('showDraftsToggle');
    const helpToggle = document.getElementById('helpToggle');

    // Load saved preferences from localStorage
    const loadPreferences = () => {
        const showDeleted = localStorage.getItem('showDeleted') === 'true';
        const showDrafts = localStorage.getItem('showDrafts') === 'true';
        const showHelp = localStorage.getItem('showHelp') === 'true';

        document.body.classList.toggle('show-deleted', showDeleted);
        document.body.classList.toggle('show-drafts', showDrafts);
        document.body.classList.toggle('show-help', showHelp);

        showDeletedToggle.setAttribute('aria-pressed', showDeleted);
        showDraftsToggle.setAttribute('aria-pressed', showDrafts);
        helpToggle.setAttribute('aria-pressed', showHelp);
    };

    // Toggle handlers
    showDeletedToggle.addEventListener('click', () => {
        const isPressed = showDeletedToggle.getAttribute('aria-pressed') === 'true';
        showDeletedToggle.setAttribute('aria-pressed', !isPressed);
        document.body.classList.toggle('show-deleted');
        localStorage.setItem('showDeleted', !isPressed);
    });

    showDraftsToggle.addEventListener('click', () => {
        const isPressed = showDraftsToggle.getAttribute('aria-pressed') === 'true';
        showDraftsToggle.setAttribute('aria-pressed', !isPressed);
        document.body.classList.toggle('show-drafts');
        localStorage.setItem('showDrafts', !isPressed);
    });

    helpToggle.addEventListener('click', () => {
        const isPressed = helpToggle.getAttribute('aria-pressed') === 'true';
        helpToggle.setAttribute('aria-pressed', !isPressed);
        document.body.classList.toggle('show-help');
        localStorage.setItem('showHelp', !isPressed);
    });

    // Initialize preferences
    loadPreferences();

    // Toggle visibility of deleted posts
    const deletedToggle = document.getElementById('showDeletedToggle');
    if (deletedToggle) {
        deletedToggle.addEventListener('click', () => {
            const isShowing = deletedToggle.getAttribute('aria-pressed') === 'true';
            deletedToggle.setAttribute('aria-pressed', !isShowing);
            document.body.classList.toggle('show-deleted', !isShowing);
            
            // Update icon and label
            const icon = deletedToggle.querySelector('.icon');
            icon.textContent = !isShowing ? '🗑️' : '📄';
        });
    }

    // Toggle visibility of draft posts
    const draftToggle = document.getElementById('showDraftsToggle');
    if (draftToggle) {
        draftToggle.addEventListener('click', () => {
            const isShowing = draftToggle.getAttribute('aria-pressed') === 'true';
            draftToggle.setAttribute('aria-pressed', !isShowing);
            document.body.classList.toggle('show-drafts', !isShowing);
            
            // Update icon and label
            const icon = draftToggle.querySelector('.icon');
            icon.textContent = !isShowing ? '📝' : '📄';
        });
    }

    // Help system
    const helpTriggers = document.querySelectorAll('.help-trigger');
    
    if (helpToggle) {
        helpToggle.addEventListener('click', () => {
            const isEnabled = helpToggle.getAttribute('aria-pressed') === 'true';
            helpToggle.setAttribute('aria-pressed', !isEnabled);
            document.body.classList.toggle('help-enabled', !isEnabled);
            
            // Update icon and label
            const icon = helpToggle.querySelector('.icon');
            icon.textContent = !isEnabled ? '❓' : '❌';
            
            // Toggle help trigger visibility
            helpTriggers.forEach(trigger => {
                trigger.style.display = !isEnabled ? 'inline-block' : 'none';
            });
        });
    }

    // Initialize help triggers as hidden
    helpTriggers.forEach(trigger => {
        trigger.style.display = 'none';
        
        // Add hover/focus event listeners for help text
        const helpText = trigger.getAttribute('data-help');
        if (helpText) {
            const tooltip = document.createElement('div');
            tooltip.className = 'help-tooltip';
            tooltip.textContent = helpText;
            trigger.appendChild(tooltip);
            
            ['mouseenter', 'focus'].forEach(event => {
                trigger.addEventListener(event, () => {
                    tooltip.style.display = 'block';
                });
            });
            
            ['mouseleave', 'blur'].forEach(event => {
                trigger.addEventListener(event, () => {
                    tooltip.style.display = 'none';
                });
            });
        }
    });
}); 