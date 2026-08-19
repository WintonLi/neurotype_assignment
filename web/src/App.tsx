import type { ReactElement } from 'react';
import { Route, BrowserRouter, Routes, Navigate } from 'react-router-dom';
import Assessment from './views/Assessment';
import Audit from './views/Audit';
import Login from './views/Login';
import Queue from './views/Queue';
import './App.css';
import ErrorBoundary from './components/ErrorBoundary';
import { useAssessmentStore } from './store/assessmentStore';

import AppLayout from './views/AppLayout';

const RequireAuth = ({ children }: { children: ReactElement }) => {
  const username = useAssessmentStore((state) => state.username);
  return username ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }
            >
              <Route path="queue" element={<Queue />} />
              <Route path="issued" element={<Assessment />} />
              <Route path="audit" element={<Audit />} />
              <Route path="/" element={<Navigate replace to="/queue" />} />
            </Route>
            <Route path="/" element={<Navigate replace to="/queue" />} />
          </Routes>
        </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;

