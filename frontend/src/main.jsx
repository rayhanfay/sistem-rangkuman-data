import React from 'react';
import ReactDOM from 'react-dom/client';
import AppRouter from "./router.jsx";
import { AuthProvider } from './hooks/useAuth.jsx';
import './styles/app.css';

import { registerLicense } from '@syncfusion/ej2-base';

const syncfusionLicenseKey = import.meta.env.VITE_SYNCFUSION_LICENSE_KEY;
registerLicense(syncfusionLicenseKey);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </React.StrictMode>,
);