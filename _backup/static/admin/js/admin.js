// Admin functionality
document.addEventListener('DOMContentLoaded', () => {
    // Toggle filters
    const showDeletedToggle = document.getElementById('show-deleted');
    const showDraftsToggle = document.getElementById('show-drafts');
    
    const toggleFilter = (button, filterClass) => {
        const posts = document.querySelectorAll('.post-item');
        button.classList.toggle('active');
        const isActive = button.classList.contains('active');
        
        posts.forEach(post => {
            if (post.classList.contains(filterClass)) {
                post.style.display = isActive ? 'block' : 'none';
            }
        });
        
        // Save filter state
        localStorage.setItem(`filter_${filterClass}`, isActive);
    };
    
    // Initialize filters from saved state
    const initializeFilter = (button, filterClass) => {
        if (button) {
            const isActive = localStorage.getItem(`filter_${filterClass}`) === 'true';
            if (isActive) {
                button.classList.add('active');
                toggleFilter(button, filterClass);
            }
            
            button.addEventListener('click', () => toggleFilter(button, filterClass));
        }
    };
    
    initializeFilter(showDeletedToggle, 'deleted');
    initializeFilter(showDraftsToggle, 'draft');
    
    // Handle post actions (delete, restore, publish, unpublish)
    document.addEventListener('click', (e) => {
        if (e.target.matches('[data-action]')) {
            e.preventDefault();
            const action = e.target.dataset.action;
            const postId = e.target.dataset.postId;
            const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
            
            fetch(`/admin/posts/${postId}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI based on action
                    const postElement = document.querySelector(`[data-post-id="${postId}"]`);
                    switch (action) {
                        case 'delete':
                            postElement.classList.add('deleted');
                            break;
                        case 'restore':
                            postElement.classList.remove('deleted');
                            break;
                        case 'publish':
                            postElement.classList.remove('draft');
                            break;
                        case 'unpublish':
                            postElement.classList.add('draft');
                            break;
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });
}); 