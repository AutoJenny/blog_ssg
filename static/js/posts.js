document.addEventListener('DOMContentLoaded', function() {
    const authorFilter = document.getElementById('authorFilter');
    const dateFilter = document.getElementById('dateFilter');
    const statusFilter = document.getElementById('statusFilter');
    const searchFilter = document.getElementById('searchFilter');
    const tagsFilter = document.getElementById('tagsFilter');
    const showDeletedToggle = document.getElementById('showDeletedToggle');
    const tableBody = document.querySelector('tbody');
    const rows = Array.from(tableBody.querySelectorAll('tr'));
    
    // Get all unique tags from the posts
    const allTags = new Set();
    rows.forEach(row => {
        const tagElements = row.querySelectorAll('.badge.bg-secondary');
        tagElements.forEach(tag => allTags.add(tag.textContent.trim()));
    });
    
    // Populate tags filter
    const sortedTags = Array.from(allTags).sort();
    sortedTags.forEach(tag => {
        const option = document.createElement('option');
        option.value = tag;
        option.textContent = tag;
        tagsFilter.appendChild(option);
    });
    
    function filterPosts() {
        const authorValue = authorFilter.value.toLowerCase();
        const dateValue = dateFilter.value;
        const statusValue = statusFilter.value;
        const searchValue = searchFilter.value.toLowerCase();
        const selectedTag = tagsFilter.value;
        const showDeleted = showDeletedToggle.checked;
        
        rows.forEach(row => {
            const author = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const date = row.querySelector('td:nth-child(3)').textContent;
            const statusBadge = row.querySelector('td:nth-child(4) .badge');
            const status = statusBadge ? statusBadge.textContent.trim().toLowerCase() : '';
            const title = row.querySelector('h6').textContent.toLowerCase();
            const subtitle = row.querySelector('small.text-muted')?.textContent.toLowerCase() || '';
            const concept = row.querySelector('.mt-1 small')?.textContent.toLowerCase() || '';
            const tags = Array.from(row.querySelectorAll('.badge.bg-secondary')).map(tag => tag.textContent.trim());
            
            const authorMatch = !authorValue || author.includes(authorValue);
            const dateMatch = !dateValue || date.includes(dateValue);
            const statusMatch = !statusValue || status === statusValue;
            const searchMatch = !searchValue || 
                              title.includes(searchValue) || 
                              subtitle.includes(searchValue) || 
                              concept.includes(searchValue);
            const tagMatch = !selectedTag || tags.includes(selectedTag);
            const deletedMatch = showDeleted || status !== 'deleted';
            
            const shouldShow = authorMatch && dateMatch && statusMatch && searchMatch && tagMatch && deletedMatch;
            row.style.display = shouldShow ? '' : 'none';
            
            // Debug logging
            if (status === 'deleted') {
                console.log('Deleted post:', {
                    title,
                    status,
                    showDeleted,
                    deletedMatch,
                    shouldShow
                });
            }
        });
    }
    
    // Add event listeners for filters
    [authorFilter, dateFilter, statusFilter, searchFilter, tagsFilter, showDeletedToggle].forEach(filter => {
        filter.addEventListener('change', filterPosts);
    });
    searchFilter.addEventListener('input', filterPosts);
    
    // Initial filter to hide deleted posts
    filterPosts();
    
    // Handle delete/restore actions
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.delete-post')) {
            const button = e.target.closest('.delete-post');
            const postId = button.dataset.postId;
            
            try {
                const response = await fetch(`/api/posts/${postId}/delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const row = button.closest('tr');
                    row.classList.remove('table-success');
                    row.classList.add('table-danger');
                    const statusBadge = row.querySelector('td:nth-child(4) .badge');
                    statusBadge.classList.remove('bg-success', 'bg-warning');
                    statusBadge.classList.add('bg-danger');
                    statusBadge.textContent = 'Deleted';
                    button.outerHTML = `
                        <button class="btn btn-sm btn-outline-success restore-post" title="Restore" data-post-id="${postId}">
                            <i class="bi bi-arrow-counterclockwise"></i>
                        </button>
                    `;
                    filterPosts(); // Re-apply filters
                }
            } catch (error) {
                console.error('Error deleting post:', error);
            }
        }
        
        if (e.target.closest('.restore-post')) {
            const button = e.target.closest('.restore-post');
            const postId = button.dataset.postId;
            
            try {
                const response = await fetch(`/api/posts/${postId}/restore`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const row = button.closest('tr');
                    row.classList.remove('table-danger');
                    row.classList.add('table-success');
                    const statusBadge = row.querySelector('td:nth-child(4) .badge');
                    statusBadge.classList.remove('bg-danger');
                    statusBadge.classList.add('bg-success');
                    statusBadge.textContent = 'Published';
                    button.outerHTML = `
                        <button class="btn btn-sm btn-outline-danger delete-post" title="Delete" data-post-id="${postId}">
                            <i class="bi bi-trash"></i>
                        </button>
                    `;
                    filterPosts(); // Re-apply filters
                }
            } catch (error) {
                console.error('Error restoring post:', error);
            }
        }
    });
}); 