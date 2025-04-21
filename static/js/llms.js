document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle settings form submission
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(settingsForm);
            const settings = Object.fromEntries(formData.entries());
            
            try {
                const response = await fetch('/api/llm/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(settings)
                });
                
                if (response.ok) {
                    showAlert('Settings updated successfully', 'success');
                    // Update current settings display
                    updateCurrentSettings(settings);
                } else {
                    throw new Error('Failed to update settings');
                }
            } catch (error) {
                showAlert('Error updating settings: ' + error.message, 'danger');
            }
        });
    }

    // Handle test form submission
    const testForm = document.getElementById('test-form');
    const testPrompt = document.getElementById('test-prompt');
    const testResult = document.getElementById('test-result');
    const testButton = document.querySelector('#test-form button[type="submit"]');

    if (testForm) {
        // Handle form submission
        testForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await runTest();
        });

        // Handle Enter key in textarea
        testPrompt.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                runTest();
            }
        });

        // Update provider info when settings change
        const updateProviderInfo = () => {
            const provider = document.getElementById('current-provider').textContent;
            const model = document.getElementById('current-model').textContent;
            const providerInfo = document.getElementById('provider-info');
            if (providerInfo) {
                providerInfo.textContent = `Using ${provider} with ${model}`;
            }
        };

        // Initial update
        updateProviderInfo();
    }

    async function runTest() {
        const prompt = testPrompt.value.trim();
        if (!prompt) {
            showAlert('Please enter a test prompt', 'warning');
            return;
        }

        // Show loading state
        testButton.disabled = true;
        testButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Testing...';
        testResult.classList.add('d-none');

        try {
            const response = await fetch('/api/llm/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt })
            });
            
            if (response.ok) {
                const data = await response.json();
                testResult.classList.remove('d-none');
                testResult.querySelector('pre').textContent = data.response;
            } else {
                throw new Error('Failed to test LLM');
            }
        } catch (error) {
            testResult.classList.remove('d-none');
            testResult.querySelector('pre').textContent = `Error: ${error.message}`;
            testResult.querySelector('pre').classList.add('text-danger');
        } finally {
            // Reset button state
            testButton.disabled = false;
            testButton.textContent = 'Test LLM';
        }
    }

    // Handle prompt template editing
    const editButtons = document.querySelectorAll('.edit-prompt');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const templateId = this.dataset.templateId;
            const templateContent = document.getElementById(`template-${templateId}`).textContent;
            
            // Create modal for editing
            const modal = createEditModal(templateId, templateContent);
            document.body.appendChild(modal);
            new bootstrap.Modal(modal).show();
        });
    });

    // Helper function to show alerts
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Helper function to update current settings display
    function updateCurrentSettings(settings) {
        const currentSettings = document.getElementById('current-settings');
        if (currentSettings) {
            currentSettings.innerHTML = `
                <p><strong>Provider:</strong> ${settings.provider}</p>
                <p><strong>Model:</strong> ${settings.model}</p>
                <p><strong>API Base URL:</strong> ${settings.api_base_url}</p>
            `;
        }
    }

    // Helper function to create edit modal
    function createEditModal(templateId, content) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'editModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Edit Prompt Template</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <textarea class="form-control" rows="10">${content}</textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="save-template">Save</button>
                    </div>
                </div>
            </div>
        `;

        // Add save functionality
        modal.querySelector('#save-template').addEventListener('click', async function() {
            const newContent = modal.querySelector('textarea').value;
            
            try {
                const response = await fetch('/api/llm/prompts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        template_id: templateId,
                        content: newContent
                    })
                });
                
                if (response.ok) {
                    document.getElementById(`template-${templateId}`).textContent = newContent;
                    bootstrap.Modal.getInstance(modal).hide();
                    showAlert('Prompt template updated successfully', 'success');
                } else {
                    throw new Error('Failed to update prompt template');
                }
            } catch (error) {
                showAlert('Error updating prompt template: ' + error.message, 'danger');
            }
        });

        return modal;
    }
}); 