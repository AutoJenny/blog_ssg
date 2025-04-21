document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('postForm');
    const workingTitleInput = document.getElementById('working_title');
    const authorSelect = document.getElementById('author');
    const conceptTextarea = document.getElementById('concept');
    const saveBtn = document.getElementById('saveBtn');

    console.log('Form loaded:', form);
    console.log('Inputs:', {workingTitleInput, authorSelect, conceptTextarea, saveBtn});

    // Function to check if all required fields are filled
    function validateForm() {
        const titleValid = workingTitleInput.value.trim() !== '';
        const authorValid = authorSelect.value !== '';
        const conceptValid = conceptTextarea.value.trim() !== '';
        
        console.log('Form validation:', {titleValid, authorValid, conceptValid});
        
        saveBtn.disabled = !(titleValid && authorValid && conceptValid);
    }

    // Add event listeners to all form fields
    [workingTitleInput, authorSelect, conceptTextarea].forEach(element => {
        element.addEventListener('input', validateForm);
        element.addEventListener('change', validateForm);
    });

    // Form submission handler
    form.addEventListener('submit', function(e) {
        console.log('Form submitted');
        console.log('Form data:', {
            working_title: workingTitleInput.value,
            author: authorSelect.value,
            concept: conceptTextarea.value
        });
        
        // Let the form submit normally
        return true;
    });
}); 