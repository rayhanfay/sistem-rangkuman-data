import React, { createContext, useContext, useState, useEffect } from 'react';
import { onIdTokenChanged } from "firebase/auth";
import { auth } from '../utils/firebase';
import { jwtDecode } from 'jwt-decode';

import LoadingOverlay from '../components/common/LoadingOverlay';
import authService from '../services/authService'; 
import { useToast, ToastProvider } from '../contexts/ToastContext';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const AuthProviderComponent = ({ children }) => {
    const { showToast } = useToast();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onIdTokenChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                try {
                    const token = await firebaseUser.getIdToken(true);
                    const decodedToken = jwtDecode(token);
                    
                    const role = decodedToken.role || 'user';
                    
                    
                    authService.setToken(token);
                    setUser({
                        uid: firebaseUser.uid,
                        email: firebaseUser.email,
                        role: role,
                    });
                } catch (error) {
                    console.error("Error memproses token:", error);
                    authService.logout(); 
                }
            } else {
                authService.setToken(null);
                setUser(null);
            }
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);
    
    const login = async (email, password) => {
        try {
            await authService.login(email, password);
            showToast('Login berhasil!', 'success');
        } catch (error) {
            throw error;
        }
    };

    const logout = () => {
        authService.logout();
    };

    const value = {
        user,
        isAuthenticated: !!user,
        loading,
        login,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {loading ? <LoadingOverlay /> : children}
        </AuthContext.Provider>
    );
};

export const AuthProvider = ({ children }) => (
    <ToastProvider>
        <AuthProviderComponent>{children}</AuthProviderComponent>
    </ToastProvider>
);