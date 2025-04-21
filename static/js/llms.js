document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up event listeners...');
    
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle model selection
    const modelSelect = document.querySelector('select[name="model_name"]');
    const customModelInput = document.querySelector('input[name="custom_model_name"]');
    
    if (modelSelect && customModelInput) {
        modelSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customModelInput.classList.remove('d-none');
                customModelInput.required = true;
            } else {
                customModelInput.classList.add('d-none');
                customModelInput.required = false;
            }
        });
    }

    // Handle settings form submission
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(settingsForm);
            const settings = Object.fromEntries(formData.entries());
            
            // Handle custom model name
            if (settings.model_name === 'custom') {
                settings.model_name = settings.custom_model_name;
                delete settings.custom_model_name;
            }
            
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

    if (testForm && testPrompt && testResult && testButton) {
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
            const provider = document.getElementById('current-provider');
            const model = document.getElementById('current-model');
            const providerInfo = document.getElementById('provider-info');
            if (provider && model && providerInfo) {
                providerInfo.textContent = `Using ${provider.textContent} with ${model.textContent}`;
            }
        };

        // Initial update
        updateProviderInfo();
    }

    async function runTest() {
        if (!testPrompt || !testResult || !testButton) return;
        
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
            showAlert('Error testing LLM: ' + error.message, 'danger');
        } finally {
            // Reset button state
            testButton.disabled = false;
            testButton.innerHTML = 'Test';
        }
    }

    // Handle prompt template editing
    const editButtons = document.querySelectorAll('.edit-prompt');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const templateId = this.dataset.templateId;
            const templateContent = document.getElementById(`template-${templateId}`);
            if (!templateContent) return;
            
            // Create modal for editing
            const modal = createEditModal(templateId, templateContent.textContent);
            document.body.appendChild(modal);
            new bootstrap.Modal(modal).show();
        });
    });

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }, 5000);
        }
    }

    function updateCurrentSettings(settings) {
        const provider = document.getElementById('current-provider');
        const model = document.getElementById('current-model');
        const apiBase = document.getElementById('current-api-base');
        const providerInfo = document.getElementById('provider-info');
        
        if (provider) provider.textContent = settings.provider_type;
        if (model) model.textContent = settings.model_name;
        if (apiBase) apiBase.textContent = settings.api_base;
        if (providerInfo) {
            providerInfo.textContent = `Using ${settings.provider_type} with ${settings.model_name}`;
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
                    const templateElement = document.getElementById(`template-${templateId}`);
                    if (templateElement) {
                        templateElement.textContent = newContent;
                    }
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

    // Load actions
    async function loadActions() {
        try {
            console.log('Loading actions...');
            const response = await fetch('/api/llm/actions');
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received data:', data);
            
            if (data.success) {
                displayActions(data.actions);
            } else {
                throw new Error(data.error || 'Failed to load actions');
            }
        } catch (error) {
            console.error('Error loading actions:', error);
            const loadingIndicator = document.getElementById('actions-loading');
            if (loadingIndicator) {
                loadingIndicator.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        Failed to load actions: ${error.message}
                    </div>
                `;
            }
        }
    }

    // Load prompts
    async function loadPrompts() {
        try {
            console.log('Loading prompts...');
            const response = await fetch('/api/llm/prompts');
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received data:', data);
            
            if (data.success) {
                displayPrompts(data.prompts);
            } else {
                throw new Error(data.error || 'Failed to load prompts');
            }
        } catch (error) {
            console.error('Error loading prompts:', error);
            const loadingIndicator = document.getElementById('prompts-loading');
            if (loadingIndicator) {
                loadingIndicator.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        Failed to load prompts: ${error.message}
                    </div>
                `;
            }
        }
    }

    // Display actions in the accordion
    function displayActions(actions) {
        const accordion = document.getElementById('actionsAccordion');
        if (!accordion) return;
        
        accordion.innerHTML = '';

        actions.forEach((action, index) => {
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            accordionItem.innerHTML = `
                <h2 class="accordion-header" id="actionHeading${index}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#actionCollapse${index}" aria-expanded="false" 
                            aria-controls="actionCollapse${index}">
                        <i class="bi bi-lightning me-2"></i>
                        ${action.name}
                    </button>
                </h2>
                <div id="actionCollapse${index}" class="accordion-collapse collapse" 
                     aria-labelledby="actionHeading${index}" data-bs-parent="#actionsAccordion">
                    <div class="accordion-body">
                        <p class="text-muted">${action.description}</p>
                        <h6 class="mt-3">Model Settings</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <tbody>
                                    <tr>
                                        <th>Model</th>
                                        <td>
                                            <select class="form-select form-select-sm model-select" 
                                                    data-action-id="${action.id}">
                                                <option value="default" ${action.model_name === 'default' ? 'selected' : ''}>Default</option>
                                                <option value="llama3.1:70b" ${action.model_name === 'llama3.1:70b' ? 'selected' : ''}>Llama 3.1 70B</option>
                                                <option value="mistral" ${action.model_name === 'mistral' ? 'selected' : ''}>Mistral</option>
                                                <option value="custom">Custom...</option>
                                            </select>
                                            <input type="text" class="form-control form-control-sm mt-2 d-none custom-model-input" 
                                                   placeholder="Enter custom model name">
                                        </td>
                                    </tr>
                                    <tr>
                                        <th>Temperature</th>
                                        <td>${action.temperature}</td>
                                    </tr>
                                    <tr>
                                        <th>Max Tokens</th>
                                        <td>${action.max_tokens}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <h6 class="mt-3">Prompt Reference</h6>
                        <div class="card bg-light">
                            <div class="card-body">
                                <code>${action.id}</code>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            accordion.appendChild(accordionItem);
        });

        // Add event listeners for model selection
        document.querySelectorAll('.model-select').forEach(select => {
            select.addEventListener('change', async function() {
                const actionId = this.dataset.actionId;
                const modelName = this.value === 'custom' 
                    ? this.nextElementSibling.value 
                    : this.value;
                
                try {
                    const response = await fetch('http://localhost:5001/api/llm/actions/update', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            action_id: actionId,
                            model_name: modelName
                        })
                    });
                    
                    if (response.ok) {
                        showAlert('Model updated successfully', 'success');
                    } else {
                        throw new Error('Failed to update model');
                    }
                } catch (error) {
                    showAlert('Error updating model: ' + error.message, 'danger');
                }
            });
        });

        // Add event listeners for custom model input
        document.querySelectorAll('.custom-model-input').forEach(input => {
            input.addEventListener('change', function() {
                const select = this.previousElementSibling;
                if (select.value === 'custom') {
                    select.dispatchEvent(new Event('change'));
                }
            });
        });

        // Hide loading spinner
        const loadingIndicator = document.getElementById('actions-loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    // Display prompts in the accordion
    function displayPrompts(prompts) {
        const accordion = document.getElementById('promptsAccordion');
        if (!accordion) return;
        
        accordion.innerHTML = '';

        prompts.forEach((prompt, index) => {
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            accordionItem.innerHTML = `
                <h2 class="accordion-header" id="promptHeading${index}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#promptCollapse${index}" aria-expanded="false" 
                            aria-controls="promptCollapse${index}">
                        <i class="bi bi-chat-quote me-2"></i>
                        ${prompt.name}
                    </button>
                </h2>
                <div id="promptCollapse${index}" class="accordion-collapse collapse" 
                     aria-labelledby="promptHeading${index}" data-bs-parent="#promptsAccordion">
                    <div class="accordion-body">
                        <p class="text-muted">${prompt.description}</p>
                        <h6 class="mt-3">Template</h6>
                        <div class="card bg-light">
                            <div class="card-body">
                                <pre class="mb-0">${prompt.template}</pre>
                            </div>
                        </div>
                        <h6 class="mt-3">Variables</h6>
                        <ul class="list-unstyled">
                            ${prompt.variables.map(v => `
                                <li class="mb-2">
                                    <strong>${v.name}</strong>
                                    ${v.required ? '<span class="badge bg-danger ms-2">required</span>' : ''}
                                    <p class="text-muted small mb-0">${v.description}</p>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
            accordion.appendChild(accordionItem);
        });

        // Hide loading spinner
        const loadingIndicator = document.getElementById('prompts-loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    // Add event listeners for tabs
    const actionsTab = document.getElementById('actions-tab');
    if (actionsTab) {
        console.log('Found actions tab, adding event listener...');
        actionsTab.addEventListener('shown.bs.tab', function() {
            console.log('Actions tab shown, loading actions...');
            loadActions();
        });
    } else {
        console.error('Actions tab element not found!');
    }

    const promptsTab = document.getElementById('prompts-tab');
    if (promptsTab) {
        console.log('Found prompts tab, adding event listener...');
        promptsTab.addEventListener('shown.bs.tab', function() {
            console.log('Prompts tab shown, loading prompts...');
            loadPrompts();
        });
    } else {
        console.error('Prompts tab element not found!');
    }
}); 