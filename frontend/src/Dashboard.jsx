import { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';

const API_BASE_URL = 'http://127.0.0.1:8000';

function Dashboard() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  // Fetch categories for the filter dropdown
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/content/categories`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setCategories(data);
      } catch (e) {
        console.error("Failed to fetch categories:", e);
      }
    };
    fetchCategories();
  }, []);

  // Fetch articles based on search and category filters
  const fetchArticles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      let url;
      if (searchQuery) {
        const params = new URLSearchParams({ query: searchQuery });
        if (selectedCategory) {
          params.append('category', selectedCategory);
        }
        url = `${API_BASE_URL}/content/search?${params.toString()}`;
      } else {
        const params = new URLSearchParams();
        if (selectedCategory) {
          params.append('category', selectedCategory);
        }
        url = `${API_BASE_URL}/content/approved?${params.toString()}`;
      }

      const response = await fetch(url);
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
  }, [searchQuery, selectedCategory]);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  return (
    <main className="content-area">
      <div className="dashboard-header">
        <h2>Human Rights AI Monitor</h2>
        <p>A real-time feed of curated articles and reports.</p>
        <div className="filters">
          <input
            type="text"
            placeholder="Search articles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="category-select"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="loader">Loading curated content...</div>}
      {error && <div className="error-message">Error: {error}</div>}
      {!loading && !error && (
        <div className="articles-grid">
          {articles.length > 0 ? (
            articles.map(article => (
              <article key={article._id} className="article-card">
                <div className="card-header">
                  <span className="category-tag">{article.category || 'N/A'}</span>
                  <span className="source-tag">{article.source}</span>
                </div>
                <h2>
                  <a href={article.url} target="_blank" rel="noopener noreferrer">
                    {article.title}
                  </a>
                </h2>
                {article.summary && article.summary.length > 0 && <p className="summary">{article.summary[0]}</p>}
              </article>
            ))
          ) : (
            <p className="no-articles">No articles found for the current filters.</p>
          )}
        </div>
      )}
    </main>
  );
}

export default Dashboard;
