import { useState, useEffect, useCallback } from 'react';
import './CurationDashboard.css';

const API_BASE_URL = 'http://localhost:8000';

function CurationDashboard() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPendingArticles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/content/pending`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setArticles(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPendingArticles();
  }, [fetchPendingArticles]);

  const handleCuration = async (articleId, action) => {
    try {
      const response = await fetch(`${API_BASE_URL}/content/curate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId, action: action }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      // Refresh the list after curation
      fetchPendingArticles();

    } catch (e) {
      console.error(`Failed to ${action} article:`, e);
      setError(e.message || `Failed to ${action} article. Please try again.`);
    }
  };

  return (
    <main className="content-area">
      <div className="curation-header">
        <h2>Content Curation</h2>
        <p>Review and approve or reject articles from the ingestion pipeline.</p>
      </div>

      {loading && <div className="loader">Loading pending articles...</div>}
      {error && <div className="error-message">Error: {error}</div>}
      {!loading && !error && (
        <div className="articles-grid">
          {articles.length > 0 ? (
            articles.map(article => (
              <article key={article._id} className="article-card curation-card">
                <div className="card-header">
                  <span className="category-tag">{article.category || 'N/A'}</span>
                  <span className="source-tag">{article.source}</span>
                </div>
                <h2>
                  <a href={article.url} target="_blank" rel="noopener noreferrer">
                    {article.title}
                  </a>
                </h2>
                <p className="summary">{article.summary ? article.summary[0] : 'No summary available.'}</p>
                <div className="card-footer curation-controls">
                  <button onClick={() => handleCuration(article._id, 'approve')} className="curate-btn approve">
                    Approve
                  </button>
                  <button onClick={() => handleCuration(article._id, 'reject')} className="curate-btn reject">
                    Reject
                  </button>
                </div>
              </article>
            ))
          ) : (
            <p className="no-articles">No pending articles to review.</p>
          )}
        </div>
      )}
    </main>
  );
}

export default CurationDashboard;
