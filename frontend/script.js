document.addEventListener('DOMContentLoaded', function() {
    const runPipelineBtn = document.getElementById('run-pipeline-btn');
    const runCompletePipelineBtn = document.getElementById('run-complete-pipeline-btn');
    const viewPublicBtn = document.getElementById('view-public-btn');
    const viewCurationBtn = document.getElementById('view-curation-btn');
    const contentContainer = document.getElementById('content-container');
    const curationContainer = document.getElementById('curation-container');
    const loader = document.getElementById('loader');
    const modal = document.getElementById('curation-modal');
    const closeModal = document.getElementsByClassName('close')[0];

    const API_BASE_URL = '/api';

    let currentContentId = null;

    const fetchContent = async () => {
        showLoader(true);
        contentContainer.innerHTML = '';
        try {
            const response = await fetch(`${API_BASE_URL}/content`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const articles = await response.json();
            displayContent(articles);
        } catch (error) {
            console.error('Error fetching content:', error);
            contentContainer.innerHTML = '<p>Error loading content. Please try again later.</p>';
        } finally {
            showLoader(false);
        }
    };

    const displayContent = (articles) => {
        if (articles.length === 0) {
            contentContainer.innerHTML = '<p>No articles found. Try fetching new articles.</p>';
            return;
        }

        articles.forEach(article => {
            const articleElement = document.createElement('div');
            articleElement.className = 'article';

            const publishedDate = new Date(article.published_at).toLocaleDateString();

            articleElement.innerHTML = `
                <div class="article-title">
                    <a href="${article.url}" target="_blank">${article.title}</a>
                    <span class="category-tag ${article.category.toLowerCase().replace(/ /g, '-')}">${article.category}</span>
                </div>
                <div class="article-meta">
                    <span>${article.source} | ${publishedDate}</span>
                </div>
                <p class="article-summary">${article.summary[0]}</p>
            `;
            contentContainer.appendChild(articleElement);
        });
    };

    const runPipeline = async () => {
        showLoader(true);
        try {
            const response = await fetch(`${API_BASE_URL}/pipeline/run`, {
                method: 'POST'
            });
            const result = await response.json();
            console.log('Pipeline result:', result);
            // Reload content after pipeline runs
            await loadContent();
        } catch (error) {
            console.error('Error running pipeline:', error);
        } finally {
            showLoader(false);
        }
    };

    const runCompletePipeline = async () => {
        showLoader(true);
        try {
            const response = await fetch(`${API_BASE_URL}/pipeline/run-complete`, {
                method: 'POST'
            });
            const result = await response.json();
            console.log('Complete pipeline result:', result);
            // Reload content after pipeline runs
            await loadContent();
        } catch (error) {
            console.error('Error running complete pipeline:', error);
        } finally {
            showLoader(false);
        }
    };

    const showPublicFeed = () => {
        contentContainer.style.display = 'block';
        curationContainer.style.display = 'none';
        updateActiveButton('view-public-btn');
        loadContent();
    };

    const showCurationDashboard = () => {
        contentContainer.style.display = 'none';
        curationContainer.style.display = 'block';
        updateActiveButton('view-curation-btn');
        loadPendingContent();
    };

    const updateActiveButton = (activeId) => {
        document.querySelectorAll('.nav-buttons .button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(activeId).classList.add('active');
    };

    const loadPendingContent = async () => {
        showLoader(true);
        try {
            const response = await fetch(`${API_BASE_URL}/content/pending`);
            const contents = await response.json();
            displayPendingContent(contents);
        } catch (error) {
            console.error('Error loading pending content:', error);
        } finally {
            showLoader(false);
        }
    };

    const displayPendingContent = (contents) => {
        const pendingContainer = document.getElementById('pending-content');
        pendingContainer.innerHTML = '';

        if (contents.length === 0) {
            pendingContainer.innerHTML = '<p>No pending content for curation.</p>';
            return;
        }

        contents.forEach(content => {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'pending-item';
            contentDiv.innerHTML = `
                <h3>${content.title}</h3>
                <div class="source">${content.source} - ${content.content_type}</div>
                <div class="summary">${content.summary.join(' ')}</div>
                <div class="category">Category: ${content.category}</div>
                <button class="curate-btn" onclick="openCurationModal('${content._id || content.id}')">Curate</button>
            `;
            pendingContainer.appendChild(contentDiv);
        });
    };

    const openCurationModal = async (contentId) => {
        currentContentId = contentId;
        try {
            const response = await fetch(`${API_BASE_URL}/content`);
            const contents = await response.json();
            const content = contents.find(c => (c._id || c.id) === contentId);
            
            if (content) {
                document.getElementById('modal-content-details').innerHTML = `
                    <h4>${content.title}</h4>
                    <p><strong>Source:</strong> ${content.source}</p>
                    <p><strong>Category:</strong> ${content.category}</p>
                    <p><strong>Summary:</strong> ${content.summary.join(' ')}</p>
                    <p><strong>URL:</strong> <a href="${content.url}" target="_blank">${content.url}</a></p>
                `;
                
                // Pre-fill edit form
                document.getElementById('edited-title').value = content.title;
                document.getElementById('edited-summary').value = content.summary.join(' ');
                
                modal.style.display = 'block';
            }
        } catch (error) {
            console.error('Error loading content details:', error);
        }
    };

    const curateContent = async (action) => {
        if (!currentContentId) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/content/curate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content_id: currentContentId,
                    action: action,
                    editor_notes: document.getElementById('editor-notes').value
                })
            });
            
            const result = await response.json();
            console.log('Curation result:', result);
            
            modal.style.display = 'none';
            loadPendingContent(); // Refresh the pending list
            
        } catch (error) {
            console.error('Error curating content:', error);
        }
    };

    const showEditForm = () => {
        document.getElementById('edit-form').style.display = 'block';
    };

    const saveEdit = async () => {
        if (!currentContentId) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/content/curate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content_id: currentContentId,
                    action: 'edit',
                    edited_title: document.getElementById('edited-title').value,
                    edited_summary: document.getElementById('edited-summary').value,
                    editor_notes: document.getElementById('editor-notes').value
                })
            });
            
            const result = await response.json();
            console.log('Edit result:', result);
            
            modal.style.display = 'none';
            document.getElementById('edit-form').style.display = 'none';
            loadPendingContent(); // Refresh the pending list
            
        } catch (error) {
            console.error('Error saving edit:', error);
        }
    };

    const closeModalHandler = () => {
        modal.style.display = 'none';
        document.getElementById('edit-form').style.display = 'none';
        currentContentId = null;
    };

    const showLoader = (show) => {
        loader.style.display = show ? 'block' : 'none';
    };

    runPipelineBtn.addEventListener('click', runPipeline);

    // Initial load of content
    fetchContent();
});
