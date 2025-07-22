import { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000';

function Home() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState({});

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        if (searchTerm) params.append('q', searchTerm);
        if (category) params.append('category', category);

        const response = await fetch(`${API_BASE_URL}/content/approved?${params.toString()}`);
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
    };

    const debounceTimer = setTimeout(() => {
      fetchContent();
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, category]);

  const handleFeedback = async (articleId, feedbackType) => {
    if (feedbackSubmitted[articleId]) return;

    try {
      const response = await fetch(`${API_BASE_URL}/content/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId, feedback_type: feedbackType }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setFeedbackSubmitted(prev => ({ ...prev, [articleId]: true }));
    } catch (e) {
      console.error("Failed to submit feedback:", e);
    }
  };

  return (
    <>
      <div className="filter-controls">
        <input
          type="text"
          placeholder="Search articles by keyword..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          className="category-select"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          <option value="AI Governance & Ethics">AI Governance & Ethics</option>
          <option value="Surveillance & Privacy">Surveillance & Privacy</option>
          <option value="Algorithmic Bias">Algorithmic Bias</option>
          <option value="Autonomous Weapons">Autonomous Weapons</option>
          <option value="Labor & Automation">Labor & Automation</option>
        </select>
      </div>
      <main className="content-area">
        {loading && <div className="loader">Loading articles...</div>}
        {error && <div className="error-message">Error fetching articles: {error}</div>}
        {!loading && !error && (
          <div className="articles-grid">
            {articles.length > 0 ? (
              articles.map(article => (
                <article key={article._id || article.id} className="article-card">
                  <div className="card-header">
                    <span className="category-tag">{article.category}</span>
                    <span className="source-tag">{article.source}</span>
                  </div>
                  <h2>
                    <a href={article.url} target="_blank" rel="noopener noreferrer">
                      {article.title}
                    </a>
                  </h2>
                  <p className="summary">{article.summary[0]}</p>
                  <div className="card-footer">
                    <span>{new Date(article.published_at).toLocaleDateString()}</span>
                    <div className="feedback-controls">
                      {feedbackSubmitted[article._id] ? (
                        <span className="feedback-thanks">Thank you!</span>
                      ) : (
                        <>
                          <button onClick={() => handleFeedback(article._id, 'helpful')} className="feedback-btn helpful">
                            Helpful
                          </button>
                          <button onClick={() => handleFeedback(article._id, 'not_helpful')} className="feedback-btn not-helpful">
                            Not Helpful
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <p className="no-articles">No articles found. The pipeline may need to be run.</p>
            )}
          </div>
        )}
      </main>
    </>
  );
}

export default Home;
