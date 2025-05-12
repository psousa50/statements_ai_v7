import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { ApiProvider } from './api/ApiContext';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ApiProvider>
      <App />
    </ApiProvider>
  </React.StrictMode>
);
