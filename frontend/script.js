document.addEventListener('DOMContentLoaded', () => {
    const contentContainer = document.getElementById('content-container');
    const runPipelineBtn = document.getElementById('run-pipeline-btn');
    const loader = document.getElementById('loader');

    const API_BASE_URL = '/api';

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
        runPipelineBtn.disabled = true;
        runPipelineBtn.textContent = 'Processing...';
        showLoader(true);
        try {
            const response = await fetch(`${API_BASE_URL}/pipeline/run`, { method: 'POST' });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            await response.json();
            // Refresh content after pipeline runs
            fetchContent();
        } catch (error) {
            console.error('Error running pipeline:', error);
            alert('Failed to run the pipeline. Please check the console for details.');
        } finally {
            runPipelineBtn.disabled = false;
            runPipelineBtn.textContent = 'Fetch New Articles';
            // The loader will be hidden by fetchContent
        }
    };

    const showLoader = (show) => {
        loader.style.display = show ? 'block' : 'none';
    };

    runPipelineBtn.addEventListener('click', runPipeline);

    // Initial load of content
    fetchContent();
});
