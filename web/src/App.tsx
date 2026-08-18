import { Route, BrowserRouter, Routes, Navigate } from 'react-router-dom';
import Assessment from './views/Assessment';
import Audit from './views/Audit';
import './App.css';
import ErrorBoundary from './components/ErrorBoundary';

import AppLayout from './views/AppLayout';


function App() {
  return (
    <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route path="assessment" element={<Assessment />} />
              <Route path="audit" element={<Audit />} />
              <Route path="/" element={<Navigate replace to="/assessment" />} />
            </Route>
            <Route path="/" element={<Navigate replace to="/assessment" />} />
          </Routes>
        </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
