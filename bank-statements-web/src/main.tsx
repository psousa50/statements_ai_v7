import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { ApiClientsProvider } from './api/ApiClientsContext';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ApiClientsProvider>
      <App />
    </ApiClientsProvider>
  </React.StrictMode>
);
