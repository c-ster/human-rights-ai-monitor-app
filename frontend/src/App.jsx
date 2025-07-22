import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link
} from 'react-router-dom';
import Dashboard from './Dashboard';
import Home from './Home';
import CurationDashboard from './CurationDashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <header className="app-header">
          <h1>Human Rights & AI Monitor</h1>
          <p>Your daily briefing on the intersection of technology and human rights.</p>
          <nav className="main-nav">
            <Link to="/">Dashboard</Link>
            <Link to="/curation">Curation</Link>
          </nav>
        </header>
        
        <Routes>
          <Route path="/curation" element={<CurationDashboard />} />
          <Route path="/" element={<Dashboard />} />
        </Routes>

        <footer className="app-footer">
          <p>&copy; 2025 Human Rights & AI Monitor. All Rights Reserved.</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
