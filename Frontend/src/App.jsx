import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import PolicyPage from './pages/PolicyPage';
import ClaimsPage from './pages/ClaimsPage';
import AdminDashboard from './pages/AdminDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/register" element={<Register />} />
        {/* Dashboard Route */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/policy" element={<PolicyPage />} />
        <Route path="/claims" element={<ClaimsPage />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
