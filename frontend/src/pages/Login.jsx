import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { LogIn, AlertCircle } from 'lucide-react';

const getFriendlyErrorMessage = (errorCode, errorMessage) => {
    if (errorMessage && !errorCode) {
        return errorMessage;
    }
    
    switch (errorCode) {
        case 'auth/invalid-email':
            return 'Format email yang Anda masukkan tidak valid.';
        case 'auth/user-not-found':
        case 'auth/wrong-password':
        case 'auth/invalid-credential':
            return 'Email atau password yang Anda masukkan salah.';
        case 'auth/too-many-requests':
            return 'Akses ke akun ini telah diblokir sementara. Silakan coba lagi nanti.';
        case 'auth/network-request-failed':
            return 'Gagal terhubung ke server. Periksa koneksi internet Anda.';
        default:
            return 'Login gagal. Terjadi kesalahan yang tidak diketahui.';
    }
};

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        
        try {
            await login(email, password);
            navigate('/');
        } catch (err) {
            console.error('Login error:', err);
            const friendlyMessage = getFriendlyErrorMessage(err.code, err.message);
            setError(friendlyMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex bg-background">
            <div className="hidden lg:flex flex-col justify-center items-center w-1/2 bg-brand-blue text-white p-12 text-center">
                <img src="/images/logo.png" alt="Logo PHR" className="w-24 mb-6 bg-white rounded-full p-2" />
                <h1 className="text-3xl font-bold">Data Summarization System</h1>
                <p className="mt-4 text-gray-300">
                    Mengintegrasikan LLM dan Spreadsheet Data menggunakan Model Context Protokol (MCP) untuk Pertamina Hulu Rokan.
                </p>
            </div>
            <div className="flex flex-col justify-center items-center w-full lg:w-1/2 p-8">
                <div className="max-w-md w-full">
                    <h2 className="text-3xl font-bold text-text-primary mb-2">Selamat Datang</h2>
                    <p className="text-text-secondary mb-8">Silakan masuk untuk mengakses dasbor Anda.</p>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="bg-brand-red/10 border border-brand-red/30 text-brand-red p-3 rounded-md flex items-center text-sm">
                                <AlertCircle className="h-5 w-5 mr-3 flex-shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}
                        
                        <Input
                            name="email"
                            label="Email"
                            type="email"
                            placeholder="Masukkan email Anda"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={loading}
                            required
                        />
                        <Input
                            name="password"
                            type="password"
                            label="Password"
                            placeholder="Masukkan password Anda"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={loading}
                            required
                        />
                        
                        <Button
                            type="submit"
                            loading={loading}
                            disabled={loading}
                            className="w-full"
                            size="lg"
                        >
                            <LogIn className="mr-2" size={20} />
                            {loading ? 'Memproses...' : 'Masuk'}
                        </Button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Login;