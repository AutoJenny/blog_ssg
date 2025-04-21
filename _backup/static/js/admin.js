document.addEventListener('DOMContentLoaded', () => {
    // Theme handling
    const themeToggle = document.getElementById('themeToggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Initialize theme
    const savedTheme = localStorage.getItem('theme');
    const initialTheme = savedTheme || (prefersDark.matches ? 'dark' : 'light');
    document.body.setAttribute('data-theme', initialTheme);
    
    if (themeToggle) {
        themeToggle.setAttribute('aria-pressed', initialTheme === 'dark');
        updateThemeIcon(initialTheme === 'dark');
        
        themeToggle.addEventListener('click', () => {
            const isDark = document.body.getAttribute('data-theme') === 'dark';
            const newTheme = isDark ? 'light' : 'dark';
            
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeToggle.setAttribute('aria-pressed', !isDark);
            updateThemeIcon(!isDark);
        });
    }

    // Deleted posts visibility
    const deletedToggle = document.getElementById('deletedToggle');
    if (deletedToggle) {
        const showDeleted = localStorage.getItem('showDeleted') === 'true';
        document.body.classList.toggle('show-deleted', showDeleted);
        deletedToggle.setAttribute('aria-pressed', showDeleted);
        updateDeletedIcon(showDeleted);
        
        deletedToggle.addEventListener('click', () => {
            const isShowing = document.body.classList.contains('show-deleted');
            const newState = !isShowing;
            
            document.body.classList.toggle('show-deleted', newState);
            localStorage.setItem('showDeleted', newState);
            deletedToggle.setAttribute('aria-pressed', newState);
            updateDeletedIcon(newState);
        });
    }

    // Draft posts visibility
    const draftToggle = document.getElementById('draftToggle');
    if (draftToggle) {
        const showDrafts = localStorage.getItem('showDrafts') === 'true';
        document.body.setAttribute('data-show-drafts', showDrafts);
        draftToggle.setAttribute('aria-pressed', showDrafts);
        updateDraftIcon(showDrafts);
        
        draftToggle.addEventListener('click', () => {
            const isShowing = document.body.getAttribute('data-show-drafts') === 'true';
            const newState = !isShowing;
            
            document.body.setAttribute('data-show-drafts', newState);
            localStorage.setItem('showDrafts', newState);
            draftToggle.setAttribute('aria-pressed', newState);
            updateDraftIcon(newState);
        });
    }

    // System theme changes
    prefersDark.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.body.setAttribute('data-theme', newTheme);
            if (themeToggle) {
                themeToggle.setAttribute('aria-pressed', e.matches);
                updateThemeIcon(e.matches);
            }
        }
    });

    // Icon update functions
    function updateThemeIcon(isDark) {
        const icon = themeToggle.querySelector('.material-icons');
        if (icon) {
            icon.textContent = isDark ? 'dark_mode' : 'light_mode';
        }
    }

    function updateDeletedIcon(isShowing) {
        const icon = deletedToggle.querySelector('.material-icons');
        const text = deletedToggle.querySelector('span:not(.material-icons)');
        if (icon) {
            icon.textContent = isShowing ? 'visibility_off' : 'visibility';
        }
        if (text) {
            text.textContent = isShowing ? 'Hide Deleted' : 'Show Deleted';
        }
    }

    function updateDraftIcon(isShowing) {
        const icon = draftToggle.querySelector('.material-icons');
        if (icon) {
            icon.textContent = isShowing ? 'draft_orders' : 'article';
        }
    }

    // Help Trigger Functionality
    document.querySelectorAll('.help-trigger').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const helpText = trigger.nextElementSibling;
            helpText.classList.toggle('visible');
        });
    });

    // Traffic Light Status Updates
    document.querySelectorAll('.traffic-light').forEach(light => {
        const status = light.dataset.status;
        if (status) {
            light.classList.add(status);
        }
    });

    // Workflow Stage Collapsible
    document.querySelectorAll('.workflow-stage summary').forEach(summary => {
        summary.addEventListener('click', (e) => {
            const details = summary.parentElement;
            const isOpen = details.hasAttribute('open');
            
            // Store the state
            const stageName = details.dataset.stage;
            if (stageName) {
                localStorage.setItem(`workflow-${stageName}`, !isOpen);
            }
        });

        // Restore state on load
        const details = summary.parentElement;
        const stageName = details.dataset.stage;
        if (stageName) {
            const isOpen = localStorage.getItem(`workflow-${stageName}`) === 'true';
            if (isOpen) {
                details.setAttribute('open', '');
            }
        }
    });

    // Restore Post Functionality
    document.querySelectorAll('.restore-button').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const postId = button.dataset.postId;
            
            try {
                const response = await fetch(`/admin/restore/${postId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const post = button.closest('.post-card');
                    post.classList.remove('post-deleted');
                    button.remove();
                    const deletedIndicator = post.querySelector('.deleted-indicator');
                    if (deletedIndicator) {
                        deletedIndicator.remove();
                    }
                } else {
                    console.error('Failed to restore post');
                }
            } catch (error) {
                console.error('Error restoring post:', error);
            }
        });
    });
}); 