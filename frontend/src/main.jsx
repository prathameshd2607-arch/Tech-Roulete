import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { EmergencyProvider } from './context/EmergencyContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <EmergencyProvider>
      <App />
    </EmergencyProvider>
  </React.StrictMode>
);
