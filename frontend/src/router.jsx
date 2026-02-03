import React from 'react';
import { createBrowserRouter, RouterProvider, Outlet, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth.jsx'; 
import { McpProvider } from './contexts/McpProvider.jsx';
import Layout from './components/common/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Stats from './pages/Stats';
import History from './pages/History';
import NotFound from './pages/NotFound';
import Cycle from './pages/Cycle';
import AccountManagement from './pages/AccountManagement';
import CustomAnalysis from './pages/CustomAnalysis';
import MasterData from './pages/MasterData';
import LoadingOverlay from './components/common/LoadingOverlay';

// Komponen untuk melindungi rute yang memerlukan login
const ProtectedLayout = () => {
    const { isAuthenticated, loading } = useAuth();
    if (loading) { return <LoadingOverlay />; }
    if (!isAuthenticated) { return <Navigate to="/login" replace />; }
    return (
        <Layout>
            <Outlet />
        </Layout>
    );
};

// Komponen untuk rute publik (halaman login)
const PublicRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();
    if (loading) { return <LoadingOverlay />; }
    if (isAuthenticated) { return <Navigate to="/" replace />; }
    return children;
};

const RoleBasedRoute = ({ allowedRoles, children }) => {
    const { user, loading } = useAuth();
    if (loading) return <LoadingOverlay />;
    if (!user || !allowedRoles.includes(user.role)) {
        return <Navigate to="/" replace />; 
    }
    return children;
};

const router = createBrowserRouter([
    {
        path: '/',
        element: <ProtectedLayout />,
        children: [
            { path: '/', element: <Home /> },
            { path: '/custom-analysis', element: <CustomAnalysis /> },
            { path: '/stats', element: <Stats /> },
            { path: '/cycle', element: <Cycle /> },
            { path: '/master-data', element: <MasterData /> },
            
            { 
                path: '/history', 
                element: (
                    <RoleBasedRoute allowedRoles={['admin']}>
                        <History />
                    </RoleBasedRoute>
                ) 
            },
            { 
                path: '/account-management', 
                element: (
                    <RoleBasedRoute allowedRoles={['admin']}>
                        <AccountManagement />
                    </RoleBasedRoute>
                ) 
            },
        ],
    },
    {
        path: '/login',
        element: (<PublicRoute><Login /></PublicRoute>),
    },
    {
        path: '*',
        element: <NotFound />,
    },
]);

const AppRouter = () => {
    return (
        <AuthProvider>
            <McpProvider>
                <RouterProvider router={router} />
            </McpProvider>
        </AuthProvider>
    );
};

export default AppRouter;